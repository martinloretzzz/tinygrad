let readline = require("readline");
const nodeGPU = require("@axinging/webgpu");

const getDevice = async () => {
	const GPU = nodeGPU.getNodeGPU();
	const adapter = await GPU.requestAdapter();
	return adapter.requestDevice();
};

const createBufFromData = (device, cpuBuf) => {
	const buf = device.createBuffer({ mappedAtCreation: true, size: cpuBuf.byteLength, usage: GPUBufferUsage.STORAGE });
	new Float32Array(buf.getMappedRange()).set(cpuBuf);
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
	passEncoder.dispatchWorkgroups(...workgroup);
	passEncoder.end();
};

const createResultCopyBuf = (device, byteSize) => {
	// TODO why is this copy needed?
	// Get a GPU buffer for reading in an unmapped state.
	return device.createBuffer({
		size: byteSize,
		usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
	});
};

const kernel1 = `
@group(0) @binding(0) var<storage, read_write> output : array<f32>;
@group(0) @binding(1) var<storage, read> input1 : array<f32>;
@group(0) @binding(2) var<storage, read> input2 : array<f32>;

@compute @workgroup_size(8, 1)
fn main(@builtin(global_invocation_id) global_id : vec3<u32>) {
	output[global_id.x] = input1[global_id.x] + input2[global_id.x];
}
`;

const kernel2 = `
@group(0) @binding(0) var<storage, read_write> output : array<f32>;
@group(0) @binding(1) var<storage, read> input1 : array<f32>;
@group(0) @binding(2) var<storage, read> input2 : array<f32>;

@compute @workgroup_size(8, 1)
fn main(@builtin(global_invocation_id) global_id : vec3<u32>) {
	output[global_id.x] = input1[global_id.x] * input2[global_id.x];
}
`;

const main = async () => {
	const device = await getDevice();
	const commandEncoder = device.createCommandEncoder();

	const dest0 = createDestBuf(device, 4);
	const dest1 = createDestBuf(device, 4);
	const input0 = createBufFromData(device, new Float32Array([1, 2, 3, 4]));
	const input1 = createBufFromData(device, new Float32Array([1, 2, 3, 4]));
	const input2 = createBufFromData(device, new Float32Array([2, 2, 2, 2]));
	const gpuReadBuffer = createResultCopyBuf(device, dest1.size);

	addComputePass(device, commandEncoder, kernel1, [dest0, input0, input1], [1]);
	addComputePass(device, commandEncoder, kernel2, [dest1, dest0, input2], [1]);

	commandEncoder.copyBufferToBuffer(dest1, 0, gpuReadBuffer, 0, dest1.size);

	const gpuCommands = commandEncoder.finish();
	device.queue.submit([gpuCommands]);

	await gpuReadBuffer.mapAsync(GPUMapMode.READ);

	console.log(Array.from(new Float32Array(gpuReadBuffer.getMappedRange())));
};

main();
