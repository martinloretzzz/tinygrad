import time
import json
import os
import subprocess
import numpy as np
from tinygrad.ops import Compiled
from tinygrad.codegen.webgpu import WebGPUCodegen
from tinygrad.runtime.lib import RawMallocBuffer

class WEBGPUProgram:
  def __init__(self, name:str, prg:str, binary=False): self.code = prg

  def __call__(self, global_size, unused_local_size, *bufs, wait=False):
    if wait: st = time.monotonic()
    self.global_size = global_size
    p = subprocess.Popen(['node', './extra/webgpu-runtime/webgpu-runtime.js'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    data = {'code':self.code, 'out_size': bufs[0].size, 'workgroup_grid': global_size,'bufs': [buf.toCPU().flatten().tolist() for buf in bufs[1:]]}
    result_str = p.communicate(input=(json.dumps(data) + os.linesep).encode())[0].decode()
    # print(result_str[0:2000])
    z = np.array(json.loads(result_str), dtype=np.float32)
    np.copyto(bufs[0].toCPU(), z)
    if wait: return time.monotonic()-st

WEBGPUBuffer = Compiled(RawMallocBuffer, WebGPUCodegen, WEBGPUProgram)
