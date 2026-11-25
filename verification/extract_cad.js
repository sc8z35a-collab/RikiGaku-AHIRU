#!/usr/bin/env node
/**
 * Bit-exact 3D CAD Mesh Extractor for RikiGaku-AHIRU (index.html)
 *
 * Executes the actual procedural CAD mesh builders inside index.html using a
 * minimal WebGL/DOM buffer interceptor, exporting every single part as a binary
 * STL (in both assembled world coordinates and local part coordinates) plus a
 * complete JSON assembly manifest with exact kinematic metadata.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const args = process.argv.slice(2);
const htmlPath = path.resolve(args[0] || path.join(__dirname, '..', 'index.html'));
const outDir = path.resolve(args[1] || path.join(__dirname, '..', 'verification_out', 'cad'));

fs.mkdirSync(path.join(outDir, 'stl_world'), { recursive: true });
fs.mkdirSync(path.join(outDir, 'stl_local'), { recursive: true });

const html = fs.readFileSync(htmlPath, 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.error('ERROR: Could not locate <script> block in ' + htmlPath);
  process.exit(1);
}

let jsSrc = scriptMatch[1];
const anchorNeedle = 'const state = {';
if (!jsSrc.includes(anchorNeedle)) {
  console.error('ERROR: Could not locate state initialization anchor in index.html');
  process.exit(1);
}

// Inject clean extraction hook immediately after `parts` array is constructed
jsSrc = jsSrc.replace(
  anchorNeedle,
  'globalThis.__AHIRU_EXTRACT__ = { parts, GROUPS, EX }; return; ' + anchorNeedle
);

// Minimal WebGL buffer interceptor capturing raw Float32/Uint16/Uint32 buffers
let nextBufId = 1;
const boundBuffers = {};
const mockGL = {
  VERTEX_SHADER: 0x8b31,
  FRAGMENT_SHADER: 0x8b30,
  COMPILE_STATUS: 0x8b81,
  LINK_STATUS: 0x8b82,
  ARRAY_BUFFER: 0x8892,
  ELEMENT_ARRAY_BUFFER: 0x8893,
  STATIC_DRAW: 0x88e4,
  UNSIGNED_INT: 0x1405,
  UNSIGNED_SHORT: 0x1403,
  createShader: () => ({}),
  shaderSource: () => {},
  compileShader: () => {},
  getShaderParameter: () => true,
  getShaderInfoLog: () => '',
  createProgram: () => ({}),
  attachShader: () => {},
  linkProgram: () => {},
  getProgramParameter: () => true,
  getProgramInfoLog: () => '',
  getAttribLocation: () => 0,
  getUniformLocation: () => 0,
  createBuffer: () => ({ __id: nextBufId++, data: null }),
  bindBuffer: (target, buf) => { boundBuffers[target] = buf; },
  bufferData: (target, data) => {
    if (boundBuffers[target]) {
      boundBuffers[target].data = data;
    }
  }
};

const mockCanvas = {
  getContext: () => mockGL,
  addEventListener: () => {},
  clientWidth: 1280,
  clientHeight: 720,
  width: 1280,
  height: 720
};

const sandbox = {
  console,
  Math,
  Float32Array,
  Uint16Array,
  Uint32Array,
  Int32Array,
  Map,
  Set,
  Array,
  Object,
  Number,
  String,
  Boolean,
  JSON,
  document: {
    getElementById: (id) => (id === 'gl' ? mockCanvas : { addEventListener: () => {}, classList: { toggle: () => {}, remove: () => {} }, style: {}, appendChild: () => {} }),
    createElement: () => ({ addEventListener: () => {}, classList: { toggle: () => {}, remove: () => {} }, style: {} })
  },
  window: {
    addEventListener: () => {},
    devicePixelRatio: 1
  },
  performance: { now: () => 0 },
  requestAnimationFrame: () => {}
};
sandbox.globalThis = sandbox;

vm.runInNewContext(jsSrc, sandbox, { filename: 'index.html' });

const extracted = sandbox.__AHIRU_EXTRACT__;
if (!extracted || !Array.isArray(extracted.parts)) {
  console.error('ERROR: Failed to extract parts from index.html');
  process.exit(1);
}

function writeBinarySTL(filePath, pos, idx, offset) {
  const ox = offset ? offset[0] : 0;
  const oy = offset ? offset[1] : 0;
  const oz = offset ? offset[2] : 0;
  const numTris = Math.floor(idx.length / 3);
  const buf = Buffer.alloc(84 + numTris * 50);
  buf.write('RikiGaku-AHIRU Bit-Exact CAD Export (mm)', 0, 'ascii');
  buf.writeUInt32LE(numTris, 80);

  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
  let signedVol6 = 0.0;
  let surfArea = 0.0;

  let off = 84;
  for (let t = 0; t < numTris; t++) {
    const i0 = idx[t * 3] * 3;
    const i1 = idx[t * 3 + 1] * 3;
    const i2 = idx[t * 3 + 2] * 3;

    const x0 = pos[i0] + ox, y0 = pos[i0 + 1] + oy, z0 = pos[i0 + 2] + oz;
    const x1 = pos[i1] + ox, y1 = pos[i1 + 1] + oy, z1 = pos[i1 + 2] + oz;
    const x2 = pos[i2] + ox, y2 = pos[i2 + 1] + oy, z2 = pos[i2 + 2] + oz;

    if (x0 < minX) minX = x0; if (x0 > maxX) maxX = x0;
    if (y0 < minY) minY = y0; if (y0 > maxY) maxY = y0;
    if (z0 < minZ) minZ = z0; if (z0 > maxZ) maxZ = z0;
    if (x1 < minX) minX = x1; if (x1 > maxX) maxX = x1;
    if (y1 < minY) minY = y1; if (y1 > maxY) maxY = y1;
    if (z1 < minZ) minZ = z1; if (z1 > maxZ) maxZ = z1;
    if (x2 < minX) minX = x2; if (x2 > maxX) maxX = x2;
    if (y2 < minY) minY = y2; if (y2 > maxY) maxY = y2;
    if (z2 < minZ) minZ = z2; if (z2 > maxZ) maxZ = z2;

    const ux = x1 - x0, uy = y1 - y0, uz = z1 - z0;
    const vx = x2 - x0, vy = y2 - y0, vz = z2 - z0;
    let nx = uy * vz - uz * vy;
    let ny = uz * vx - ux * vz;
    let nz = ux * vy - uy * vx;
    const nl = Math.hypot(nx, ny, nz);
    surfArea += 0.5 * nl;
    if (nl > 1e-12) { nx /= nl; ny /= nl; nz /= nl; } else { nx = 0; ny = 0; nz = 0; }

    // Signed volume contribution: dot(p0, cross(p1, p2)) / 6
    const cx = y1 * z2 - z1 * y2;
    const cy = z1 * x2 - x1 * z2;
    const cz = x1 * y2 - y1 * x2;
    signedVol6 += x0 * cx + y0 * cy + z0 * cz;

    buf.writeFloatLE(nx, off); off += 4;
    buf.writeFloatLE(ny, off); off += 4;
    buf.writeFloatLE(nz, off); off += 4;
    buf.writeFloatLE(x0, off); off += 4;
    buf.writeFloatLE(y0, off); off += 4;
    buf.writeFloatLE(z0, off); off += 4;
    buf.writeFloatLE(x1, off); off += 4;
    buf.writeFloatLE(y1, off); off += 4;
    buf.writeFloatLE(z1, off); off += 4;
    buf.writeFloatLE(x2, off); off += 4;
    buf.writeFloatLE(y2, off); off += 4;
    buf.writeFloatLE(z2, off); off += 4;
    buf.writeUInt16LE(0, off); off += 2;
  }

  fs.writeFileSync(filePath, buf);
  return {
    triangles: numTris,
    vertices: Math.floor(pos.length / 3),
    bbox_min: [minX, minY, minZ],
    bbox_max: [maxX, maxY, maxZ],
    bbox_size: [maxX - minX, maxY - minY, maxZ - minZ],
    signed_volume_mm3: signedVol6 / 6.0,
    surface_area_mm2: surfArea
  };
}

const manifestParts = [];
const allWorldTris = [];

for (const p of extracted.parts) {
  const pos = p.mesh.posBuf.data;
  const idx = p.mesh.idxBuf.data;
  const basePos = p.basePos || [0, 0, 0];

  const worldFile = path.join(outDir, 'stl_world', `${p.name}.stl`);
  const localFile = path.join(outDir, 'stl_local', `${p.name}.stl`);

  const worldStats = writeBinarySTL(worldFile, pos, idx, basePos);
  writeBinarySTL(localFile, pos, idx, [0, 0, 0]);

  if (!p.isPlasma) {
    allWorldTris.push({ pos, idx, basePos });
  }

  manifestParts.push({
    name: p.name,
    group: p.group,
    anim: p.anim || null,
    basePos,
    explode: p.explode || [0, 0, 0],
    anchor: p.anchor || [0, 0, 0],
    isShell: p.isShell || null,
    isCutawayHide: Boolean(p.isCutawayHide),
    isTransparent: Boolean(p.isTransparent),
    isPlasma: Boolean(p.isPlasma),
    heatGlow: p.heatGlow || 0,
    color: p.color,
    metal: p.metal,
    rough: p.rough,
    alpha: p.alpha,
    stl_world: worldFile,
    stl_local: localFile,
    ...worldStats
  });
}

// Write combined assembled STL (excluding visual plasma glow)
let totalTris = 0;
for (const m of allWorldTris) totalTris += Math.floor(m.idx.length / 3);
const combinedBuf = Buffer.alloc(84 + totalTris * 50);
combinedBuf.write('RikiGaku-AHIRU Full Assembly (mm)', 0, 'ascii');
combinedBuf.writeUInt32LE(totalTris, 80);
let off = 84;
for (const m of allWorldTris) {
  const { pos, idx, basePos } = m;
  const [ox, oy, oz] = basePos;
  const nt = Math.floor(idx.length / 3);
  for (let t = 0; t < nt; t++) {
    const i0 = idx[t * 3] * 3, i1 = idx[t * 3 + 1] * 3, i2 = idx[t * 3 + 2] * 3;
    const x0 = pos[i0] + ox, y0 = pos[i0 + 1] + oy, z0 = pos[i0 + 2] + oz;
    const x1 = pos[i1] + ox, y1 = pos[i1 + 1] + oy, z1 = pos[i1 + 2] + oz;
    const x2 = pos[i2] + ox, y2 = pos[i2 + 1] + oy, z2 = pos[i2 + 2] + oz;
    const ux = x1 - x0, uy = y1 - y0, uz = z1 - z0;
    const vx = x2 - x0, vy = y2 - y0, vz = z2 - z0;
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const nl = Math.hypot(nx, ny, nz) || 1;
    combinedBuf.writeFloatLE(nx / nl, off); off += 4;
    combinedBuf.writeFloatLE(ny / nl, off); off += 4;
    combinedBuf.writeFloatLE(nz / nl, off); off += 4;
    combinedBuf.writeFloatLE(x0, off); off += 4; combinedBuf.writeFloatLE(y0, off); off += 4; combinedBuf.writeFloatLE(z0, off); off += 4;
    combinedBuf.writeFloatLE(x1, off); off += 4; combinedBuf.writeFloatLE(y1, off); off += 4; combinedBuf.writeFloatLE(z1, off); off += 4;
    combinedBuf.writeFloatLE(x2, off); off += 4; combinedBuf.writeFloatLE(y2, off); off += 4; combinedBuf.writeFloatLE(z2, off); off += 4;
    combinedBuf.writeUInt16LE(0, off); off += 2;
  }
}
const combinedPath = path.join(outDir, 'ahiru_full_assembly.stl');
fs.writeFileSync(combinedPath, combinedBuf);

// Compute global assembly bounding box (excluding plasma)
const solidParts = manifestParts.filter((p) => !p.isPlasma);
const gMin = [0, 1, 2].map((k) => Math.min(...solidParts.map((p) => p.bbox_min[k])));
const gMax = [0, 1, 2].map((k) => Math.max(...solidParts.map((p) => p.bbox_max[k])));

const manifest = {
  source_html: htmlPath,
  engine_axis_x_mm: extracted.EX,
  part_count: manifestParts.length,
  total_triangles: totalTris,
  assembly_stl: combinedPath,
  global_bbox_min_mm: gMin,
  global_bbox_max_mm: gMax,
  global_envelope_mm: [gMax[0] - gMin[0], gMax[1] - gMin[1], gMax[2] - gMin[2]],
  groups: extracted.GROUPS,
  parts: manifestParts
};

const manifestPath = path.join(outDir, 'assembly_manifest.json');
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

console.log(JSON.stringify({
  status: 'OK',
  parts: manifestParts.length,
  total_triangles: totalTris,
  global_bbox_min_mm: gMin.map((v) => Number(v.toFixed(3))),
  global_bbox_max_mm: gMax.map((v) => Number(v.toFixed(3))),
  global_envelope_mm: manifest.global_envelope_mm.map((v) => Number(v.toFixed(3))),
  manifest: manifestPath
}, null, 2));
