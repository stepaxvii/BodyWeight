/**
 * XP and Level calculation utilities
 * Based on the formulas from DEVELOPMENT_PLAN.md
 */

/**
 * Calculate XP for completing an exercise set
 */
export function calculateXp(
	baseXp: number,
	difficulty: number,
	reps: number,
	streakDays: number,
	isFirstToday: boolean
): number {
	// Difficulty multiplier: 1.0, 1.25, 1.5, 1.75, 2.0
	const difficultyMult = 1 + (difficulty - 1) * 0.25;

	// Streak bonus (max 50% at 30+ days)
	const streakMult = 1 + Math.min(streakDays, 30) * 0.0167;

	// Volume bonus (diminishing returns after 20 reps)
	let volumeMult: number;
	if (reps <= 20) {
		volumeMult = 1 + reps * 0.02; // 1.0 to 1.4
	} else {
		volumeMult = 1.4 + (reps - 20) * 0.01; // slower growth
	}

	// First workout bonus
	const firstBonus = isFirstToday ? 1.2 : 1.0;

	const xp = baseXp * difficultyMult * streakMult * volumeMult * firstBonus;
	return Math.floor(xp);
}

/**
 * Calculate coins earned from XP
 */
export function calculateCoins(xpEarned: number, hasAchievement: boolean = false): number {
	// Base: 1 coin per 10 XP
	let coins = Math.floor(xpEarned / 10);

	// Achievement bonus
	if (hasAchievement) {
		coins += 50;
	}

	return coins;
}

/**
 * Calculate XP required to reach a specific level
 * Level 1: 0 XP (starting level)
 * Level 2: 100 XP
 * Level 3: 400 XP
 * Level 4: 900 XP
 */
export function xpForLevel(level: number): number {
	const lvl = level - 1;
	return 100 * lvl * lvl; // 0, 100, 400, 900...
}

/**
 * Get current level from total XP
 */
export function getLevelFromXp(totalXp: number): number {
	let level = 1;
	while (xpForLevel(level + 1) <= totalXp) {
		level++;
	}
	return level;
}

/**
 * Calculate XP progress within current level
 */
export function getLevelProgress(totalXp: number): {
	level: number;
	currentLevelXp: number;
	nextLevelXp: number;
	xpInLevel: number;
	xpNeeded: number;
	progressPercent: number;
} {
	const level = getLevelFromXp(totalXp);
	const currentLevelXp = xpForLevel(level);
	const nextLevelXp = xpForLevel(level + 1);
	const xpInLevel = totalXp - currentLevelXp;
	const xpNeeded = nextLevelXp - currentLevelXp;
	const progressPercent = Math.min(100, Math.floor((xpInLevel / xpNeeded) * 100));

	return {
		level,
		currentLevelXp,
		nextLevelXp,
		xpInLevel,
		xpNeeded,
		progressPercent
	};
}

/**
 * Calculate streak multiplier
 */
export function getStreakMultiplier(streakDays: number): number {
	return 1 + Math.min(streakDays, 30) * 0.0167;
}

/**
 * Format XP with K suffix for large numbers
 */
export function formatXp(xp: number): string {
	if (xp >= 10000) {
		return `${(xp / 1000).toFixed(1)}K`;
	}
	return xp.toString();
}
