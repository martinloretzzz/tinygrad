import ast
import json
import subprocess

from extra.utils import fetch

lib = """
const getDevice = async () => (await nodeGPU.getNodeGPU().requestAdapter()).requestDevice();
const str2buf = (str) => new Float32Array(Uint8Array.from(str, c => c.charCodeAt(0)).buffer);

const createEmptyBuf = (device, floatLength) => {
	return device.createBuffer({size: floatLength * Float32Array.BYTES_PER_ELEMENT, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC });
};

const createWeightBuf = (device, floatLength, dataBuf) => {
	const buf = device.createBuffer({ mappedAtCreation: true, size: floatLength * Float32Array.BYTES_PER_ELEMENT, usage: GPUBufferUsage.STORAGE });
	new Float32Array(buf.getMappedRange()).set(dataBuf);
	buf.unmap();
	return buf;
};

const addComputePass = (device, commandEncoder, code, bufs, workgroup) => {
	const computePipeline = device.createComputePipeline({
		layout: "auto",
		compute: { module: device.createShaderModule({ code }), entryPoint: "main" },
	});

	const bindGroup = device.createBindGroup({
		layout: computePipeline.getBindGroupLayout(0),
		entries: bufs.map((buffer, index) => ({ binding: index, resource: { buffer } })),
	});

	const passEncoder = commandEncoder.beginComputePass();
	passEncoder.setPipeline(computePipeline);
	passEncoder.setBindGroup(0, bindGroup);
	passEncoder.dispatchWorkgroups(...workgroup);
	passEncoder.end();
};"""

f = open('../../examples/net.json')
data = json.load(f)
f.close()

kernel_code = f"\n\n".join([f"const {key} = `{code}`;" for key, code in data['functions'].items()])
weight_values = '\n'.join([f'const data_{key} = "{buf}";' for key, buf in data["bufs_to_save"].items() ])
   
kernel_calls = '\n    '.join([f"addComputePass(device, commandEncoder, {statement['kernel']}, [{', '.join(statement['args'])}], {statement['global_size']});" for statement in data["statements"] ])
bufs =  '\n    '.join([f"const {buf[0]} = createEmptyBuf(device, {buf[1]});" if buf[0] not in data["bufs_to_save"] and buf[0] != 'input' else f"const {buf[0]} = createWeightBuf(device, {buf[1]}, {'inputData' if buf[0] == 'input' else f'str2buf(data_{buf[0]})'});" for buf in data["bufs"].values() ])


prg_net = f"""

{lib}

{kernel_code}

{weight_values}
           
const net = async (device, inputData) => {{
	const commandEncoder = device.createCommandEncoder();

	{bufs}

	{kernel_calls}

    const gpuReadBuffer = device.createBuffer({{
		size: outputs.size,
		usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
	}});
    
	commandEncoder.copyBufferToBuffer(outputs, 0, gpuReadBuffer, 0, outputs.size);

	const gpuCommands = commandEncoder.finish();
	device.queue.submit([gpuCommands]);

	await gpuReadBuffer.mapAsync(GPUMapMode.READ);

    return gpuReadBuffer.getMappedRange();
}}


"""

prg_test = f"""
const nodeGPU = require("@axinging/webgpu");

{prg_net}

const main = async () => {{
	const device = await getDevice();
	const inputData = Float32Array.from([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
	console.log(inputData);
	const out = await net(device, inputData);
    console.log(Array.from(new Float32Array(out)))
}};

main();
"""

lbls = fetch("https://gist.githubusercontent.com/yrevar/942d3a0ac09ec9e5eb3a/raw/238f720ff059c1f82f368259d1ca4ffa5dd8f9f5/imagenet1000_clsidx_to_labels.txt")
lbls = ast.literal_eval(lbls.decode('utf-8'))
lbls = ', '.join(['"'+lbls[i]+'"' for i in range(1000)])

prg_efficientnet = f"""
const nodeGPU = require("@axinging/webgpu");
const sharp = require("sharp");

{prg_net}

const main = async () => {{
	const device = await getDevice();

	const image = await sharp("cat.jpg").resize({{ width: 224, height: 224 }}).raw().toBuffer();
	console.log("image");
    console.log(image)
	const pix = Array.from(Uint8Array.from(image)).map((pix) => (pix / 255.0 - 0.45) / 0.225);
    const arrx = [];
	let i = 0;
	for (let c = 0; c < 3; c++) {{
		for (let y = 0; y < 224; y++) {{
			for (let x = 0; x < 224; x++) {{
				arrx[i] = pix[c * 224 * 224 + x * 224 + y];
				i++;
			}}
		}}
	}}
    const inputData = arrx;
	console.log(inputData);

	const out = await net(device, inputData);

	const arr = Array.from(new Float32Array(out));
    console.log(arr)
    
    const labels = [{lbls}];

    const index = arr.indexOf(Math.max(...arr));
    console.log(index)
	console.log(labels[index]);
    
    const indices = [...arr.keys()].sort((a, b) => arr[b] - arr[a]);
	console.log("10 Biggest:")
    console.log(indices.slice(0, 10))
	for (const index of indices.slice(0, 10)) {{
    	console.log(labels[index]);
	}}
    

}};

main();
"""
prg = prg_efficientnet

with open("net.js", "w") as text_file:
    text_file.write(prg)
    
subprocess.run(['node', 'net.js'])