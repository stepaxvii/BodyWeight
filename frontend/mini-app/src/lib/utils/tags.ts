/**
 * Mapping of English exercise-tag slugs to localized names.
 * Display strings live in the `misc.tags` i18n namespace; this file only
 * maps each raw tag slug to its message key.
 */
import { t } from '$lib/i18n/index.svelte';

const TAG_KEYS: Record<string, string> = {
	// Muscle groups
	'chest': 'chest',
	'triceps': 'triceps',
	'biceps': 'biceps',
	'shoulders': 'shoulders',
	'back': 'back',
	'lats': 'lats',
	'core': 'core',
	'abs': 'abs',
	'obliques': 'obliques',
	'legs': 'legs',
	'quads': 'quads',
	'hamstrings': 'hamstrings',
	'glutes': 'glutes',
	'calves': 'calves',
	'hip-flexors': 'hipFlexors',
	'lower-back': 'lowerBack',
	'upper-back': 'upperBack',
	'forearms': 'forearms',
	'traps': 'traps',
	'neck': 'neck',
	'full-body': 'fullBody',

	// Difficulty level
	'beginner': 'beginner',
	'intermediate': 'intermediate',
	'advanced': 'advanced',
	'expert': 'expert',

	// Place/equipment
	'home': 'home',
	'outdoor': 'outdoor',
	'gym': 'gym',
	'pullup-bar': 'pullupBar',
	'dip-bars': 'dipBars',
	'bench': 'bench',
	'bike': 'bike',
	'wall': 'wall',
	'floor': 'floor',
	'no-equipment': 'noEquipment',

	// Exercise type
	'push': 'push',
	'pull': 'pull',
	'hold': 'hold',
	'static': 'static',
	'dynamic': 'dynamic',
	'explosive': 'explosive',
	'plyometric': 'plyometric',
	'balance': 'balance',
	'flexibility': 'flexibility',
	'mobility': 'mobility',
	'stretch': 'stretch',
	'warmup': 'warmup',
	'cooldown': 'cooldown',

	// Cardio
	'cardio': 'cardio',
	'hiit': 'hiit',
	'endurance': 'endurance',
	'fat-burn': 'fatBurn',
	'energy': 'energy',

	// Equipment
	'dumbbell': 'dumbbell',
	'resistance-band': 'resistanceBand',
	'home-friendly': 'homeFriendly',

	// Load type
	'strength': 'strength',
	'power': 'power',
	'functional': 'functional',
	'isolation': 'isolation',
	'gymnastics': 'gymnastics',
	'push-pull': 'pushPull',
	'grip-strength': 'gripStrength',
	'coordination': 'coordination',
	'mindful': 'mindful',
	'intense': 'intense',
	'quick': 'quick',
	'time-saver': 'timeSaver',

	// Body parts
	'arms': 'arms',
	'delts': 'delts',
	'upper-body': 'upperBody',
	'lower-body': 'lowerBody',

	// Body parts for stretching
	'spine': 'spine',
	'hips': 'hips',
	'groin': 'groin',
	'ankles': 'ankles',
	'wrists': 'wrists',
	'chest-stretch': 'chestStretch',
	'back-stretch': 'backStretch',
	'leg-stretch': 'legStretch',
	'arm-stretch': 'armStretch',
};

/**
 * Get the localized name of a tag (falls back to the raw tag slug).
 */
export function getTagName(tag: string): string {
	const key = TAG_KEYS[tag];
	return key ? t(`misc.tags.${key}`) : tag;
}

/**
 * Get localized names for an array of tags.
 */
export function getTagNames(tags: string[]): string[] {
	return tags.map(getTagName);
}
