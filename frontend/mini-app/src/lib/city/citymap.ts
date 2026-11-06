// Top-down city-map overlay geometry.
//
// The background art (static/city/citymap_base.png, 1080×1920) is rendered by
// branding/stories/make_citymap2d.py --base: a muted top-down city (the backdrop
// layer) with the 5 district islands drawn on top, but WITHOUT labels, state
// markers, hero or chrome. That same run exports the anchor points below (centre
// of each district island + where its name banner and state badge go) in
// base-image pixels. The /city map draws the PNG at its native aspect ratio and
// positions HTML overlay elements by PERCENTAGE of these anchors, so the overlay
// stays pixel-aligned to the art at any display size with no JS scale math.
//
// KEEP IN SYNC: if the generator's PLOTS/geometry change, re-run `--base` and
// paste the emitted citymap2d.json values here.

type Anchor = [number, number];
export interface CityDistrict {
	center: Anchor; // district island centre (hotspot / "you are here" anchor)
	label: Anchor; // name-banner centre (below the island)
	badge: Anchor; // state marker centre (above the island)
}

export const CITY_MAP = {
	w: 1080,
	h: 1920,
	districts: {
		home: { center: [540, 1440], label: [540, 1550], badge: [540, 1290] },
		french: { center: [270, 1040], label: [270, 1150], badge: [270, 890] },
		cossack: { center: [810, 1040], label: [810, 1150], badge: [810, 890] },
		downtown: { center: [470, 650], label: [470, 760], badge: [470, 500] },
		port: { center: [650, 330], label: [650, 440], badge: [650, 180] }
	} as Record<string, CityDistrict>
};

/** base-image x-pixel → percentage of image width (for `left:` on the overlay). */
export const pctX = (px: number): number => (px / CITY_MAP.w) * 100;
/** base-image y-pixel → percentage of image height (for `top:` on the overlay). */
export const pctY = (px: number): number => (px / CITY_MAP.h) * 100;
