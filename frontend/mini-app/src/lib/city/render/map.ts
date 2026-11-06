// City map render module, ported verbatim from branding/stories/city_map.html.
// Node positions/state come from the `nodes` param; every draw function body is verbatim.

import { AV_FOX } from "./sprites";

export type MapNode = {
  id: string;
  x: number;
  y: number;
  state: "open" | "lock";
  vign: "home" | "french" | "cossack" | "downtown" | "port";
};

// Module ctx that all helper functions close over (set by drawCityMap first).
let ctx: CanvasRenderingContext2D;

// Per-draw state derived from params.
let W: number, H: number;
let reduce: boolean;
let D: MapNode[];
let sel: string;
let player: string;

// ---------- helpers ----------
const R = (x: number, y: number, w: number, h: number, col: string) => { ctx.fillStyle = col; ctx.fillRect(x | 0, y | 0, Math.max(1, w | 0), Math.max(1, h | 0)); };
const Rx = (c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, col: string) => { c.fillStyle = col; c.fillRect(x | 0, y | 0, Math.max(1, w | 0), Math.max(1, h | 0)); };
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
function glow(cx: number, cy: number, r: number, col: string) { discA(cx, cy, r, col, 0.07); discA(cx, cy, (r * 0.6) | 0, col, 0.1); }
function drawAvatarCtx(c: CanvasRenderingContext2D, av: readonly (readonly [number, number, number, number, string])[], ox: number, oy: number, sc: number) { for (const r of av) { Rx(c, ox + Math.round(r[0] * sc), oy + Math.round(r[1] * sc), Math.max(1, Math.round(r[2] * sc)), Math.max(1, Math.round(r[3] * sc)), r[4]); } }

const byId = (id: string) => D.find(d => d.id === id)!;

