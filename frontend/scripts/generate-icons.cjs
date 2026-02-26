#!/usr/bin/env node
/**
 * Generates PNG icon files for the PWA manifest using only Node.js built-ins.
 * Creates solid terracotta (#c95d1b) squares with a simple white house shape.
 * Run: node scripts/generate-icons.js
 */

const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const STATIC_DIR = path.join(__dirname, '..', 'static');

// Brand colors
const BG = [201, 93, 27];    // #c95d1b terracotta
const FG = [255, 255, 255];   // white

/**
 * Create a minimal valid PNG from raw RGBA pixel data.
 */
function createPng(width, height, getPixel) {
  // Raw image data: each row = filter byte (0) + RGB pixels
  const rawRows = [];
  for (let y = 0; y < height; y++) {
    const row = Buffer.alloc(1 + width * 3);
    row[0] = 0; // filter type: None
    for (let x = 0; x < width; x++) {
      const [r, g, b] = getPixel(x, y, width, height);
      row[1 + x * 3] = r;
      row[1 + x * 3 + 1] = g;
      row[1 + x * 3 + 2] = b;
    }
    rawRows.push(row);
  }
  const rawData = Buffer.concat(rawRows);
  const compressed = zlib.deflateSync(rawData, { level: 9 });

  function crc32(buf) {
    const table = (() => {
      const t = new Uint32Array(256);
      for (let i = 0; i < 256; i++) {
        let c = i;
        for (let j = 0; j < 8; j++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
        t[i] = c;
      }
      return t;
    })();
    let c = 0xffffffff;
    for (let i = 0; i < buf.length; i++) c = table[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  }

  function chunk(type, data) {
    const typeBytes = Buffer.from(type, 'ascii');
    const lenBuf = Buffer.alloc(4);
    lenBuf.writeUInt32BE(data.length, 0);
    const crcInput = Buffer.concat([typeBytes, data]);
    const crcBuf = Buffer.alloc(4);
    crcBuf.writeUInt32BE(crc32(crcInput), 0);
    return Buffer.concat([lenBuf, typeBytes, data, crcBuf]);
  }

  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData[8] = 8;  // bit depth
  ihdrData[9] = 2;  // color type: RGB
  ihdrData[10] = 0; // compression
  ihdrData[11] = 0; // filter
  ihdrData[12] = 0; // interlace

  return Buffer.concat([
    signature,
    chunk('IHDR', ihdrData),
    chunk('IDAT', compressed),
    chunk('IEND', Buffer.alloc(0))
  ]);
}

/**
 * Draw the brand icon: terracotta background + simplified white house silhouette.
 * The house is drawn procedurally: a triangular roof + rectangular body + door.
 */
function brandIcon(x, y, w, h) {
  const cx = w / 2;
  const cy = h / 2;
  const scale = Math.min(w, h);

  // Background: rounded-ish square (just fill all with BG, corners handled by OS)
  // Check if pixel is inside the house shape
  const margin = scale * 0.12;
  const houseLeft = cx - scale * 0.28;
  const houseRight = cx + scale * 0.28;
  const houseBottom = cy + scale * 0.28;
  const roofTop = cy - scale * 0.32;
  const wallTop = cy - scale * 0.06;

  // Roof: triangle from roofTop-cx to wallTop corners
  // Use line equation: roof peak at (cx, roofTop), base corners at (houseLeft - margin*0.3, wallTop) and (houseRight + margin*0.3, wallTop)
  const roofLeft = houseLeft - scale * 0.04;
  const roofRight = houseRight + scale * 0.04;

  // Is the pixel inside the triangle (roof)?
  function inRoof() {
    // Triangle with vertices: (cx, roofTop), (roofLeft, wallTop), (roofRight, wallTop)
    const px = x, py = y;
    const ax = cx, ay = roofTop;
    const bx = roofLeft, by = wallTop;
    const dx = roofRight, dy = wallTop;
    // Barycentric-ish: check if y <= wallTop and above both slanted edges
    if (py > wallTop || py < roofTop) return false;
    const t = (py - ay) / (by - ay);
    const leftEdge = ax + t * (bx - ax);
    const rightEdge = ax + t * (dx - ax);
    return px >= leftEdge && px <= rightEdge;
  }

  // Is the pixel inside the house body (rectangle)?
  function inBody() {
    return x >= houseLeft && x <= houseRight && y >= wallTop && y <= houseBottom;
  }

  // Door: centered, bottom of house
  const doorW = scale * 0.12;
  const doorH = scale * 0.18;
  const doorLeft = cx - doorW / 2;
  const doorRight = cx + doorW / 2;
  const doorTop = houseBottom - doorH;

  function inDoor() {
    return x >= doorLeft && x <= doorRight && y >= doorTop && y <= houseBottom;
  }

  // Heart inside the door arch (small, subtle)
  // Skip heart for simplicity — just use solid door cutout as BG color

  if (inDoor()) return BG;
  if (inRoof() || inBody()) return FG;
  return BG;
}

const sizes = [
  { name: 'favicon.png', size: 32 },
  { name: 'apple-touch-icon.png', size: 180 },
  { name: 'icon-192.png', size: 192 },
  { name: 'icon-512.png', size: 512 },
];

for (const { name, size } of sizes) {
  const png = createPng(size, size, (x, y, w, h) => brandIcon(x, y, w, h));
  const outPath = path.join(STATIC_DIR, name);
  fs.writeFileSync(outPath, png);
  console.log(`✓ ${name} (${size}×${size})`);
}

console.log('Done. Icons written to frontend/static/');
