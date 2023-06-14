let readline = require("readline");
const nodeGPU = require("@axinging/webgpu");

const runKernel = async (device, code, bufs, outBufSize, workgroupGrid) => {
	const destBuf = device.createBuffer({
		size: outBufSize,
		usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC,
	});

	const gpuBufs = [destBuf];
	for (const buf of bufs) {
		const gpuBuf = device.createBuffer({ mappedAtCreation: true, size: buf.byteLength, usage: GPUBufferUsage.STORAGE });
		new Float32Array(gpuBuf.getMappedRange()).set(buf);
		gpuBuf.unmap();
		gpuBufs.push(gpuBuf);
	}

	// TODO why is this copy needed?
	const gpuReadBuffer = device.createBuffer({
		size: outBufSize,
		usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
	});

	const computePipeline = device.createComputePipeline({
		layout: "auto",
		compute: { module: device.createShaderModule({ code }), entryPoint: "main" },
	});

	const bindGroup = device.createBindGroup({
		layout: computePipeline.getBindGroupLayout(0),
		entries: gpuBufs.map((buffer, index) => ({ binding: index, resource: { buffer } })),
	});

	const commandEncoder = device.createCommandEncoder();

	const passEncoder = commandEncoder.beginComputePass();
	passEncoder.setPipeline(computePipeline);
	passEncoder.setBindGroup(0, bindGroup);
	passEncoder.dispatchWorkgroups(...workgroupGrid);
	passEncoder.end();

	commandEncoder.copyBufferToBuffer(destBuf, 0, gpuReadBuffer, 0, outBufSize);

	device.queue.submit([commandEncoder.finish()]);

	await gpuReadBuffer.mapAsync(GPUMapMode.READ);
	return new Float32Array(gpuReadBuffer.getMappedRange());
};

const getDevice = async () => {
	const GPU = nodeGPU.getNodeGPU();
	const adapter = await GPU.requestAdapter();
	return adapter.requestDevice();
};

async function readLine(line) {
	try {
		const data = JSON.parse(line.replace(/\bNaN\b/g, "null"));
		const device = await getDevice();
		const buf = await runKernel(
			device,
			data.code,
			data.bufs.map((arr) => new Float32Array(arr.map((v) => (v === null ? NaN : v)))),
			data.out_size * Float32Array.BYTES_PER_ELEMENT,
			data.workgroup_grid
		);

		console.log(JSON.stringify(Array.from(buf)));
	} catch (error) {
		console.log(error);
	}
}

let rl = readline.createInterface({ input: process.stdin });
rl.on("line", readLine);
