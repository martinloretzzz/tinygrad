import time
import json
import os
import subprocess
import numpy as np
from tinygrad.ops import Compiled
from tinygrad.codegen.webgpu import WebGPUCodegen
from tinygrad.runtime.lib import RawMallocBuffer

class WEBGPUProgram:
  def __init__(self, name:str, prg:str, binary=False):
    self.code = prg
    print(prg)

  def __call__(self, unused_global_size, unused_local_size, *bufs, wait=False):
    if wait: st = time.monotonic()

    p = subprocess.Popen(['node', './extra/webgpu-runtime/webgpu-runtime.js'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    data_str = json.dumps({'code':self.code, 'bufs': [buf.toCPU().flatten().tolist() for buf in bufs[1:]]})
    out = p.communicate(input=(data_str + os.linesep).encode())[0]
    print(out[0:2000])
    z = np.array(json.loads(out.decode()), dtype=np.float32)
    np.copyto(bufs[0].toCPU(), z)

    if wait: return time.monotonic()-st

WEBGPUBuffer = Compiled(RawMallocBuffer, WebGPUCodegen, WEBGPUProgram)
