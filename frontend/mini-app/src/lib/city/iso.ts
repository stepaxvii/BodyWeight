// Isometric city-map overlay geometry.
//
// The background art (static/city/citymap_iso_base.png, 1080×1920) is rendered by
// branding/stories/make_citymap_iso.py --base. That same run exports the anchor
// points below (centre of each plot + its name-banner + its state badge) in
// base-image pixels. The `/city` map draws the PNG at its native aspect ratio and
// positions HTML overlay elements by PERCENTAGE of these anchors — so the overlay
// stays pixel-aligned to the art at any display size with no JS scale math.
//
// KEEP IN SYNC: if the generator's PLOTS/geometry change, re-run `--base` and
// paste the emitted citymap_iso.json values here.

type Anchor = [number, number];
export interface IsoDistrict {
	center: Anchor; // plot diamond centre (hotspot / "you are here" anchor)
	label: Anchor; // name-banner centre (above the buildings)
	badge: Anchor; // state marker centre (above the banner)
}

export const ISO_MAP = {
	w: 1080,
	h: 1920,
	districts: {
		home: { center: [540, 560], label: [540, 422], badge: [540, 375] },
		french: { center: [300, 820], label: [300, 682], badge: [300, 635] },
		cossack: { center: [780, 820], label: [780, 682], badge: [780, 635] },
		downtown: { center: [540, 1080], label: [540, 942], badge: [540, 895] },
		port: { center: [540, 1340], label: [540, 1202], badge: [540, 1155] }
	} as Record<string, IsoDistrict>
};

/** base-image x-pixel → percentage of image width (for `left:` on the overlay). */
export const pctX = (px: number): number => (px / ISO_MAP.w) * 100;
/** base-image y-pixel → percentage of image height (for `top:` on the overlay). */
export const pctY = (px: number): number => (px / ISO_MAP.h) * 100;
