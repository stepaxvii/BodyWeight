// Ported verbatim from branding/stories/district_yard.html per FIDELITY RULES.
// Entry: drawYard(ctx, t). Keep every drawing call, constant, color, loop bound exactly.

import { AV_FOX, AV_LION, type Rect } from "../sprites";

let ctx: CanvasRenderingContext2D;

const cv = { width: 200, height: 356 };
const W = cv.width, H = cv.height;
const reduce = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;

// ---------- helpers ----------
const R = (x: number, y: number, w: number, h: number, col: string) => { ctx.fillStyle = col; ctx.fillRect(x | 0, y | 0, Math.max(1, w | 0), Math.max(1, h | 0)); };
const A = (a: number, fn: () => void) => { ctx.globalAlpha = a; fn(); ctx.globalAlpha = 1; };
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
function mix(a: string, b: string, t: number) {
  const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
  const r = Math.round(lerp((pa >> 16) & 255, (pb >> 16) & 255, t)), g = Math.round(lerp((pa >> 8) & 255, (pb >> 8) & 255, t)), bl = Math.round(lerp(pa & 255, pb & 255, t));
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + bl).toString(16).slice(1);
}
function mulberry(s: number) { return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hash = (a: number) => { a = Math.sin(a) * 43758.5453; return a - Math.floor(a); };
function disc(cx: number, cy: number, r: number, col: string) { ctx.fillStyle = col; for (let y = -r; y <= r; y++) { const w = Math.floor(Math.sqrt(r * r - y * y) + 1e-3); ctx.fillRect((cx - w) | 0, (cy + y) | 0, 2 * w + 1, 1); } }
const discA = (cx: number, cy: number, r: number, col: string, a: number) => A(a, () => disc(cx, cy, r, col));
function glow(cx: number, cy: number, r: number, col: string) { discA(cx, cy, r, col, 0.08); discA(cx, cy, (r * 0.6) | 0, col, 0.1); }
function vgrad(x: number, y: number, w: number, h: number, c0: string, c1: string, bands: number) {
  const bh = h / bands; for (let i = 0; i < bands; i++) R(x, y + Math.floor(i * bh), w, Math.ceil(bh) + 1, mix(c0, c1, i / (bands - 1)));
  for (let i = 1; i < bands; i++) { const yy = y + Math.round(i * bh), ca = mix(c0, c1, (i - 1) / (bands - 1)); for (let xx = x + ((yy & 1) ? 0 : 1); xx < x + w; xx += 2) R(xx, yy, 1, 1, ca); }
}
function avatar(av: Rect[], cx: number, topY: number, sc: number) { for (const r of av) R(Math.round(cx - 16 * sc + r[0] * sc), Math.round(topY + r[1] * sc), Math.max(1, Math.round(r[2] * sc)), Math.max(1, Math.round(r[3] * sc)), r[4]); }

// ---------- palette (bright day) ----------
const C = {
  skyTop: '#4f94cf', skyHor: '#d2e8ec', sun: '#fff3c8',
  grass: '#5a9142', grassDk: '#3f6e30', grassHi: '#74a850', path: '#ab9f84', pathDk: '#8a7f66', sand: '#ceba86',
  win: '#9cc0d6', winDk: '#5a7e92', wall: ['#cfc6a8', '#b8c2b0', '#c6b0a4', '#bcc0cc', '#d2c2a2'],
  red: '#c0443a', blue: '#3a6bb0', yellow: '#d8a838', green: '#4a8a4a',
  rimWarm: '#fff0c0', rimCool: '#cfe6f0', ink: '#141821'
};
const FAR = 168, GROUND = 232, SPT = 276;

// ---------- static ----------
const rС = mulberry(31);
const CLOUDS = Array.from({ length: 3 }, (_, i) => ({ x0: rС() * W, y: 20 + i * 20 + (rС() * 8 | 0), spd: 0.05 + rС() * 0.05, sc: 1 + rС() * 0.7 }));
const FLOCKS = [{ y: 70, spd: 0.12, n: 5, ph: 0 }, { y: 52, spd: 0.18, n: 4, ph: 80 }];
const BFLY = Array.from({ length: 3 }, () => ({ x: 40 + (rС() * 120) | 0, y: GROUND + 16 + (rС() * 40) | 0, ph: rС(), col: [C.red, C.yellow, C.blue][(rС() * 3) | 0] }));

// ---------- sky ----------
function sky(t: number) {
  vgrad(0, 0, W, SPT, C.skyTop, C.skyHor, 10);
  // sun + rays
  const sx = 162, sy = 38; if (!reduce) for (let a = 0; a < 12; a++) { const an = a / 12 * 6.283 + t * 0.0003; A(0.12, () => R((sx + Math.cos(an) * 16) | 0, (sy + Math.sin(an) * 16) | 0, 2, 2, C.sun)); }
  glow(sx, sy, 20, C.sun); disc(sx, sy, 9, '#fff6d6'); disc(sx, sy, 6, '#fffbe8');
  for (const cl of CLOUDS) { const x = ((cl.x0 + t * cl.spd) % (W + 70)) - 35; cloud(x, cl.y, cl.sc); }
  for (const fl of FLOCKS) { const head = ((fl.ph + t * fl.spd) % (W + 60)) - 30; for (let j = 0; j < fl.n; j++) { const bx = (head - j * 10) | 0, by = (fl.y + Math.sin(t / 300 + j) * 2 + (j % 2) * 3) | 0, up = ((t / 90 | 0) + j) % 2 ? 0 : 2, c = '#3a4a58';
    R(bx - 3, by, 2, 1, c); R(bx - 1, by - up, 2, 1, c); R(bx + 1, by, 2, 1, c); } }
}
function cloud(x: number, y: number, sc: number) { for (const [dx, dy, r] of [[-13, 2, 8], [-3, -3, 11], [9, 2, 9], [18, 3, 6]]) { const rr = (r * sc) | 0; A(0.95, () => { disc(x + dx, y + dy, rr, '#eef4f6'); disc(x + dx, y + dy + 1, rr, '#d6e2e6'); }); } }

// ---------- far: treeline + low distant roofs ----------
function far(t: number) {
  for (let x = -6; x < W; x += 16) { const h = 12 + ((x * 5) % 8); R(x, FAR - h, 16, h + 6, mix('#3f6e34', '#2a4a22', 0.3)); disc(x + 8, FAR - h, 9, mix('#4f8a3e', '#2f5a26', 0.25)); }
  // faint distant roofs peeking (rest of the city is low)
  for (let x = 20; x < W; x += 46) { R(x, FAR - 6, 30, 8, mix('#9aa0a0', '#6a7070', 0.4)); R(x, FAR - 8, 30, 2, mix('#9aa0a0', '#b0b6b6', 0.3)); }
  A(0.4, () => R(0, FAR - 2, W, 4, mix(C.skyHor, '#fff', 0.2)));
}

// ---------- buildings: low pastel apartment blocks ----------
function apartment(x: number, seed: number) {
  const w = 46 + (hash(seed) * 20 | 0), floors = 3, fh = 18, h = floors * fh + 8, top = GROUND - h;
  const wall = C.wall[(hash(seed * 3) * C.wall.length) | 0], wallSh = mix(wall, '#000', 0.12), wallHi = mix(wall, '#fff', 0.15);
  R(x, top, w, h, wall); R(x, top, w, 1, wallHi); R(x, top, 1, h, wallHi); R(x + w - 2, top, 2, h, wallSh);
  for (let f = 1; f < floors; f++) R(x, GROUND - f * fh, w, 1, mix(wallSh, '#000', 0.12));                        // panel floor seams
  for (let sx2 = x + 16; sx2 < x + w - 6; sx2 += 20) R(sx2, top, 1, h, mix(wall, '#000', 0.07));                       // vertical panel seams
  R(x - 1, top - 3, w + 2, 3, mix(wall, '#000', 0.18)); R(x - 1, top - 3, w + 2, 1, wallHi);                            // parapet roof
  const cols = Math.max(3, (w - 8) / 15 | 0), gap = (w - 8) / cols, ec = (cols >> 1);                                 // entrance column
  for (let f = 0; f < floors; f++) for (let c = 0; c < cols; c++) { if (f === 0 && c === ec) continue;                    // free the ground-floor doorway slot
    const wx = (x + 5 + c * gap) | 0, wy = GROUND - (f + 1) * fh + 4;
    if (c % 2 === 0) { R(wx - 2, wy + 10, 13, 4, mix(wall, '#000', 0.07)); R(wx - 2, wy + 10, 13, 1, wallHi); for (let b = 0; b < 13; b += 2) R(wx - 2 + b, wy + 7, 1, 3, mix(wallSh, '#000', 0.15));  // balcony + railing
      if (hash(seed + f * 3 + c) > 0.55) { R(wx, wy + 6, 2, 3, C.red); R(wx + 3, wy + 6, 2, 3, C.blue); R(wx + 6, wy + 6, 2, 3, '#e8e4d8'); } }  // laundry on balcony
    R(wx - 1, wy - 1, 10, 13, wallSh); R(wx, wy, 8, 11, hash(seed * 5 + f + c) > 0.5 ? C.win : C.winDk); R(wx + 1, wy + 1, 5, 4, mix(C.win, '#fff', 0.35)); R(wx + 4, wy, 1, 11, wallSh); R(wx, wy + 5, 8, 1, wallSh);
    if (hash(seed * 2 + f * c + 1) > 0.72) R(wx, wy - 2, 8, 2, C.green); }                                          // flower box
  const edx = (x + 5 + ec * gap) | 0;                                                                         // подъезд в освобождённом слоте
  R(edx - 3, GROUND - 17, 14, 3, mix(wall, '#000', 0.28)); R(edx - 3, GROUND - 17, 14, 1, wallHi);                    // козырёк
  R(edx - 1, GROUND - 15, 10, 15, mix(wall, '#000', 0.22)); R(edx, GROUND - 14, 8, 14, mix(C.winDk, '#000', 0.25));   // дверной проём + дверь
  R(edx + 1, GROUND - 13, 6, 6, mix(C.win, '#000', 0.1)); R(edx + 5, GROUND - 8, 1, 2, C.yellow); R(edx - 2, GROUND - 1, 12, 1, C.pathDk);  // фрамуга + ручка + ступень
}

// ---------- yard ----------
function yard(t: number) {
  // grass + path
  vgrad(0, GROUND, W, SPT - GROUND + 6, C.grass, C.grassDk, 4);
  const rp = mulberry(77); for (let i = 0; i < 90; i++) { const x = (rp() * W) | 0, y = GROUND + 2 + (rp() * (SPT - GROUND)) | 0; R(x, y - 2, 1, 2, rp() < 0.5 ? C.grassHi : C.grassDk); }  // grass blades
  R(0, GROUND + 22, W, 10, C.path); R(0, GROUND + 22, W, 1, mix(C.path, '#fff', 0.2)); R(0, GROUND + 31, W, 1, C.pathDk);  // path across
  for (let x = 6; x < W; x += 12) R(x, GROUND + 22, 1, 10, mix(C.path, '#000', 0.1));                                    // path seams
  // props
  tree(26, GROUND + 6); tree(176, GROUND + 6); bush(150, GROUND + 18); bush(54, GROUND + 20);
  carpetBeater(96, GROUND + 18); gribok(70, GROUND + 34);
  bench(126, GROUND + 34); flowerbed(40, GROUND + 34); flowerbed(160, GROUND + 36);
  laundry(108, GROUND - 2, 150, GROUND + 2);
  for (const b of BFLY) { if (reduce) break; const bx = b.x + Math.sin(t / 400 + b.ph * 6) * 8, by = b.y + Math.sin(t / 250 + b.ph * 9) * 5, w = (t / 120 | 0) % 2 ? 1 : 2;
    A(0.9, () => { R(bx - w, by, w, 1, b.col); R(bx + 1, by, w, 1, b.col); R(bx, by, 1, 1, '#2a2420'); }); }
}
function tree(x: number, y: number) {
  R(x - 2, y - 20, 4, 20, '#6a4a2a'); R(x - 2, y - 20, 1, 20, '#8a6a44');
  disc(x, y - 30, 11, mix(C.grass, '#000', 0.08)); disc(x - 5, y - 26, 8, mix(C.grass, '#000', 0.18)); disc(x + 5, y - 33, 7, mix(C.grass, C.grassHi, 0.4)); disc(x + 1, y - 36, 5, mix(C.grass, '#fff', 0.12)); A(0.3, () => disc(x + 4, y - 38, 3, '#bfe08a'));
}
function bush(x: number, y: number) { disc(x, y - 4, 6, mix(C.grass, '#000', 0.1)); disc(x - 4, y - 2, 4, mix(C.grass, '#000', 0.2)); disc(x + 4, y - 5, 4, mix(C.grass, C.grassHi, 0.3)); }
function bench(x: number, y: number) { R(x - 11, y - 4, 22, 2, '#4a8a4a'); R(x - 11, y - 8, 22, 2, mix('#4a8a4a', '#000', 0.2)); R(x - 11, y - 7, 22, 1, mix('#4a8a4a', '#fff', 0.2)); R(x - 10, y - 2, 2, 6, '#3a4048'); R(x + 8, y - 2, 2, 6, '#3a4048'); }
function carpetBeater(x: number, y: number) {
  R(x - 11, y - 16, 2, 16, '#8a8f98'); R(x + 9, y - 16, 2, 16, '#8a8f98'); R(x - 11, y - 16, 2, 16, '#9aa0a8'); R(x - 11, y - 16, 22, 2, '#9aa0a8'); R(x - 11, y - 10, 22, 1, '#7a8088');
  R(x - 8, y - 13, 16, 9, C.red); R(x - 8, y - 13, 16, 1, mix(C.red, '#fff', 0.2)); for (let i = 0; i < 16; i += 3) R(x - 8 + i, y - 12, 1, 7, '#8a2a22'); R(x - 7, y - 11, 4, 2, C.yellow); R(x + 1, y - 9, 4, 2, C.yellow);
}  // carpet
function gribok(x: number, y: number) {
  R(x - 8, y - 2, 16, 3, '#c6ac6a'); R(x - 8, y - 2, 16, 1, mix('#c6ac6a', '#fff', 0.2)); R(x - 8, y + 1, 16, 1, '#8a6a3a');  // sandbox
  R(x - 1, y - 15, 2, 13, '#8a8f98'); disc(x, y - 18, 8, C.red); R(x - 8, y - 18, 16, 1, mix(C.red, '#000', 0.2)); R(x - 7, y - 20, 14, 2, '#e4ddd0'); for (const [dx, dy] of [[-3, -1], [2, -2], [0, 1]]) R(x + dx, y - 19 + dy, 2, 2, '#f0ece0');
}  // mushroom
function flowerbed(x: number, y: number) { R(x - 7, y - 2, 14, 3, mix(C.pathDk, '#000', 0.1)); R(x - 6, y - 3, 12, 1, mix(C.grass, '#000', 0.1)); for (let i = 0; i < 6; i++) { const fx = x - 5 + i * 2, c = [C.red, C.yellow, '#d85a9a', C.blue][i % 4]; R(fx, y - 5, 1, 2, '#3a6b2a'); R(fx - 1, y - 6, 2, 2, c); } }
function laundry(x1: number, y1: number, x2: number, y2: number) {
  for (let x = x1; x <= x2; x++) { const y = lerp(y1, y2, (x - x1) / (x2 - x1)) + Math.sin((x - x1) / (x2 - x1) * Math.PI) * 2; R(x, y | 0, 1, 1, '#6a6a60'); }
  const items: [number, string][] = [[x1 + 10, C.red], [x1 + 18, '#e8e4d8'], [x1 + 26, C.blue], [x1 + 34, C.yellow]]; for (const [ix, col] of items) { const iy = lerp(y1, y2, (ix - x1) / (x2 - x1)) + Math.sin((ix - x1) / (x2 - x1) * Math.PI) * 2; R(ix - 2, iy + 1, 4, 6, col); R(ix - 2, iy + 1, 4, 1, mix(col, '#fff', 0.3)); }
}

// ---------- спортплощадка (foreground) ----------
function sport(t: number) {
  R(0, SPT, W, H - SPT, C.sand); R(0, SPT, W, 1, mix(C.sand, '#000', 0.2)); vgrad(0, SPT, W, H - SPT, mix(C.sand, '#fff', 0.03), mix(C.sand, '#000', 0.22), 4);
  const rp = mulberry(55); for (let i = 0; i < 60; i++) { const x = (rp() * W) | 0, y = SPT + 4 + (rp() * (H - SPT - 6)) | 0; R(x, y, 1, 1, rp() < 0.5 ? mix(C.sand, '#fff', 0.08) : mix(C.sand, '#000', 0.18)); }
  A(0.07, () => disc(100, 300, 40, C.sun));                                                              // soft sunny patch
  // инвентарь: турник, брусья, кольца, шведская стенка
  wallBars(24, SPT + 6); rings(176, SPT + 2, t); parallelBars(52, H - 18); turnik(150, SPT + 8);
  R(70, H - 20, 60, 7, mix(C.blue, '#000', 0.15)); R(70, H - 20, 60, 2, mix(C.blue, '#fff', 0.18));                 // mat
  heroFox(72, H - 10, t); mentor(134, H - 12, AV_LION, t);
  questBang(134, 266, t);
  A(0.35, () => { disc(-10, -10, 38, '#000'); disc(W + 10, -10, 38, '#000'); disc(-10, H + 10, 42, '#000'); disc(W + 10, H + 10, 42, '#000'); });
}
function rrect(x: number, y: number, w: number, h: number, col: string) { R(x + 1, y, w - 2, 1, col); R(x + 1, y + h, w - 2, 1, col); R(x, y + 1, 1, h - 2, col); R(x + w, y + 1, 1, h - 2, col); }
function turnik(x: number, y: number) {
  R(x - 20, y, 3, 44, C.red); R(x + 18, y, 3, 44, C.red); R(x - 20, y, 1, 44, mix(C.red, '#fff', 0.25)); R(x - 22, y, 43, 3, '#9aa0a8'); R(x - 22, y, 43, 1, '#c4ccd4');  // high bar
  R(x - 12, y + 14, 3, 30, C.blue); R(x - 12, y + 14, 15, 3, '#9aa0a8');
}                                          // low bar
function parallelBars(x: number, y: number) { for (const s of [-1, 1]) { R(x + s * 9 - 1, y, 2, 20, C.yellow); R(x + s * 9 - 8, y - 2, 16, 3, '#9aa0a8'); R(x + s * 9 - 8, y - 2, 16, 1, '#c4ccd4'); } }
function rings(x: number, y: number, t: number) {
  R(x - 12, y, 24, 3, C.red); R(x - 12, y, 24, 1, mix(C.red, '#fff', 0.2)); const sw = reduce ? 0 : Math.round(Math.sin(t / 500) * 2);
  for (const s of [-1, 1]) { R(x + s * 7 - 1 + sw, y + 3, 1, 16, '#6a5a3a'); disc(x + s * 7 + sw, y + 21, 3, '#d8b34a'); R(x + s * 7 - 1 + sw, y + 20, 3, 2, '#2a241a'); }
}
function wallBars(x: number, y: number) { R(x - 7, y, 3, 52, C.green); R(x + 6, y, 3, 52, C.green); R(x - 7, y, 1, 52, mix(C.green, '#fff', 0.2)); for (let r = 0; r < 8; r++) R(x - 6, y + 4 + r * 6, 13, 2, '#d8a838'); }  // шведская стенка
function heroFox(x: number, y: number, t: number) {
  const bob = reduce ? 0 : (Math.sin(t / 430) > 0 ? 0 : 1); y -= bob; const sh = '#d84a3a', shSh = '#a8362a', pant = '#3a4656', sc = 0.8;
  A(0.4, () => R(x - 8, y, 16, 1, '#2a2a22')); R(x - 6, y - 6, 5, 6, pant); R(x + 1, y - 6, 5, 6, pant); R(x - 6, y, 5, 2, '#20242b'); R(x + 1, y, 5, 2, '#20242b');
  R(x - 7, y - 16, 14, 10, sh); R(x - 7, y - 16, 3, 10, shSh); R(x + 5, y - 16, 2, 10, mix(sh, '#fff', 0.12)); R(x - 7, y - 16, 14, 2, mix(sh, '#fff', 0.14)); R(x - 2, y - 16, 4, 2, '#efe6cf');  // t-shirt + collar
  A(0.3, () => R(x + 6, y - 16, 1, 10, C.rimWarm)); avatar(AV_FOX, x, y - 13 - Math.round(32 * sc), sc);
}
function mentor(x: number, y: number, av: Rect[], t: number) {
  const br = reduce ? 0 : (Math.sin(t / 1000) > 0 ? 0 : 1); y -= br; const trk = '#2f5aa0', trkSh = '#214078', trkHi = '#4a76bc', sc = 0.95;  // coach tracksuit
  A(0.45, () => R(x - 13, y, 26, 1, '#2a2a22')); R(x - 9, y - 8, 7, 8, trk); R(x + 2, y - 8, 7, 8, trk); R(x - 9, y - 8, 2, 8, '#e8e4d8'); R(x + 2, y - 8, 2, 8, '#e8e4d8'); R(x - 9, y, 7, 2, '#e8e4d8'); R(x + 2, y, 7, 2, '#e8e4d8');  // track pants + white stripes/sneakers
  R(x - 12, y - 20, 24, 14, trk); R(x - 12, y - 20, 3, 14, trkSh); R(x + 9, y - 20, 3, 14, trkHi); R(x - 12, y - 20, 24, 2, mix(trk, '#fff', 0.14));
  R(x - 12, y - 18, 2, 12, '#e8e4d8'); R(x + 10, y - 18, 2, 12, '#e8e4d8');                                        // sporty side stripes
  R(x - 16, y - 19, 5, 14, trk); R(x + 11, y - 19, 5, 14, trk); R(x - 16, y - 19, 5, 2, trkHi); R(x + 11, y - 19, 5, 2, trkHi);
  R(x - 2, y - 12, 3, 6, '#e8e4d8'); R(x - 1, y - 6, 2, 4, '#c0443a');                                             // towel + whistle
  A(0.4, () => { R(x + 15, y - 19, 1, 14, C.rimWarm); R(x - 16, y - 19, 1, 14, C.rimCool); }); avatar(av, x, y - 17 - Math.round(32 * sc), sc);
}
function questBang(x: number, y: number, t: number) {
  const b = reduce ? 0 : Math.round(Math.sin(t / 300) * 2); y += b; glow(x, y + 7, 9, '#e8bf48'); R(x - 8, y, 16, 15, '#e8bf48'); R(x - 8, y, 16, 2, mix('#e8bf48', '#fff', 0.4)); rrect(x - 8, y, 16, 15, C.ink);
  R(x - 1, y + 3, 3, 6, C.ink); R(x - 1, y + 10, 3, 2, C.ink); for (let i = 0; i < 5; i++) R(x - 4 + i, y + 15 + i, Math.max(1, 8 - 2 * i), 1, '#e8bf48');
}

function draw(t: number) { R(0, 0, W, H, C.ink); sky(t); far(t); let bx = -10; let i = 0; while (bx < W) { apartment(bx, i * 7 + 1); bx += 46 + ((i * 13) % 20) + 8; i++; } R(0, GROUND, W, 1, mix(C.grassDk, '#000', 0.2)); yard(t); sport(t); }

export function drawYard(context: CanvasRenderingContext2D, t: number) {
  ctx = context;
  draw(t);
}
