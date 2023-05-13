import time, hashlib, ctypes
from typing import ClassVar
from tinygrad.ops import Compiled
from tinygrad.helpers import getenv, DEBUG
from ctypes import CFUNCTYPE
from tinygrad.codegen.llvmir import LLVMIRCodegen
from tinygrad.runtime.lib import RawMallocBuffer

import json
import os
import subprocess
import numpy as np

class WEBGPUProgram:
  def __init__(self, name:str, prg:str, binary=False):
    print(prg)

  def __call__(self, unused_global_size, unused_local_size, *bufs, wait=False):
    if wait: st = time.monotonic()

    code = '''
    @group(0) @binding(0) var<storage, read_write> output : array<f32>;
    @group(0) @binding(1) var<storage, read> input1 : array<f32>;
    @group(0) @binding(2) var<storage, read> input2 : array<f32>;

    @compute @workgroup_size(8, 1)
    fn main(@builtin(global_invocation_id) global_id : vec3<u32>) {
        output[global_id.x] = input1[global_id.x] + input2[global_id.x];
    }'''

    p = subprocess.Popen(['node', './extra/webgpu-runtime/webgpu-runtime.js'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    data_str = json.dumps({'code':code, 'bufs': [buf.toCPU().flatten().tolist() for buf in bufs[1:]]})
    out = p.communicate(input=(data_str + os.linesep).encode())[0]
    print(out[0:2000])
    z = np.array(json.loads(out.decode()), dtype=np.float32)
    np.copyto(bufs[0].toCPU(), z)

    if wait: return time.monotonic()-st

WEBGPUBuffer = Compiled(RawMallocBuffer, LLVMIRCodegen, WEBGPUProgram)





