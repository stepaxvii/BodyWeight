import type { Badge, BadgeId } from '$lib/types';
import { t } from '$lib/i18n/index.svelte';

/** Localized badge name (reactive to the active locale). */
export function getBadgeName(badge: Badge): string {
	return t(`gamedata.${badge.id}.name`);
}

/** Localized badge description (reactive to the active locale). */
export function getBadgeDescription(badge: Badge): string {
	return t(`gamedata.${badge.id}.description`);
}

/**
 * Badge definitions. `name`/`name_ru`/`description`/`description_ru` are exposed
 * as getters so they resolve through the `gamedata` i18n namespace lazily and
 * stay reactive to the active locale.
 */
function badge(
	id: BadgeId,
	rarity: Badge['rarity'],
): Badge {
	return {
		id,
		rarity,
		get name() {
			return t(`gamedata.${id}.name`);
		},
		get name_ru() {
			return t(`gamedata.${id}.name`);
		},
		get description() {
			return t(`gamedata.${id}.description`);
		},
		get description_ru() {
			return t(`gamedata.${id}.description`);
		},
	};
}

export const BADGES: Badge[] = [
	// === COMMON ===
	badge('first-blood', 'common'),
	badge('early-bird', 'common'),
	badge('night-owl', 'common'),

	// === RARE ===
	badge('week-warrior', 'rare'),
	badge('iron-will', 'rare'),
	badge('perfectionist', 'rare'),

	// === EPIC ===
	badge('centurion', 'epic'),
	badge('month-master', 'epic'),

	// === LEGENDARY ===
	badge('legend', 'legendary'),
	badge('unstoppable', 'legendary'),
];

export function getBadge(id: BadgeId): Badge | undefined {
	return BADGES.find((b) => b.id === id);
}

export function getBadgesByRarity(rarity: Badge['rarity']): Badge[] {
	return BADGES.filter((b) => b.rarity === rarity);
}

export function getRarityColor(rarity: Badge['rarity']): string {
	switch (rarity) {
		case 'common':
			return '#9CA3AF'; // gray
		case 'rare':
			return '#3B82F6'; // blue
		case 'epic':
			return '#8B5CF6'; // purple
		case 'legendary':
			return '#F59E0B'; // gold
	}
}
