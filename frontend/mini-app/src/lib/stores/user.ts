import { writable, derived } from 'svelte/store';
import type { User } from '$lib/api/client';

export const user = writable<User | null>(null);

export const userLevel = derived(user, ($user) => $user?.level ?? 1);
export const userXP = derived(user, ($user) => $user?.experience ?? 0);
export const userStreak = derived(user, ($user) => $user?.streak_days ?? 0);

export function getLevelProgress(experience: number, level: number): number {
	const currentThreshold = 100 * (level ** 2);
	const nextThreshold = 100 * ((level + 1) ** 2);
	const progressInLevel = experience - currentThreshold;
	const levelRange = nextThreshold - currentThreshold;
	return levelRange > 0 ? Math.floor((progressInLevel / levelRange) * 100) : 0;
}

export function getXPForNextLevel(level: number): number {
	return 100 * ((level + 1) ** 2);
}
