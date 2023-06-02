const sharp = require("sharp");

const init = async () => {
	const image = await sharp("input.jpg").resize({ width: 16, height: 16 }).raw().toBuffer();
	const pix = Array.from(Uint8Array.from(image)).map((pix) => (pix / 255.0 - 0.45) / 0.225);
	const arr = [];
	let i = 0;
	for (let c = 0; c < 3; c++) {
		for (let y = 0; y < 224; y++) {
			for (let x = 0; x < 224; x++) {
				arr[i] = pix[c * 224 * 224 + y * 224 + x];
				i++;
			}
		}
	}
	console.log(arr);
};
init();