// ---------- map background ----------
const rG = mulberry(11); const GTREES = Array.from({ length: 26 }, () => ({ x: (rG() * 200) | 0, y: 40 + (rG() * (300 - 50)) | 0, r: 2 + (rG() * 2 | 0) }));
const RIVER: [number, number][] = [[-6, 120], [40, 118], [78, 96], [110, 110], [150, 96], [190, 70], [210, 58]];     // winding river pts
const ROADS: [string, string][] = [['home', 'french'], ['home', 'cossack'], ['french', 'downtown'], ['cossack', 'downtown'], ['downtown', 'port']];
function drawMap(t: number) {
  // dusk ground
  for (let y = 0; y < H; y++) R(0, y, W, 1, mix('#223a34', '#15241f', y / H));
  // soft ground mottle
  const rm = mulberry(3); for (let i = 0; i < 220; i++) { const x = (rm() * W) | 0, y = (rm() * H) | 0; R(x, y, 1, 1, rm() < 0.5 ? mix('#223a34', '#2c463e', 0.6) : mix('#223a34', '#12201b', 0.6)); }
  // river
  for (let i = 0; i < RIVER.length - 1; i++) {
    const [x1, y1] = RIVER[i], [x2, y2] = RIVER[i + 1], st = Math.max(Math.abs(x2 - x1), Math.abs(y2 - y1));
    for (let s = 0; s <= st; s++) { const x = lerp(x1, x2, s / st) | 0, y = lerp(y1, y2, s / st) | 0; R(x - 5, y - 2, 11, 5, '#1d3b46'); R(x - 5, y - 2, 11, 1, '#2f5c6a'); }
  }
  if (!reduce) for (let i = 0; i < 10; i++) {
    const u = (i / 10 + (t * 0.00003)) % 1, seg = u * (RIVER.length - 1), k = seg | 0, f = seg - k; if (k >= RIVER.length - 1) continue;
    const x = lerp(RIVER[k][0], RIVER[k + 1][0], f) | 0, y = lerp(RIVER[k][1], RIVER[k + 1][1], f) | 0; A(0.5, () => R(x - 2, y - 1, 2, 1, '#4f8a98'));
  }
  // trees scattered
  for (const g of GTREES) { R(g.x - 1, g.y, 2, 3, '#3a2c1c'); disc(g.x, g.y - 2, g.r, mix('#2f5e42', '#17301f', 0.3)); }
  // roads between districts
  for (const [a, b] of ROADS) {
    const A1 = byId(a), B1 = byId(b), locked = (A1.state === 'lock' || B1.state === 'lock');
    road(A1.x, A1.y, B1.x, B1.y, locked);
  }
  // district vignettes
  for (const d of D) { vignette(d, t); }
  // player token (fox) at current node
  const p = byId(player); A(0.5, () => disc(p.x, p.y + 10, 4, '#07080c'));
  drawAvatarCtx(ctx, AV_FOX, p.x - 8, p.y - 6 + (reduce ? 0 : (Math.sin(t / 430) > 0 ? 0 : -1)), 0.5);
}
function road(x1: number, y1: number, x2: number, y2: number, locked: boolean) {
  const mx = (x1 + x2) / 2 + (y2 - y1) * 0.12, my = (y1 + y2) / 2 + (x1 - x2) * 0.12;  // slight curve via control
  const col = locked ? '#2b2f36' : '#6a5f44', hi = locked ? '#333845' : '#8a7d58';
  let px = x1, py = y1; for (let s = 1; s <= 16; s++) {
    const u = s / 16, x = lerp(lerp(x1, mx, u), lerp(mx, x2, u), u) | 0, y = lerp(lerp(y1, my, u), lerp(my, y2, u), u) | 0;
    const st = Math.max(Math.abs(x - px), Math.abs(y - py)); for (let k = 0; k <= st; k++) { const xx = lerp(px, x, k / st) | 0, yy = lerp(py, y, k / st) | 0; R(xx - 2, yy - 1, 4, 2, col); R(xx - 1, yy - 1, 2, 1, hi); } px = x; py = y;
  }
}
// ---------- district vignettes ----------
function vignette(d: MapNode, t: number) {
  const cx = d.x, cy = d.y, lk = d.state === 'lock';
  A(0.5, () => disc(cx, cy + 11, 14, '#0a0f0e'));                            // base shadow
  disc(cx, cy + 10, 13, lk ? '#1c2420' : mix('#3b5a40', '#263d2b', 0.3));        // grass platform
  if (d.vign === 'home') vHome(cx, cy, t); else if (d.vign === 'french') vFrench(cx, cy, t);
  else if (d.vign === 'cossack') vCossack(cx, cy, t); else if (d.vign === 'downtown') vDowntown(cx, cy);
  else if (d.vign === 'port') vPort(cx, cy);
  if (lk) {
    A(0.55, () => { for (let yy = -24; yy < 13; yy++) for (let xx = -15; xx < 16; xx++) if (((xx + yy) & 1) === 0) R(cx + xx, cy + yy, 1, 1, '#0c1013'); });  // locked veil
    padlock(cx, cy - 6);
  }
  if (d.id === sel) { ring(cx, cy, d.state === 'lock'); }                   // selection ring
  if (d.state === 'open' && !reduce) { glow(cx, cy - 6, 16 + Math.sin(t / 500 + cx) * 1.5, '#e8bf48'); } // gentle beacon
}
function warmWin(x: number, y: number, w: number, h: number, on: boolean) { R(x, y, w, h, on ? '#ffbe5a' : '#2a3550'); }
function vHome(cx: number, cy: number, t: number) {                                              // bright courtyard: 2 small houses + tree + pull-up bar
  disc(cx - 2, cy + 4, 15, mix('#3f6a46', '#2a4a30', 0.3));                    // sunlit lawn
  // house 1
  R(cx - 15, cy - 8, 12, 12, '#c7b48c'); R(cx - 15, cy - 8, 12, 1, '#ddd0a8'); R(cx - 16, cy - 9, 14, 4, '#8a5a3a'); R(cx - 9, cy - 14, 2, 6, '#5a3a28');
  warmWin(cx - 12, cy - 4, 3, 4, true); warmWin(cx - 7, cy - 4, 3, 4, false);
  // house 2
  R(cx + 2, cy - 6, 11, 10, '#bfa27a'); R(cx + 2, cy - 6, 11, 1, '#d6c096'); R(cx + 1, cy - 7, 13, 4, '#7a4a30'); warmWin(cx + 5, cy - 3, 3, 4, true);
  // tree
  R(cx + 14, cy - 2, 1, 6, '#4a3826'); disc(cx + 14, cy - 5, 4, mix('#3f7a4c', '#2a4a30', 0.2));
  // pull-up bar (inventory playground)
  R(cx - 3, cy + 1, 1, 7, '#4a4f58'); R(cx + 4, cy + 1, 1, 7, '#4a4f58'); R(cx - 3, cy + 1, 8, 1, '#6a7079');
}
function vFrench(cx: number, cy: number, t: number) {                                            // Haussmann row + tiny Eiffel
  for (let i = 0; i < 3; i++) {
    const bx = cx - 14 + i * 10, h = 14 + (i === 1 ? 4 : 0);
    R(bx, cy - 8 - ((h - 14)) | 0, 9, h, mix('#c2b89a', '#b0a686', i / 3)); R(bx, cy - 8 - ((h - 14)) | 0, 9, 1, '#d8cda8');
    R(bx - 1, cy - 10 - ((h - 14)) | 0, 11, 3, '#454b56');                         // mansard
    for (let f = 0; f < 3; f++) for (let c = 0; c < 2; c++) warmWin(bx + 1 + c * 5, cy - 6 + f * 5, 3, 3, hash(i * 3 + f + c) > 0.5);
  }
  // Eiffel behind
  const ex = cx + 15; for (let i = 0; i < 16; i += 3) { const hh = Math.round(5 - 4 * i / 16); R(ex - hh, cy - 10 - i, 2, 1, '#2f3442'); R(ex + hh - 1, cy - 10 - i, 2, 1, '#2f3442'); } R(ex - 1, cy - 26, 2, 16, '#2f3442');
}
function vCossack(cx: number, cy: number, t: number) {                                           // wooden izba + onion-dome church
  // izba
  R(cx - 15, cy - 5, 13, 9, '#7a5330'); for (let ly = cy - 5; ly < cy + 4; ly += 2) R(cx - 15, ly, 13, 1, mix('#7a5330', '#000', 0.2)); // logs
  R(cx - 16, cy - 8, 15, 4, '#8a5a3a'); R(cx - 16, cy - 8, 15, 1, '#9c6a44'); warmWin(cx - 11, cy - 3, 4, 4, true); R(cx - 11, cy - 3, 4, 1, '#caa'); R(cx - 11, cy - 3, 1, 4, '#caa');
  // church tower + onion dome
  const chx = cx + 7; R(chx - 3, cy - 14, 7, 18, '#cfc6b2'); R(chx - 3, cy - 14, 7, 1, '#e4dcc8'); warmWin(chx - 1, cy - 4, 3, 5, true);
  disc(chx, cy - 17, 4, '#3f7a5a'); R(chx, cy - 24, 1, 4, '#e8bf48'); R(chx - 1, cy - 21, 3, 1, '#e8bf48');  // green onion dome + gold cross
  disc(chx, cy - 17, 4, '#3f7a5a');
}
function vDowntown(cx: number, cy: number) {                                            // glass skyscrapers
  for (let i = 0; i < 3; i++) {
    const bx = cx - 13 + i * 9, h = 18 + ((i * 7) % 11); R(bx, cy - 8 - (h - 14), 8, h + 6, mix('#2a3240', '#1a2130', i / 3)); R(bx, cy - 8 - (h - 14), 8, 1, '#3a4454');
    for (let wy = cy - 6 - (h - 14); wy < cy + 2; wy += 3) for (let wx = bx + 1; wx < bx + 7; wx += 2) R(wx, wy, 1, 2, hash(bx + wy) > 0.6 ? '#8fb8d0' : '#1f2838');
  }
  R(cx + 8, cy - 30, 1, 8, '#3a4454');
}
function vPort(cx: number, cy: number) {                                                // crane + containers
  for (let i = 0; i < 4; i++) R(cx - 12 + i * 6, cy - 1, 6, 5, ['#7e322f', '#2f567f', '#3a6b4a', '#6b4a2a'][i]);   // containers
  R(cx - 6, cy - 1, 12, 1, '#3a4048');
  R(cx + 6, cy - 18, 2, 18, '#8a6a3a'); R(cx - 2, cy - 18, 12, 2, '#8a6a3a'); R(cx - 2, cy - 18, 2, 6, '#6a4f2a');   // crane
}
function padlock(cx: number, cy: number) { R(cx - 4, cy - 1, 8, 7, '#b7bcc6'); R(cx - 4, cy - 1, 8, 1, '#d6dae2'); R(cx - 3, cy - 5, 6, 4, '#8b909a'); R(cx - 2, cy - 5, 4, 3, mix('#1c2026', '#000', 0.1)); R(cx - 1, cy + 1, 2, 3, '#3a3f48'); }
function ring(cx: number, cy: number, locked: boolean) { const col = locked ? '#cf9b7f' : '#e8bf48'; for (let a = 0; a < 28; a++) { const an = a / 28 * 6.283, x = cx + Math.cos(an) * 17 | 0, y = cy + 2 + Math.sin(an) * 10 | 0; if (a % 2 === 0) R(x, y, 1, 1, col); } }

// ---------- entry ----------
export function drawCityMap(c: CanvasRenderingContext2D, t: number, nodes: MapNode[], playerId: string) {
  ctx = c;
  W = c.canvas.width; H = c.canvas.height;
  reduce = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  D = nodes;
  player = playerId;
  sel = playerId;
  drawMap(t);
}
