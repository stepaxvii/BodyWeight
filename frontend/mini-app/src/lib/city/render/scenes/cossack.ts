// Казачья слобода · вечер — detailed canvas scene, ported verbatim from
// branding/stories/district_cossack.html per FIDELITY RULES.
// Avatar sprite arrays imported from the shared sprites module.

import { AV_FOX, AV_MINO, type Rect } from '../sprites';

let ctx: CanvasRenderingContext2D;

export function drawCossack(context: CanvasRenderingContext2D, t: number): void {
  ctx = context;
  const cv = ctx.canvas;
  const W = cv.width, H = cv.height; ctx.imageSmoothingEnabled = false;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

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
  function glow(cx: number, cy: number, r: number, col: string) { discA(cx, cy, r, col, 0.07); discA(cx, cy, (r * 0.6) | 0, col, 0.1); discA(cx, cy, (r * 0.33) | 0, col, 0.13); }
  function vgrad(x: number, y: number, w: number, h: number, c0: string, c1: string, bands: number) {
    const bh = h / bands; for (let i = 0; i < bands; i++) R(x, y + Math.floor(i * bh), w, Math.ceil(bh) + 1, mix(c0, c1, i / (bands - 1)));
    for (let i = 1; i < bands; i++) { const yy = y + Math.round(i * bh), ca = mix(c0, c1, (i - 1) / (bands - 1)); for (let xx = x + ((yy & 1) ? 0 : 1); xx < x + w; xx += 2) R(xx, yy, 1, 1, ca); }
  }
  function haze(x: number, y: number, w: number, h: number, col: string, topA: number) { for (let yy = 0; yy < h; yy++) { const a = topA * (1 - yy / h); for (let xx = 0; xx < w; xx++) if (((xx + (yy & 1)) & 1) === 0 && hash((x + xx) * 2.1 + (y + yy) * 3.7) < a) R(x + xx, y + yy, 1, 1, col); } }
  function avatar(av: Rect[], cx: number, topY: number, sc: number) { for (const r of av) R(Math.round(cx - 16 * sc + r[0] * sc), Math.round(topY + r[1] * sc), Math.max(1, Math.round(r[2] * sc)), Math.max(1, Math.round(r[3] * sc)), r[4]); }

  // ---------- palette ----------
  const C = {
    skyTop: '#1b2238', skyHor: '#b07a52', haze: '#4a4458',
    wood: ['#7a5330', '#89602f', '#6b4a2a'], woodDk: '#4a3320', woodHi: '#9c7446',
    roof: '#4a3828', roofDk: '#362718', wall: '#d2c6a8', wallSh: '#a99a78',
    win: '#ffcf7a', winCold: '#2a3a50', trim: '#5a7f93', dome: '#3f7a5a', domeGold: '#c89a3a', gold: '#e8bf48',
    dirt: '#4a3b2a', dirtDk: '#2e2418', grass: '#3f6a3a', rimCool: '#9ec2d8', rimWarm: '#ffd49a', fire: '#ff7a2a'
  };
  const FAR = 172, GROUND = 232, SPT = 276;

  // ---------- static ----------
  const rS = mulberry(23); const STARS = Array.from({ length: 52 }, () => ({ x: (rS() * W) | 0, y: (rS() * 150) | 0, b: rS() }));
  const FIRE = Array.from({ length: 7 }, (_, i) => ({ x: 40 + (rS() * 130) | 0, y: GROUND + 10 + (rS() * 54) | 0, ph: rS() }));   // fireflies
  const IZBAS = [{ x: -8, s: 1.3 }, { x: 30, s: 2.7 }, { x: 66, s: 4.1 }, { x: 160, s: 5.5 }];                                  // + church at 110
  const CHIM: Array<[number, number]> = [];

  // ---------- LAYER 1 · sky ----------
  function sky(t: number) {
    vgrad(0, 0, W, SPT, C.skyTop, C.skyHor, 12);
    for (const s of STARS) { if (s.y > FAR - 20) continue; const on = reduce ? s.b > .3 : (Math.sin(t / 800 + s.x) > -.2); if (on) R(s.x, s.y, 1, 1, mix('#2a3350', '#d6def0', s.b)); }
    const mx = 150, my = 40; glow(mx, my, 20, mix(C.skyTop, '#ffe9c0', 0.85)); disc(mx, my, 8, '#f2e6c6'); R(mx - 8, my - 8, 16, 1, '#fff4d8'); A(0.5, () => disc(mx - 3, my - 2, 5, mix('#f2e6c6', '#000', 0.1)));
  }
  // ---------- LAYER 2 · far landscape ----------
  function far(t: number) {
    // rolling hills
    for (let i = 0; i < 3; i++) A(1, () => disc(30 + i * 78, FAR + 8 + i * 4, 52, mix('#33543a', '#1f3a22', 0.25 + i * 0.2)));
    // fir treeline on the hills
    for (let x = 4; x < W; x += 9) { const h = 10 + ((x * 7) % 7), by = FAR - 2 - ((x * 3) % 5); fir(x, by, h, mix('#24402a', '#162a18', 0.3)); }
    windmill(176, FAR - 4);
    // distant onion-dome silhouette on the left hill
    const dsx = 24; R(dsx - 2, FAR - 14, 4, 14, mix('#2a3340', '#1a2230', 0.4)); disc(dsx, FAR - 16, 3, mix('#2a3340', '#1a2230', 0.4)); R(dsx - 1, FAR - 22, 2, 6, mix('#2a3340', '#1a2230', 0.4));
    haze(0, FAR - 14, W, 18, C.haze, 0.5);
  }
  function fir(x: number, baseY: number, h: number, col: string) { R(x - 1, baseY, 2, 3, C.woodDk); for (let i = 0; i < h; i += 2) { const half = ((h - i) / h * 3 + 0.5) | 0; R(x - half, baseY - 3 - i, half * 2 + 1, 2, col); } }
  function windmill(x: number, baseY: number) {
    const col = mix('#3a3026', '#1d1812', 0.3);
    R(x - 5, baseY - 20, 10, 20, col); R(x - 5, baseY - 20, 10, 1, mix(col, '#fff', 0.15)); R(x - 6, baseY - 24, 12, 5, C.roofDk);   // tower + cap
    const cx = x, cy = baseY - 22; for (const [dx, dy] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) for (let i = 1; i <= 9; i++) R(cx + dx * i, cy + dy * i, 1, 1, col);  // sails (X)
    // warm window
    R(x - 2, baseY - 10, 4, 4, mix(C.win, '#000', 0.3));
  }

  // ---------- LAYER 3 · слобода (izbas + church) ----------
  function izba(x: number, seed: number) {
    const w = 34 + (hash(seed) * 14 | 0), wh = 28 + (hash(seed * 2) * 8 | 0), top = GROUND - wh;
    const wood = C.wood[(hash(seed * 3) * 3) | 0], woodSh = mix(wood, '#000', 0.26);
    R(x, top, w, wh, wood); for (let ly = top + 2; ly < GROUND; ly += 3) R(x, ly, w, 1, mix(wood, '#000', 0.2));      // log courses
    R(x, top, 2, wh, woodSh); R(x + w - 2, top, 2, wh, woodSh); R(x, top, w, 1, mix(wood, '#fff', 0.12));           // corner venets
    // gable roof
    const rh = 15; for (let i = 0; i < rh; i++) { const half = ((w / 2 + 2) * (1 - i / rh)) | 0; R(x + w / 2 - half, top - i, half * 2, 1, mix(C.roof, '#000', (i / rh) * 0.25)); }
    R(x - 2, top - 1, w + 4, 2, C.roofDk); R(x + w / 2 - 1, top - rh - 3, 2, 4, C.woodDk);                                // eave board + конёк
    // window with carved наличник + shutters
    for (let c = 0; c < (w > 44 ? 2 : 1); c++) {
      const wx = x + 8 + c * 18, wy = top + 9, warm = hash(seed * 5 + c) > 0.35;
      R(wx - 3, wy - 4, 14, 17, mix(wood, '#fff', 0.16)); R(wx - 3, wy - 6, 14, 3, C.trim);                          // frame + carved valance
      R(wx - 5, wy - 1, 2, 13, C.trim); R(wx + 10, wy - 1, 2, 13, C.trim);                                         // ставни shutters
      R(wx, wy, 8, 11, warm ? C.win : C.winCold); if (warm) R(wx + 1, wy + 1, 6, 4, mix(C.win, '#fff', 0.3));
      R(wx + 4, wy, 1, 11, woodSh); R(wx, wy + 5, 8, 1, woodSh);
    }
    const chx = x + w - 9; R(chx, top - rh - 7, 4, 9, '#8a5a3a'); R(chx, top - rh - 8, 4, 1, '#9c6a44'); CHIM.push([chx + 2, top - rh - 8]);
    R(x + 3, GROUND - 5, w - 6, 1, mix(wood, '#000', 0.3));
  }
  function church(x: number) {
    const w = 28, wh = 40, top = GROUND - wh;
    R(x, top, w, wh, C.wall); R(x, top, w, 1, mix(C.wall, '#fff', 0.12)); R(x + w - 2, top, 2, wh, C.wallSh);
    R(x, GROUND - 5, w, 5, '#a9824e');                                                                   // ochre plinth
    for (let c = 0; c < 2; c++) { const wx = x + 7 + c * 11, wy = top + 14; R(wx, wy - 2, 5, 2, C.wallSh); R(wx, wy, 5, 11, '#b0a080'); R(wx + 1, wy + 1, 3, 9, mix(C.win, '#000', 0.1)); }
    // drum + green onion dome + cross
    const dx = x + w / 2 | 0; R(dx - 5, top - 7, 10, 8, '#c8b890'); R(dx - 5, top - 7, 10, 1, mix('#c8b890', '#fff', 0.15));
    disc(dx, top - 12, 6, C.dome); R(dx - 3, top - 18, 6, 5, C.dome); R(dx - 2, top - 22, 4, 5, C.dome); R(dx - 1, top - 25, 2, 4, C.dome);  // onion taper
    A(0.4, () => disc(dx - 2, top - 13, 3, mix(C.dome, '#fff', 0.3)));
    R(dx - 1, top - 33, 2, 9, C.gold); R(dx - 4, top - 31, 8, 1, C.gold); R(dx - 3, top - 29, 6, 1, C.gold); R(dx - 3, top - 27, 6, 1, C.gold); // 3-bar cross
    // bell tower (left)
    const bx = x - 13, bw = 12, bh = wh + 16, bt = GROUND - bh; R(bx, bt, bw, bh, C.wall); R(bx, bt, bw, 1, mix(C.wall, '#fff', 0.12)); R(bx + bw - 2, bt, 2, bh, C.wallSh);
    R(bx + 2, bt + 7, 8, 9, '#241c12'); R(bx + 4, bt + 8, 4, 7, '#4a4030'); R(bx + 3, bt + 6, 6, 1, C.wallSh);              // belfry arch + bell
    const bdx = bx + bw / 2 | 0; R(bdx - 4, bt - 6, 8, 6, '#c8b890'); disc(bdx, bt - 10, 4, C.domeGold); R(bdx - 2, bt - 14, 4, 4, C.domeGold); R(bdx - 1, bt - 17, 2, 3, C.domeGold);
    R(bdx - 1, bt - 24, 2, 7, C.gold); R(bdx - 3, bt - 22, 6, 1, C.gold); R(bdx - 2, bt - 20, 4, 1, C.gold);
  }

  // ---------- LAYER 4 · двор ----------
  function yard(t: number) {
    vgrad(0, GROUND, W, SPT - GROUND + 6, mix(C.dirt, '#000', 0.05), C.dirtDk, 4);                          // dirt road
    const rp = mulberry(91); for (let i = 0; i < 120; i++) { const x = (rp() * W) | 0, y = GROUND + 2 + (rp() * (SPT - GROUND)) | 0; R(x, y, 2, 1, rp() < 0.5 ? mix(C.dirt, '#fff', 0.05) : mix(C.dirt, '#000', 0.3)); }
    for (const rut of [GROUND + 10, GROUND + 20]) A(0.3, () => R(0, rut, W, 1, C.dirtDk));                        // wheel ruts
    haze(0, GROUND - 5, W, 8, C.haze, 0.35);
    fence(0, 52, GROUND + 8); fence(150, W, GROUND + 8);
    for (const x of [14, 38]) sunflower(x, GROUND + 8);
    birch(118, GROUND + 6); birch(185, GROUND + 8);
    well(96, GROUND + 14, t); haystack(60, GROUND + 30); haystack(74, GROUND + 34);
    lantern(30, GROUND + 16, t); lantern(168, GROUND + 14, t);
    for (const [cx, cy] of CHIM) smoke(cx, cy, t);
    if (!reduce) for (const f of FIRE) { const yy = f.y - Math.sin(t / 700 + f.ph * 6) * 4, on = (Math.sin(t / 300 + f.ph * 9) > 0); if (on) A(0.7, () => { R(f.x, yy | 0, 1, 1, '#ffe08a'); discA(f.x, yy | 0, 2, '#ffd24a', 0.3); }); }
  }
  function fence(x1: number, x2: number, y: number) { for (let x = x1; x < x2; x += 3) { R(x, y - 7, 2, 7, '#5a4228'); R(x, y - 8, 2, 1, '#4a3320'); R(x, y - 9, 1, 1, '#3a2a18'); } A(0.4, () => R(x1, y - 4, x2 - x1, 1, '#3a2a18')); }
  function birch(x: number, y: number) {
    R(x - 1, y - 26, 2, 26, '#d8d8cc'); R(x, y - 26, 1, 26, '#b8b8ac'); for (let i = 0; i < 5; i++) R(x - 1, y - 22 + i * 5, 2, 1, '#2a2a2a');
    disc(x, y - 30, 6, mix(C.grass, '#000', 0.2)); disc(x - 3, y - 27, 4, mix(C.grass, '#000', 0.05)); disc(x + 3, y - 33, 4, mix(C.grass, '#efe6cf', 0.12)); A(0.3, () => disc(x + 1, y - 35, 2, C.grass));
  }
  function sunflower(x: number, y: number) {
    R(x, y - 15, 1, 15, '#3a6b2a'); R(x - 2, y - 9, 2, 1, '#3a6b2a'); R(x + 1, y - 12, 2, 1, '#3a6b2a');
    for (let a = 0; a < 7; a++) { const an = a / 7 * 6.28; R((x + Math.cos(an) * 4) | 0, (y - 18 + Math.sin(an) * 4) | 0, 1, 1, '#f2c84a'); } disc(x, y - 18, 2, '#b4822a');
  }
  function haystack(x: number, y: number) { disc(x, y - 2, 8, '#a8893e'); disc(x, y - 6, 6, '#bd9a4c'); disc(x, y - 10, 4, '#d0ab5a'); R(x - 1, y - 13, 2, 3, '#7a5a24'); for (let i = 0; i < 5; i++) R((x - 6 + i * 3) | 0, (y - 1 - (i % 2)) | 0, 1, 1, '#8a6a2a'); }
  function well(x: number, y: number, t: number) {
    R(x - 7, y - 9, 14, 9, '#6b4a2a'); for (let ly = y - 9; ly < y; ly += 2) R(x - 7, ly, 14, 1, mix('#6b4a2a', '#000', 0.22)); R(x - 7, y - 9, 14, 1, mix('#6b4a2a', '#fff', 0.1));
    R(x - 9, y - 15, 18, 3, C.roofDk); R(x - 1, y - 20, 2, 5, '#5a4228');                                           // little roof
    const px = x + 11; R(px - 1, y - 34, 2, 34, '#5a4228');                                                      // журавль post
    let bx0 = px, by0 = y - 30; for (let i = 0; i <= 14; i++) { const bx = lerp(px, x - 3, i / 14) | 0, by = lerp(y - 30, y - 40, i / 14) | 0; R(bx, by, 1, 1, '#4a3826'); }  // slanted sweep
    R(px - 2, y - 30, 4, 5, '#3a2a18');                                                                      // counterweight
    R(x - 4, y - 38, 1, 10, '#6a6a6a'); R(x - 5, y - 28, 3, 3, '#3a2a18');
  }                                          // rope + bucket
  function lantern(x: number, y: number, t: number) { const fl = reduce ? 1 : (0.8 + 0.2 * (Math.sin(t / 160 + x) > 0 ? 1 : 0)); A(fl, () => glow(x, y - 20, 9, C.rimWarm)); R(x - 1, y - 20, 2, 20, '#3a2c1c'); R(x - 3, y - 24, 6, 5, '#241c12'); R(x - 2, y - 23, 4, 3, mix(C.win, '#000', 0.05)); R(x - 3, y - 25, 6, 1, '#4a3826'); }
  function smoke(x: number, y: number, t: number) { if (reduce) return; for (let i = 0; i < 4; i++) { const ph = ((t * 0.016 + i * 0.3) % 1), yy = y - (ph * 26 | 0), rr = 1 + (ph * 3 | 0), xx = x + Math.round(Math.sin(ph * 5 + i) * 3); A(0.14 * (1 - ph), () => disc(xx, yy, rr, '#b8b4b0')); } }

  // ---------- LAYER 5 · спортплощадка + костёр ----------
  function sport(t: number) {
    vgrad(0, SPT, W, H - SPT, mix('#3a2f24', C.dirt, 0.3), '#120d08', 4); R(0, SPT, W, 1, mix('#3a2f24', '#000', 0.4));
    const rp = mulberry(55); for (let i = 0; i < 70; i++) { const x = (rp() * W) | 0, y = SPT + 4 + (rp() * (H - SPT - 6)) | 0; R(x, y, 1, 1, rp() < 0.5 ? mix('#3a2f24', '#fff', 0.05) : mix('#3a2f24', '#000', 0.35)); }
    rrect(10, SPT + 8, W - 20, H - SPT - 16, mix('#3a2f24', C.gold, 0.14));
    // снаряды: турник из брёвен, гири, бревно, камень
    logRig(40, SPT + 10); kettle(176, H - 20); kettle(186, H - 18); heavyLog(168, H - 10); stone(26, H - 12);
    bonfire(104, H - 12, t);                                                                            // костёр = тёплый свет
    heroFox(64, H - 10, t); boss(140, H - 14, AV_MINO, t);
    questBang(140, 266, t);
    A(0.5, () => { disc(-10, -10, 40, '#000'); disc(W + 10, -10, 40, '#000'); disc(-10, H + 10, 46, '#000'); disc(W + 10, H + 10, 46, '#000'); });
  }
  function rrect(x: number, y: number, w: number, h: number, col: string) { R(x + 1, y, w - 2, 1, col); R(x + 1, y + h, w - 2, 1, col); R(x, y + 1, 1, h - 2, col); R(x + w, y + 1, 1, h - 2, col); }
  function logRig(x: number, y: number) { R(x - 22, y, 3, 44, C.woodDk); R(x + 20, y, 3, 44, C.woodDk); R(x - 22, y, 1, 44, mix(C.woodDk, '#fff', 0.12)); R(x - 24, y, 47, 3, '#5a4228'); R(x - 24, y, 47, 1, mix('#5a4228', '#fff', 0.15)); }
  function kettle(x: number, y: number) { R(x - 3, y - 4, 6, 5, '#23272e'); R(x - 3, y - 4, 6, 1, '#343a44'); R(x - 2, y - 7, 4, 3, '#23272e'); R(x - 2, y - 7, 4, 1, '#343a44'); R(x - 1, y - 6, 2, 1, '#0e1014'); }
  function heavyLog(x: number, y: number) { R(x - 10, y - 4, 20, 4, '#6b4a2a'); R(x - 10, y - 4, 20, 1, '#8a5e34'); R(x - 10, y, 20, 1, '#3a2a18'); for (let i = 0; i < 4; i++) R((x - 8 + i * 5) | 0, y - 3, 1, 2, mix('#6b4a2a', '#000', 0.2)); disc(x - 10, y - 2, 2, '#4a3320'); }
  function stone(x: number, y: number) { disc(x, y, 5, '#5a5f66'); R(x - 5, y, 11, 2, '#3f444b'); R(x - 3, y - 3, 5, 2, mix('#5a5f66', '#fff', 0.12)); }
  function bonfire(x: number, gY: number, t: number) {
    A(0.06, () => disc(x, gY + 1, 34, '#ff8a3a')); glow(x, gY - 4, 24, C.fire);            // wide warm pool + glow
    R(x - 10, gY - 1, 20, 3, '#4a3320'); R(x - 8, gY - 3, 16, 2, '#5a4228'); R(x - 9, gY, 4, 2, '#3a2a18'); R(x + 5, gY, 4, 2, '#3a2a18'); R(x - 2, gY - 2, 4, 2, '#2a1e12');
    if (reduce) { R(x - 4, gY - 10, 8, 8, '#ff8a3a'); R(x - 2, gY - 14, 4, 5, '#ffd24a'); }
    else {
      for (let i = 0; i < 7; i++) { const fx = x - 6 + i * 2 + Math.round(Math.sin(t / 90 + i) * 1), fh = 7 + Math.round(Math.sin(t / 70 + i * 1.3) * 3) + ((i === 3) ? 4 : 0); R(fx, gY - 3 - fh, 2, fh, mix(C.fire, '#ffd24a', i / 7)); }
      R(x - 2, gY - 13, 4, 8, '#ffb24a'); R(x - 1, gY - 12, 2, 6, '#ffe08a');
      for (let i = 0; i < 6; i++) { const ph = ((t * 0.045 + i * 0.25) % 1); A(1 - ph, () => R(x - 3 + ((hash(i) * 7) | 0), (gY - 8 - ph * 26) | 0, 1, 1, mix('#ffd24a', C.fire, ph))); }
    }
  }
  function heroFox(x: number, y: number, t: number) {
    const bob = reduce ? 0 : (Math.sin(t / 430) > 0 ? 0 : 1); y -= bob; const hood = '#5a5240', hoodSh = '#43402f', pant = '#3b342a', sc = 0.8;
    A(0.5, () => R(x - 8, y, 16, 1, '#07080c')); R(x - 6, y - 6, 5, 6, pant); R(x + 1, y - 6, 5, 6, pant); R(x - 6, y, 5, 2, '#241c12'); R(x + 1, y, 5, 2, '#241c12');
    R(x - 7, y - 16, 14, 10, hood); R(x - 7, y - 16, 3, 10, hoodSh); R(x + 5, y - 16, 2, 10, mix(hood, '#fff', 0.08)); R(x - 7, y - 16, 14, 2, mix(hood, '#fff', 0.12)); R(x - 1, y - 15, 2, 8, hoodSh);
    A(0.3, () => R(x + 6, y - 16, 1, 10, C.rimWarm)); avatar(AV_FOX, x, y - 13 - Math.round(32 * sc), sc);
  }
  function boss(x: number, y: number, av: Rect[], t: number) {
    const br = reduce ? 0 : (Math.sin(t / 1100) > 0 ? 0 : 1); y -= br; const vest = '#6b2f2a', vestSh = '#471c18', vestHi = '#8a3f36', sc = 0.95;   // red Cossack coat
    A(0.55, () => R(x - 14, y, 28, 1, '#07080c')); R(x - 9, y - 8, 7, 8, '#2a2016'); R(x + 2, y - 8, 7, 8, '#2a2016'); R(x - 9, y, 7, 2, '#140e08'); R(x + 2, y, 7, 2, '#140e08');
    R(x - 12, y - 20, 24, 14, vest); R(x - 12, y - 20, 3, 14, vestSh); R(x + 9, y - 20, 3, 14, vestHi); R(x - 12, y - 20, 24, 2, mix(vest, '#fff', 0.12)); R(x - 1, y - 20, 2, 14, '#d8b34a');  // gold trim closure
    R(x - 16, y - 19, 5, 12, vest); R(x + 11, y - 19, 5, 12, vest); R(x - 16, y - 8, 5, 2, vestSh); R(x + 11, y - 8, 5, 2, vestSh);
    R(x - 12, y - 9, 24, 2, '#1a1a2e'); R(x - 13, y - 9, 2, 3, '#d8b34a');                                            // belt + buckle
    A(0.45, () => R(x - 16, y - 19, 1, 13, C.rimWarm)); A(0.35, () => R(x + 15, y - 19, 1, 13, C.rimCool));                 // warm from the fire (left), cool from moon
    avatar(av, x, y - 17 - Math.round(32 * sc), sc);
  }
  function questBang(x: number, y: number, t: number) {
    const b = reduce ? 0 : Math.round(Math.sin(t / 300) * 2); y += b; glow(x, y + 7, 9, C.gold); R(x - 8, y, 16, 15, C.gold); R(x - 8, y, 16, 2, mix(C.gold, '#fff', 0.4)); rrect(x - 8, y, 16, 15, '#0e1017');
    R(x - 1, y + 3, 3, 6, '#0e1017'); R(x - 1, y + 10, 3, 2, '#0e1017'); for (let i = 0; i < 5; i++) R(x - 4 + i, y + 15 + i, Math.max(1, 8 - 2 * i), 1, C.gold);
  }

  function draw(t: number) { R(0, 0, W, H, '#0e1017'); sky(t); far(t); for (const z of IZBAS) izba(z.x, z.s); church(110); R(0, GROUND, W, 1, '#0b0a08'); yard(t); sport(t); }
  draw(reduce ? 9000 : t);
}
