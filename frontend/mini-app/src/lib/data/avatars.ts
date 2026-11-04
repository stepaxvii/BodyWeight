import type { Avatar, AvatarId } from '$lib/types';
import { t } from '$lib/i18n/index.svelte';

/** Localized avatar name (reactive to the active locale). */
export function getAvatarName(avatar: Avatar): string {
	return t(`gamedata.${avatar.id}.name`);
}

/**
 * Avatar definitions. `name`/`name_ru` are exposed as getters so they resolve
 * through the `gamedata` i18n namespace lazily and stay reactive to the active
 * locale.
 */
function avatar(id: AvatarId, requiredLevel: number, price: number): Avatar {
	return {
		id,
		requiredLevel,
		price,
		get name() {
			return t(`gamedata.${id}.name`);
		},
		get name_ru() {
			return t(`gamedata.${id}.name`);
		},
	};
}

export const AVATARS: Avatar[] = [
	// === Free animals (level 1) ===
	avatar('shadow-wolf', 1, 0),
	avatar('iron-bear', 1, 0),
	avatar('fire-fox', 1, 0),
	avatar('night-panther', 1, 0),

	// === Mythical creatures (paid) ===
	avatar('phoenix', 3, 100),
	avatar('griffin', 5, 200),
	avatar('cerberus', 7, 300),
	avatar('thunder-fang', 7, 350),
	avatar('cyber-ape', 7, 375),
	avatar('hydra', 10, 400),
	avatar('minotaur', 12, 500),
	avatar('kraken', 15, 750),
	avatar('leviathan', 20, 1000),
	avatar('titan', 25, 1500),

	// === New heroes (Stardew redesign) ===
	avatar('solar-lion', 8, 350),
	avatar('crystal-stag', 10, 450),
	avatar('storm-eagle', 14, 600),
	avatar('void-serpent', 18, 900),
	avatar('magma-golem', 22, 1200),
];

export function getAvatar(id: AvatarId): Avatar | undefined {
	return AVATARS.find((a) => a.id === id);
}

export function getAvailableAvatars(level: number): Avatar[] {
	return AVATARS.filter((a) => a.requiredLevel <= level);
}

export function canUnlockAvatar(avatar: Avatar, level: number, coins: number): boolean {
	return level >= avatar.requiredLevel && coins >= avatar.price;
}
