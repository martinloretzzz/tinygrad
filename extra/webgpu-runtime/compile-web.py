import ast
import json

from extra.utils import fetch

f = open('../../examples/net.json')

data = json.load(f)
f.close()

prg = []
prg.append('const nodeGPU = require("@axinging/webgpu");\nconst sharp = require("sharp");')
prg.append('\n'.join([f"const {key} = `{code}`\n" for key, code in data['functions'].items()]))
prg.append("""

const getDevice = async () => {
	const GPU = nodeGPU.getNodeGPU();
	const adapter = await GPU.requestAdapter();
	return adapter.requestDevice();
};

const str2buf = (str) => {
	const bytes = Uint8Array.from(str, c => c.charCodeAt(0))
	return new Float32Array(bytes.buffer)
}

const createBufFromData = (device, floatLength, dataBuf) => {
	const buf = device.createBuffer({ mappedAtCreation: true, size: Float32Array.BYTES_PER_ELEMENT * floatLength, usage: GPUBufferUsage.STORAGE });
	new Float32Array(buf.getMappedRange()).set(dataBuf);
	buf.unmap();
	return buf;
};



const createDestBuf = (device, floatLength) => {
	return device.createBuffer({
		size: floatLength * Float32Array.BYTES_PER_ELEMENT,
		usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC,
	});
};

const addComputePass = (device, commandEncoder, code, bufs, workgroup) => {
	const computePipeline = device.createComputePipeline({
		layout: "auto",
		compute: {
			module: device.createShaderModule({ code }),
			entryPoint: "main",
		},
	});

	const bindGroup = device.createBindGroup({
		layout: computePipeline.getBindGroupLayout(0),
		entries: bufs.map((buffer, index) => ({ binding: index, resource: { buffer } })),
	});

	const passEncoder = commandEncoder.beginComputePass();
	passEncoder.setPipeline(computePipeline);
	passEncoder.setBindGroup(0, bindGroup);
	passEncoder.dispatchWorkgroups(Math.ceil(workgroup[0] / 64), workgroup.length > 1 ? workgroup[1] : 1, workgroup.length > 2 ? workgroup[2] : 1);
	passEncoder.end();
};

const createResultCopyBuf = (device, byteSize) => {
	// TODO why is this copy needed?
	// Get a GPU buffer for reading in an unmapped state.
	return device.createBuffer({
		size: byteSize,
		usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
	});
};""")
           
kernel_calls = '\n'.join([f"addComputePass(device, commandEncoder, {statement['kernel']}, [{', '.join(statement['args'])}], {statement['global_size']});" for statement in data["statements"] ])
bufs =  '\n'.join([f"const {buf[0]} = createDestBuf(device, {buf[1]});" if buf[0] not in data["bufs_to_save"] and buf[0] != 'input' else f"const {buf[0]} = createBufFromData(device, {buf[1]}, {'inputArr' if buf[0] == 'input' else f'str2buf(data_{buf[0]})'});" for buf in data["bufs"].values() ])

weights = '\n'.join([f'const data_{key} = "{buf}";' for key,buf in data["bufs_to_save"].items() ])

lbls = fetch("https://gist.githubusercontent.com/yrevar/942d3a0ac09ec9e5eb3a/raw/238f720ff059c1f82f368259d1ca4ffa5dd8f9f5/imagenet1000_clsidx_to_labels.txt")
lbls = ast.literal_eval(lbls.decode('utf-8'))
lbls = ', '.join(['"'+lbls[i]+'"' for i in range(1000)])

prg.append(f"""
const main = async () => {{
	const device = await getDevice();
	const commandEncoder = device.createCommandEncoder();

	const image = await sharp("hen.jpg").resize({{ width: 224, height: 224 }}).raw().toBuffer();
    console.log(image)
	const inputArr = Array.from(Uint8Array.from(image)).map((pix) => 2 * ((pix / 255.0) - 0.5));
    
	console.log(inputArr);
    {weights}
   
{bufs}
	const gpuReadBuffer = createResultCopyBuf(device, outputs.size);

{kernel_calls}

	commandEncoder.copyBufferToBuffer(outputs, 0, gpuReadBuffer, 0, outputs.size);

	const gpuCommands = commandEncoder.finish();
	device.queue.submit([gpuCommands]);

	await gpuReadBuffer.mapAsync(GPUMapMode.READ);
    
    const labels = [{lbls}];
    
    const arr = Array.from(new Float32Array(gpuReadBuffer.getMappedRange()))
	const index = 310; //arr.indexOf(Math.max(...arr));
    console.log(index)
    

	console.log(labels[index]);
}};

main();
""")


with open("net.js", "w") as text_file:
    text_file.write('\n'.join(prg))