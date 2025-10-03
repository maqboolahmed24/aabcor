const fs = require('fs');
const sharp = require('sharp');

async function main() {
  const input = 'og.svg';
  const output = 'og.png';
  if (!fs.existsSync(input)) {
    console.error(`Missing ${input}`);
    process.exit(1);
  }
  await sharp(input, { density: 300 })
    .resize(1200, 630, { fit: 'cover' })
    .png({ quality: 90 })
    .toFile(output);
  console.log(`Wrote ${output}`);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});

