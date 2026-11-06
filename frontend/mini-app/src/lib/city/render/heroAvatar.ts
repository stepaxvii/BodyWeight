// Turn the player's chosen avatar into a hero head for the district scenes.
//
// The scene renderers draw the hero's head as a Rect[] sprite (AV_FOX by default).
// Avatars live as flat <rect> pixel-art SVGs (static/sprites/avatars/<id>.svg) on
// a 32×32 grid — the same coordinate space the scenes draw in — so we parse those
// rects straight into a Rect[], dropping the full-tile background and any
// semi-transparent decorative aura so the face sits cleanly on the hero body.
//
// IMPORTANT — this is fully DYNAMIC on purpose: there is NO per-avatar sprite
// table to maintain, so adding a new avatar SVG needs no code change and can't
// silently break quest rendering. On ANY problem (missing/unreachable file, parse
// error, or an avatar that yields no usable rects) we return null and every caller
// falls back to the default fox head (`heroAv ?? AV_FOX`) — the scene always draws.
// The only contract is that avatars stay flat <rect> art (no <path>/gradients); a
// future avatar that breaks that just falls back to the fox instead of crashing.

import type { Rect } from './sprites';

const num = (el: Element, name: string, dflt = 0): number => {
	const v = el.getAttribute(name);
	const n = v == null ? dflt : parseFloat(v);
	return Number.isFinite(n) ? n : dflt;
};

// The hero HEAD occupies the AV_FOX box (x∈[4,28], y∈[0,26]) on the 32×32 grid.
// Avatars are FULL portraits (head + body/base/appendages), so we clip every rect
// to that box and drop anything below/outside it — otherwise a golem's base slab
// or a kraken's tentacles would paint over the hero's neck. A wide rect sitting low
// in the box is body, not a facial feature, so it's dropped too.
const HX0 = 4,
	HY0 = 0,
	HX1 = 28,
	HY1 = 26;

/**
 * Fetch + parse an avatar SVG into a drawable Rect[] head. Returns null (→ caller
 * keeps the default fox) if the avatar can't be loaded or yields no usable rects.
 */
export async function loadAvatarHead(base: string, avatarId: string): Promise<Rect[] | null> {
	try {
		const res = await fetch(`${base}/sprites/avatars/${avatarId}.svg`);
		if (!res.ok) return null;
		const doc = new DOMParser().parseFromString(await res.text(), 'image/svg+xml');
		if (doc.querySelector('parsererror')) return null;
		const out: Rect[] = [];
		for (const el of Array.from(doc.querySelectorAll('rect'))) {
			const fill = el.getAttribute('fill');
			if (!fill || fill === 'none') continue;
			if (num(el, 'opacity', 1) < 1) continue; // decorative aura / glow
			const x = num(el, 'x');
			const y = num(el, 'y');
			const w = num(el, 'width');
			const h = num(el, 'height');
			if (w <= 0 || h <= 0) continue;
			if (x <= 0 && y <= 0 && w >= 32 && h >= 32) continue; // full-tile background
			// Clip to the head box; skip rects that fall entirely outside it.
			const cx0 = Math.max(x, HX0);
			const cy0 = Math.max(y, HY0);
			const cx1 = Math.min(x + w, HX1);
			const cy1 = Math.min(y + h, HY1);
			if (cx1 - cx0 < 1 || cy1 - cy0 < 1) continue;
			// A wide rect low in the box is a body/base bar, not a facial feature.
			if (cy0 >= 18 && cx1 - cx0 >= 20) continue;
			out.push([cx0, cy0, cx1 - cx0, cy1 - cy0, fill]);
		}
		return out.length ? out : null;
	} catch {
		return null;
	}
}
