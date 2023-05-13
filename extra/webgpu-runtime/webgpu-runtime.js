let readline = require("readline");
const nodeGPU = require("@axinging/webgpu");

const runKernel = async (device, code, bufs, outBufSize, workgroupSize) => {
	const destBuf = device.createBuffer({
		size: outBufSize * Float32Array.BYTES_PER_ELEMENT,
		usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC,
	});

	const gpuBufs = [destBuf];
	for (const buf of bufs) {
		const gpuBuf = device.createBuffer({ mappedAtCreation: true, size: buf.byteLength, usage: GPUBufferUsage.STORAGE });
		new Float32Array(gpuBuf.getMappedRange()).set(buf);
		gpuBuf.unmap();
		gpuBufs.push(gpuBuf);
	}

	const shaderModule = device.createShaderModule({ code });

	const computePipeline = device.createComputePipeline({
		layout: "auto",
		compute: {
			module: shaderModule,
			entryPoint: "main",
		},
	});

	const bindGroup = device.createBindGroup({
		layout: computePipeline.getBindGroupLayout(0),
		entries: gpuBufs.map((buffer, index) => ({ binding: index, resource: { buffer } })),
	});

	const commandEncoder = device.createCommandEncoder();

	const passEncoder = commandEncoder.beginComputePass();
	passEncoder.setPipeline(computePipeline);
	passEncoder.setBindGroup(0, bindGroup);

	const workgroupX = Math.ceil(workgroupSize[0] / 64);
	const workgroupY = workgroupSize.length > 1 ? Math.ceil(workgroupSize[1] / 1) : 1;
	const workgroupZ = workgroupSize.length > 2 ? Math.ceil(workgroupSize[2] / 1) : 1;
	passEncoder.dispatchWorkgroups(workgroupX, workgroupY, workgroupZ);
	passEncoder.end();

	// TODO why is this copy needed?
	// Get a GPU buffer for reading in an unmapped state.
	const gpuReadBuffer = device.createBuffer({
		size: outBufSize * Float32Array.BYTES_PER_ELEMENT,
		usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
	});

	commandEncoder.copyBufferToBuffer(destBuf, 0, gpuReadBuffer, 0, outBufSize * Float32Array.BYTES_PER_ELEMENT);

	const gpuCommands = commandEncoder.finish();
	device.queue.submit([gpuCommands]);

	await gpuReadBuffer.mapAsync(GPUMapMode.READ);
	return new Float32Array(gpuReadBuffer.getMappedRange());
};

const getDevice = async () => {
	const GPU = nodeGPU.getNodeGPU();
	const adapter = await GPU.requestAdapter();
	return adapter.requestDevice();
};

let rl = readline.createInterface({ input: process.stdin });

async function readLine(line) {
	try {
		const data = JSON.parse(line);
		const device = await getDevice();
		const buf = await runKernel(
			device,
			data.code,
			data.bufs.map((arr) => new Float32Array(arr)),
			data.out_size,
			data.workgroup_size
		);

		console.log(JSON.stringify(Array.from(buf)));
	} catch (error) {
		console.log(error);
	}
}

rl.on("line", readLine);
