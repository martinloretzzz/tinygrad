import collections
from math import ceil, log2, prod, inf
from typing import DefaultDict, Dict, Final, List, Tuple
from tinygrad.codegen.linearizer import Linearizer, UOps, UOp
from tinygrad.helpers import colored
from tinygrad.ops import ASTRunner, BinaryOps
from tinygrad.lazy import LazyBuffer
from tinygrad.runtime.lib import RawConst

from tinygrad.shape.symbolic import NumNode
from tinygrad.codegen.cstyle import code_for_op as cstyle_code_for_op, render_cl

code_for_op = cstyle_code_for_op.copy()
code_for_op[BinaryOps.CMPEQ] = lambda a,b: f"f32({a}=={b})"

def uops_to_webgpu_ir(uops:List[UOp], bufs:List[LazyBuffer]) -> str:
  kernel = []
  bufnames = [f"data{i}" for i,b in enumerate(bufs)]
  global_size = []
  const_buf = []
  gid = ['global_id.x', 'global_id.y', 'global_id.z']
  depth = 1
  def kk(s): kernel.append("  "*depth+s)

  for uop,newvar,vin,args in uops:
    if uop == UOps.CONST:
      # There'S no infinity builtin yet: https://github.com/gpuweb/gpuweb/issues/3431
      kk(f"var {newvar.render()} = {args if args != -inf else '-0x1.fffffep+127f'};")
    if uop == UOps.LOOP:
      for i,var in enumerate(args[0]):
        if isinstance(var, NumNode): continue
        if args[1] == "global":
          if len(args[0]) >= 4 and len(args[0])-i > 2:
            # sometimes, there's more dimensions. compact all the dimensions into the last CL dimension
            # TODO: these compactions should be searchable (they sort of are with reshapes and permutes)
            if i == 0:
              kk(f"{{ var {var.expr}:i32 = i32({gid[-1]}); /* {var.max+1} */")
              root = var.expr
              global_size.append(var.max+1)
            else:
              kk(f"{{ var {var.expr}:i32 = {root} % {var.max+1}; {root} /= {var.max+1};")
              global_size[-1] *= var.max+1
            if i == len(args[0]) - 2 - 1:
              kk(f"if(i32({gid[-1]}) >= {global_size[-1]}) {{ return; }} /* {global_size[-1]} */")
          else:
            kk(f"{{ var {var.expr}:i32 = i32({gid[len(args[0])-1-i]}); if({var.expr} >= {var.max+1}) {{ return; }} /* {var.max+1} */")
            global_size.append(var.max+1)
        else:
          kk(f"for (var {var.expr}:i32 = 0; {var.expr} <= {var.max}; {var.expr} = {var.expr} + 1) {{")
        depth += 1
    if uop == UOps.ENDLOOP:
      for var in args[0]:
        if isinstance(var, NumNode): continue
        depth -= 1
        kk("}")
    if uop == UOps.LOAD:
      if bufs[args.i] is not None and isinstance(bufs[args.i].realized, RawConst):
        # nan? inf?
        val = f"{bufs[args.i].realized._buf}f"
        const_buf.append(args.i)
      else:
        val = f"{bufnames[args.i]}[{args.idx.render(render_cl)}]"
      if args.valid.min == 1: kk(f"let {newvar.name} = {val};")
      else: kk(f"let {newvar.name} = select(0.0, ({val}), ({args.valid.render(render_cl)}));")
    if uop == UOps.STORE:
      assert args.valid.min == 1, "store must be valid"
      kk(f"{bufnames[args.i]}[{args.idx.render(render_cl)}] = {vin[0].render()};")
    elif uop == UOps.ALU:
      assert newvar is not None
      kk(f"{'let ' if newvar not in vin else ''}{newvar.render()} = {code_for_op[args](*[x.render() for x in vin])};")
  nl = '\n'

  # TODO refactor this
  bindings = ['@group(0) @binding(0) var<storage, read_write> data0 : array<f32>;']
  bindIndex = 0
  for i, buf in enumerate(bufs):
    if not isinstance(buf.realized, RawConst) and i > 0:
      bindIndex += 1
      bindings.append(f'@group(0) @binding({bindIndex}) var<storage, read> data{i} : array<f32>;')


  workgroup_grid, workgroup_size = optimize_workgroup_size(global_size[::-1])
  return f"""
{nl.join(bindings)}

@compute @workgroup_size({', '.join(map(str, workgroup_size))})
fn KERNEL_NAME_PLACEHOLDER(@builtin(global_invocation_id) global_id : vec3<u32>) {{
{nl.join(kernel)}
}}""", workgroup_grid

# TODO: find a better solution
def optimize_workgroup_size(global_size):
  log_org_size = [ceil(log2(x)) for x in global_size]
  log_goup_size = log_org_size.copy()
  i = 0
  while prod([int(2 ** x) for x in log_goup_size]) > 256: 
    log_goup_size = [max(ceil(x-1), log_org-16, 1) for x, log_org in zip(log_goup_size, log_org_size)]
    i += 1
    if i > 100: raise Exception("No solution found") # pylint: disable=broad-exception-raised

  workgroup_size = [int(2 ** log_goup_size[i]) if len(global_size) > i else 1 for i in range(3)]
  workgroup_grid = [ceil(global_size[i] / workgroup_size[i]) if len(global_size) > i else 1 for i in range(3)] 
  return workgroup_grid, workgroup_size

class WebGPUCodegen(Linearizer):
  supports_constant_folding: bool = True

  kernel_cnt: Final[DefaultDict[str, int]] = collections.defaultdict(int)
  kernel_name_cache: Final[Dict[str, Tuple[str, str]]] = {}

  def codegen(self):
    self.process()
    # no optimize, this doesn't support local
    self.linearize()
    prg, global_size = uops_to_webgpu_ir(self.uops, self.bufs)

    # painfully name the function something unique
    if prg in WebGPUCodegen.kernel_name_cache: function_name, _display_name = WebGPUCodegen.kernel_name_cache[prg]
    else:
      WebGPUCodegen.kernel_cnt[self.function_name] += 1
      suffix = f"{'n'+str(WebGPUCodegen.kernel_cnt[self.function_name]-1)}" if WebGPUCodegen.kernel_cnt[self.function_name] > 1 else ""
      WebGPUCodegen.kernel_name_cache[prg] = function_name, _display_name = self.function_name+suffix, self.display_name+colored(suffix, 'black', bright=True)

    return ASTRunner(function_name, prg.replace("KERNEL_NAME_PLACEHOLDER", "main"), global_size=global_size, op_estimate=self.info.flops, mem_estimate=self.mem_estimate, display_name=self.display_name)
