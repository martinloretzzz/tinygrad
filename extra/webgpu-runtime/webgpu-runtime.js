let readline = require("readline");
const nodeGPU = require("@axinging/webgpu");

const runKernel = async (device, code, bufs) => {
	const gpuBufs = [];
	for (const buf of bufs) {
		const gpuBuf = device.createBuffer({ mappedAtCreation: true, size: buf.byteLength, usage: GPUBufferUsage.STORAGE });
		new Float32Array(gpuBuf.getMappedRange()).set(buf);
		gpuBuf.unmap();
		gpuBufs.push(gpuBuf);
	}

	const destBufSize = bufs[0].byteLength;
	const destBuf = device.createBuffer({ size: destBufSize, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC });

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
		entries: [destBuf, ...gpuBufs].map((buffer, index) => ({ binding: index, resource: { buffer } })),
	});

	const commandEncoder = device.createCommandEncoder();

	const passEncoder = commandEncoder.beginComputePass();
	passEncoder.setPipeline(computePipeline);
	passEncoder.setBindGroup(0, bindGroup);
	const workgroupCountX = Math.ceil(bufs[0].length / 8);
	passEncoder.dispatchWorkgroups(workgroupCountX, 1);
	passEncoder.end();

	// TODO why is this copy needed?
	// Get a GPU buffer for reading in an unmapped state.
	const gpuReadBuffer = device.createBuffer({
		size: destBufSize,
		usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
	});

	commandEncoder.copyBufferToBuffer(destBuf, 0, gpuReadBuffer, 0, destBufSize);

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
				data.bufs.map((arr) => new Float32Array(arr))
			);

			console.log(JSON.stringify(Array.from(buf)));
  } catch (error) {
    console.log(error)
  }
}

rl.on("line", readLine);
