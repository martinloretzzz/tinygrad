import functools, math
from typing import ClassVar
from llvmlite import ir  # type: ignore
from tinygrad.codegen.ast import ASTKernel
from tinygrad.ops import UnaryOps, BinaryOps, ReduceOps, LazyOp, ASTRunner
from tinygrad.helpers import DEBUG, prod, dtypes
from tinygrad.shape.symbolic import Variable, NumNode, MulNode, DivNode, ModNode, GeNode, LtNode, SumNode, AndNode

def int_const(x): return ir.Constant(ir.IntType(64), x)

render_llvm = {
  Variable: lambda self,ops,ctx: self.expr,
  NumNode: lambda self,ops,ctx: int_const(self.b),
  MulNode: lambda self,ops,ctx: ctx.mul(self.a.render(ops,ctx), int_const(self.b)),
  DivNode: lambda self,ops,ctx: ctx.sdiv(self.a.render(ops,ctx), int_const(self.b)),
  ModNode: lambda self,ops,ctx: ctx.srem(self.a.render(ops,ctx), int_const(self.b)),
  GeNode: lambda self,ops,ctx: ctx.icmp_signed(">=", self.a.render(ops,ctx), int_const(self.b)),
  LtNode: lambda self,ops,ctx: ctx.icmp_signed("<", self.a.render(ops,ctx), int_const(self.b)),
  SumNode: lambda self,ops,ctx: functools.reduce(lambda a,b: ctx.add(a,b.render(ops,ctx)), self.nodes[1:], self.nodes[0].render(ops,ctx)),
  AndNode: lambda self,ops,ctx: functools.reduce(lambda a,b: ctx.and_(a,b.render(ops,ctx)), self.nodes[1:], self.nodes[0].render(ops,ctx))
}

