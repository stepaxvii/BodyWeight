import type { User, UserStats, AvatarId } from '$lib/types';
import { api } from '$lib/api/client';

// User state using Svelte 5 runes
class UserStore {
	user = $state<User | null>(null);
	stats = $state<UserStats | null>(null);
	isLoading = $state(false);
	isAuthenticated = $state(false);
	error = $state<string | null>(null);

	// Derived values
	get level() {
		return this.user?.level ?? 1;
	}

	get xp() {
		return this.user?.total_xp ?? 0;
	}

	get coins() {
		return this.user?.coins ?? 0;
	}

	get streak() {
		return this.user?.current_streak ?? 0;
	}

	get xpForCurrentLevel() {
		// Level 1 starts at 0 XP, Level 2 at 100 XP, Level 3 at 400 XP, etc.
		const lvl = this.level - 1;
		return 100 * lvl * lvl;
	}

	get xpForNextLevel() {
		// Level 2 requires 100 XP, Level 3 requires 400 XP, etc.
		const lvl = this.level;
		return 100 * lvl * lvl;
	}

	get xpProgress() {
		const currentLevelXp = this.xpForCurrentLevel;
		const nextLevelXp = this.xpForNextLevel;
		const xpInLevel = this.xp - currentLevelXp;
		const xpNeeded = nextLevelXp - currentLevelXp;
		return Math.min(100, Math.floor((xpInLevel / xpNeeded) * 100));
	}

	get displayName() {
		if (!this.user) return 'Guest';
		return this.user.first_name || this.user.username || 'Guest';
	}

	get isOnboarded() {
		return this.user?.is_onboarded ?? false;
	}

	async authenticate(initData: string) {
		this.isLoading = true;
		this.error = null;

		try {
			// Always use real API - mocks are for development only
			api.setUseMocks(false);
			api.setInitData(initData);
			const response = await api.validateAuth();
			this.user = response.user;
			this.isAuthenticated = true;
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Authentication failed';
			this.isAuthenticated = false;
		} finally {
			this.isLoading = false;
		}
	}

	async loadUser() {
		if (!this.isAuthenticated) return;

		this.isLoading = true;
		try {
			this.user = await api.getCurrentUser();
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to load user';
		} finally {
			this.isLoading = false;
		}
	}

	async loadStats() {
		if (!this.isAuthenticated) return;

		try {
			this.stats = await api.getUserStats();
		} catch (err) {
			console.error('Failed to load stats:', err);
		}
	}

	addXp(amount: number) {
		if (this.user) {
			this.user.total_xp += amount;
			// Check for level up
			while (this.user.total_xp >= this.xpForNextLevel) {
				this.user.level++;
			}
		}
	}

	addCoins(amount: number) {
		if (this.user) {
			this.user.coins += amount;
		}
	}

	spendCoins(amount: number): boolean {
		if (this.user && this.user.coins >= amount) {
			this.user.coins -= amount;
			return true;
		}
		return false;
	}

	updateStreak(streak: number) {
		if (this.user) {
			this.user.current_streak = streak;
			if (streak > this.user.max_streak) {
				this.user.max_streak = streak;
			}
		}
	}

	async setAvatar(avatarId: AvatarId) {
		if (this.user) {
			this.user.avatar_id = avatarId;
			try {
				await api.updateUser({ avatar_id: avatarId });
			} catch (err) {
				console.error('Failed to update avatar:', err);
			}
		}
	}

	async completeOnboarding() {
		if (this.user) {
			try {
				this.user = await api.completeOnboarding();
			} catch (err) {
				console.error('Failed to complete onboarding:', err);
			}
		}
	}
}

export const userStore = new UserStore();
