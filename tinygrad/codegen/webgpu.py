import math
from typing import List
from tinygrad.codegen.linearizer import Linearizer, UOps, UOp, Token
from tinygrad.ops import Op, ASTRunner, UnaryOps, BinaryOps, FusedOps
from tinygrad.lazy import LazyBuffer

from tinygrad.shape.symbolic import Variable, NumNode, MulNode, DivNode, ModNode, GeNode, LtNode, SumNode, AndNode
from tinygrad.codegen.cstyle import code_for_op, render_cl

def uops_to_webgpu_ir(uops:List[UOp], bufs:List[LazyBuffer]) -> str:
  kernel = []
  bufnames = [f"data{i}" for i,b in enumerate(bufs)]
  depth = 1
  def kk(s): kernel.append("  "*depth+s)

  for uop,newvar,vin,args in uops:
    if uop == UOps.CONST:
      # There'S no infinity builtin yet: https://github.com/gpuweb/gpuweb/issues/3431
      kk(f"{newvar.render(True)} = {args if args != -math.inf else '-0x1.fffffep+127'}f;")
    if uop == UOps.LOOP:
      pass
    if uop == UOps.ENDLOOP:
      pass
    if uop == UOps.LOAD:
      val = f"{bufnames[args.i]}[{args.idx.render(render_cl)}]"
      if args.valid.min == 1: kk(f"let {newvar.name} = {val};")
      else: kk(f"let {newvar.name} = ({args.valid.render(render_cl)}) ? ({val}) : 0.0f;")
    if uop == UOps.STORE:
      assert args.valid.min == 1, "store must be valid"
      kk(f"{bufnames[args.i]}[{args.idx.render(render_cl)}] = {vin[0].render()};")
    elif uop == UOps.ALU:
      assert newvar is not None
      kk(f"let {newvar.render()} = {code_for_op[args](*[x.render() for x in vin])};")
  join_newline = lambda lines:'\n'.join(lines)
  return f"""
@group(0) @binding(0) var<storage, read_write> data0 : array<f32>;
{join_newline([f'@group(0) @binding({i}) var<storage, read> data{i} : array<f32>;' for i in range(1, len(bufs))])}

@compute @workgroup_size(8, 1)
fn main(@builtin(global_invocation_id) global_id : vec3<u32>) {{
{join_newline(kernel).replace('gidx0', 'global_id.x')}
}}"""

class WebGPUCodegen(Linearizer):
  def codegen(self):
    self.process()
    # no optimize, this doesn't support local
    self.linearize()
    return ASTRunner('exec', uops_to_webgpu_ir(self.uops, self.bufs), op_estimate=self.info.flops, mem_estimate=self.mem_estimate, display_name=self.display_name)
