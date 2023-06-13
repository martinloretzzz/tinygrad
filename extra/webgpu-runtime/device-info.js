const nodeGPU = require("@axinging/webgpu");

const run = async () => {
	const GPU = nodeGPU.getNodeGPU();
    
	const adapter = await GPU.requestAdapter();
	const info = await adapter.requestAdapterInfo();
	console.log({
		architecture: info.architecture,
		description: info.description,
		device: info.device,
		vendor: info.vendor,
	});
	console.log(adapterLimits.maxStorageBufferBindingSize);

	const device = adapter.requestDevice();
	console.log(device.limits.maxStorageBufferBindingSize);
};

run();