class LLVMCodegen(ASTKernel):
  op_lookup: ClassVar = {
    UnaryOps.NOOP: lambda builder,x: x,
    UnaryOps.NEG: lambda builder,x: builder.fneg(x, flags=('fast',)),
    UnaryOps.EXP: lambda builder,x: builder.call(builder._block.module.declare_intrinsic('llvm.exp', [ir.FloatType()]), [x], fastmath=('fast',)),
    UnaryOps.LOG: lambda builder,x: builder.call(builder._block.module.declare_intrinsic('llvm.log', [ir.FloatType()]), [x], fastmath=('fast',)),
    UnaryOps.NOT: lambda builder,x: builder.fsub(ir.Constant(ir.FloatType(), 1), x, flags=('fast',)),
    BinaryOps.ADD: lambda builder,x,y: builder.fadd(x,y, flags=('fast',)),
    BinaryOps.SUB: lambda builder,x,y: builder.fsub(x,y, flags=('fast',)),
    BinaryOps.MUL: lambda builder,x,y: builder.fmul(x,y, flags=('fast',)),
    BinaryOps.DIV: lambda builder,x,y: builder.fdiv(x,y, flags=('fast',)),
    BinaryOps.POW: lambda builder,x,y: builder.call(builder._block.module.declare_intrinsic('llvm.pow', [ir.FloatType()]), [x,y], fastmath=('fast',)),
    BinaryOps.CMPEQ: lambda builder,x,y: builder.uitofp(builder.fcmp_ordered("==", x, y, flags=('fast',)), ir.FloatType()),
    BinaryOps.MAX: lambda builder,x,y: builder.select(builder.fcmp_unordered(">", x, y, flags=('fast',)), x, y, flags=('fast',)),
    ReduceOps.SUM: lambda builder,x,y: builder.fadd(x, y, flags=('fast',)),
    ReduceOps.MAX: lambda builder,x,y: builder.select(builder.fcmp_unordered(">", y, x, flags=('fast',)), y, x, flags=('fast',))
  }
  start_for_op: ClassVar = {
    ReduceOps.SUM: ir.Constant(ir.FloatType(), 0),
    ReduceOps.MAX: ir.Constant(ir.FloatType(), -math.inf)
  }

  def codegen(self):
    self.process()
    if DEBUG >= 3: self.printbufs("old:", DEBUG>=4)

    # create llvm function
    module = ir.Module(name=__file__)
    func_dtypes = [{dtypes.float16:ir.HalfType(), dtypes.float32:ir.FloatType()}[buf.dtype] for buf in self.bufs]
    func = ir.Function(module, ir.FunctionType(ir.VoidType(), [x.as_pointer() for x in func_dtypes]), name='exec')

    # force llvmlite to allow us to add function attribute then add the attribute
    func.attributes._known = func.attributes._known.union(frozenset(['"no-nans-fp-math"="true"']))
    func.attributes.add('"no-nans-fp-math"="true"')

    # construct the structure of the loops
    loop_entry = [ir.IRBuilder(func.append_basic_block(name)) for name in (["entry"] + [f"loop_{i}" for i in range(len(self.full_shape))])]
    loop_exit = [ir.IRBuilder(func.append_basic_block(name)) for name in ([f"loopexit_{len(self.full_shape)-i-1}" for i in range(len(self.full_shape))] + ["exit"])][::-1]

    store_loop = self.sts[0].shape.index(1) if 1 in self.sts[0].shape else -1

    if self.reduceop:
      phis = [LLVMCodegen.start_for_op[self.reduceop.op]]  # type: ignore
      for i in range(store_loop+1, len(loop_entry)):
        val = loop_entry[i].phi(ir.FloatType(), f"reduce_phi_{i}")
        val.add_incoming(phis[-1], loop_entry[i-1]._block)
        phis.append(val)

    # add the looping
    loop_vars = []
    loop_ex = []    # TODO remove this
    for i,s in enumerate(self.full_shape):
      loop_entry[i].branch(loop_entry[i+1]._block)
      idx = loop_entry[i+1].phi(ir.IntType(64), name=f"loopvar_{i}")
      loop_vars.append(idx)
      idx.add_incoming(int_const(0), loop_entry[i]._block)
      idx_p1 = loop_exit[i+1].add(idx, int_const(1))
      idx.add_incoming(idx_p1, loop_exit[i+1]._block)
      loop_ex.append(idx_p1)

    # the ast parser
    def ast_parse(builder, x, reduce_result=None):
      if not isinstance(x, LazyOp):
        buf_index = self.bufs.index(x)
        idx, valid = self.sts[buf_index].expr_idxs(0, [loop_vars[i] for i in range(len(self.sts[buf_index].shape))])
        if valid.min == 0:
          valid = valid.render(render_llvm, builder)
          # this always does the load, so we have it load *0 if the arg won't be used
          # TODO: would control flow be faster?
          aug_idx = builder.select(valid, idx.render(render_llvm, builder), int_const(0))
          element = builder.select(valid, builder.load(builder.gep(func.args[buf_index], [aug_idx], inbounds=True)), ir.Constant(func_dtypes[buf_index], 0))
        else:
          element = builder.load(builder.gep(func.args[buf_index], [idx.render(render_llvm, builder)], inbounds=True))
        # upcast
        if func_dtypes[buf_index] != ir.FloatType(): element = builder.fpext(element, ir.FloatType())
        return element
      if isinstance(x.op, ReduceOps):
        if reduce_result is None: raise RuntimeError("no reduce")
        return reduce_result
      return LLVMCodegen.op_lookup[x.op](builder, *[ast_parse(builder, v, reduce_result) for v in x.src])

    # do the early ast
    reduce_result = None
    if self.reduceop:
      reduce_input = ast_parse(loop_exit[-1], self.reduceop.src[0])
      # TODO why is val right?
      reduce_result = LLVMCodegen.op_lookup[self.reduceop.op](loop_exit[-1], reduce_input, val)

      for i,phi in enumerate(phis[1:]):
        phi.add_incoming(reduce_result, loop_exit[store_loop+1+i]._block)

    # do the late ast
    builder = loop_exit[store_loop]
    result = ast_parse(builder, self.ast, reduce_result)
    if func_dtypes[0] != ir.FloatType(): result = builder.fptrunc(result, func_dtypes[0])

    # store result
    idx, _ = self.sts[0].expr_idxs(0, [loop_vars[i] for i in range(len(self.sts[0].shape))])
    builder.store(result, builder.gep(func.args[0], [idx.render(render_llvm, builder)], inbounds=True))

    for i,s in enumerate(self.full_shape):
      loop_exit[i+1].cbranch(loop_exit[i+1].icmp_unsigned("==", loop_ex[i], int_const(s)), loop_exit[i]._block, loop_entry[i+1]._block)

    loop_entry[-1].branch(loop_exit[-1]._block)
    loop_exit[0].ret_void()

    # TODO: mem_estimate is copied from GPU
    mem_estimate = sum(x.dtype.itemsize*(x.realized.size if x.realized is not None else prod(x.shape)) for x in self.bufs if x is not None)
    return ASTRunner('exec', str(module), op_estimate=self.info.flops, mem_estimate=mem_estimate)