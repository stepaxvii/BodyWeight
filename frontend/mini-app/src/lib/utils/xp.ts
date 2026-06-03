/**
 * XP and Level calculation utilities
 * Based on the formulas from DEVELOPMENT_PLAN.md
 */

// XP per rep = base_xp × rate. The rate gives a classic push-up
// (base_xp = 10) 3 XP/rep. Difficulty is baked into base_xp.
// MUST mirror backend xp_calculator.py.
export const XP_PER_REP_RATE = 0.3;

// A timed hold of this many seconds counts as one rep-equivalent.
export const SECONDS_PER_REP_EQUIVALENT = 10;

/** XP for a single rep (or rep-equivalent) of this exercise. */
export function xpPerRep(baseXp: number): number {
	return baseXp * XP_PER_REP_RATE;
}

/**
 * XP for a reps-based exercise. Mirrors backend calculate_exercise_xp.
 *
 * XP = total_reps × (base_xp × XP_PER_REP_RATE) × streak_mult
 *
 * Strictly proportional to total reps; independent of how the work was
 * split into sets (30 reps = 1×30 = 3×10 = 6×5).
 */
export function calculateExerciseXp(
	baseXp: number,
	totalReps: number,
	streakDays: number = 0
): number {
	if (totalReps <= 0) return 0;
	return Math.floor(totalReps * xpPerRep(baseXp) * getStreakMultiplier(streakDays));
}

/**
 * XP for a timed/hold exercise. Mirrors backend calculate_timed_xp.
 *
 * rep_equivalent = total_seconds / 10
 * XP = rep_equivalent × (base_xp × XP_PER_REP_RATE) × streak_mult
 */
export function calculateTimedXp(
	baseXp: number,
	totalDurationSeconds: number,
	streakDays: number = 0
): number {
	if (totalDurationSeconds <= 0) return 0;
	const repEquiv = totalDurationSeconds / SECONDS_PER_REP_EQUIVALENT;
	return Math.floor(repEquiv * xpPerRep(baseXp) * getStreakMultiplier(streakDays));
}

/**
 * Calculate coins earned from a workout.
 * Coins are rare and valuable!
 *
 * Sources:
 * - Workout XP threshold: 1 coin only if earned 500+ XP
 * - Streak bonus: 1 coin per 7 days of streak (max 4 coins at 28+ days)
 * - Long workout bonus: 1 coin if workout > 45 min
 */
export function calculateCoins(
	xpEarned: number,
	streakDays: number = 0,
	workoutDurationMinutes: number = 0
): number {
	let coins = 0;

	// XP threshold bonus - only for really good workouts
	if (xpEarned >= 500) {
		coins += 1;
	}

	// Streak bonus (1 coin per week of streak, max 4 at 28+ days)
	coins += Math.min(Math.floor(streakDays / 7), 4);

	// Long workout bonus - only for serious sessions
	if (workoutDurationMinutes >= 45) {
		coins += 1;
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
 * Calculate streak multiplier.
 * Ramps linearly from 1.0 (no streak) to 1.5 (+50%) over one week,
 * then stays capped at 1.5 for 7+ days.
 */
export function getStreakMultiplier(streakDays: number): number {
	return 1 + (Math.min(streakDays, 7) / 7) * 0.5;
}

/**
 * Calculate cycling XP from distance, average speed and streak.
 * Formula mirrors backend implementation.
 */
export function calculateCyclingXp(
	distanceKm: number,
	durationMinutes: number,
	streakDays: number = 0
): number {
	if (distanceKm <= 0 || durationMinutes <= 0) return 0;

	const baseXp = distanceKm * 15;
	const avgSpeed = distanceKm / (durationMinutes / 60);
	const multiplier = Math.max(1, Math.min(1.6, 1 + (avgSpeed - 10) * 0.025));

	return Math.floor(baseXp * multiplier * getStreakMultiplier(streakDays));
}

/**
 * Calculate walking XP from total step count and streak.
 * Formula mirrors backend: 1 XP per 50 steps, scaled by streak.
 */
export function calculateWalkingXp(steps: number, streakDays: number = 0): number {
	if (steps <= 0) return 0;
	return Math.floor(Math.floor(steps / 50) * getStreakMultiplier(streakDays));
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
