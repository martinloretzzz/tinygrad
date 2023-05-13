import json
import os
import subprocess
import numpy as np

code = '''
@group(0) @binding(0) var<storage, read_write> output : array<f32>;
@group(0) @binding(1) var<storage, read> input1 : array<f32>;
@group(0) @binding(2) var<storage, read> input2 : array<f32>;

@compute @workgroup_size(8, 1)
fn main(@builtin(global_invocation_id) global_id : vec3<u32>) {
    output[global_id.x] = input1[global_id.x] * input2[global_id.x];
}'''

p = subprocess.Popen(['node', './webgpu-runtime.js', 'TENSOR1'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

x = np.random.rand(32*4096)
y = np.random.rand(32*4096)

data_str = json.dumps({'code':code, 'bufs': [x.tolist(), y.tolist()]})
out = p.communicate(input=(data_str + os.linesep).encode())[0]
print(out[0:2000])
z = np.array(json.loads(out.decode()))

print(z)
print(x * y)
print(np.allclose(z, x*y))
