import type { User, UserStats, AvatarId } from '$lib/types';
import { api } from '$lib/api/client';

export type AuthMode = 'telegram' | 'web' | null;

// User state using Svelte 5 runes
class UserStore {
	user = $state<User | null>(null);
	stats = $state<UserStats | null>(null);
	isLoading = $state(false);
	isAuthenticated = $state(false);
	error = $state<string | null>(null);
	authMode = $state<AuthMode>(null);

	// Derived values
	get level() {
		return Math.max(1, this.user?.level ?? 1);
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

	get streakFreezes() {
		return this.user?.streak_freezes ?? 0;
	}

	get dailyActivityNorm() {
		return this.user?.daily_activity_norm ?? 1400;
	}

	get xpForCurrentLevel() {
		const lvl = this.level - 1;
		return 100 * lvl * lvl;
	}

	get xpForNextLevel() {
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
		if (this.user.username) return `${this.user.username}`;
		return this.user.first_name || this.user.email || 'Guest';
	}

	get isOnboarded() {
		return this.user?.is_onboarded ?? false;
	}

	get hasTelegram() {
		return !!this.user?.telegram_id;
	}

	get hasWebAuth() {
		return !!this.user?.email && !!this.user?.has_password;
	}

	// Telegram Mini App auth
	async authenticate(initData: string) {
		this.isLoading = true;
		this.error = null;

		try {
			api.setInitData(initData);
			const response = await api.validateAuth();
			this.user = response.user;
			this.isAuthenticated = true;
			this.authMode = 'telegram';
			try { localStorage.setItem('cache_user', JSON.stringify(response.user)); } catch {}
		} catch (err) {
			// If offline, try cached user data
			if (!navigator.onLine) {
				try {
					const cached = localStorage.getItem('cache_user');
					if (cached) {
						this.user = JSON.parse(cached);
						this.isAuthenticated = true;
						this.authMode = 'telegram';
						return;
					}
				} catch {}
			}
			this.error = err instanceof Error ? err.message : 'Authentication failed';
			this.isAuthenticated = false;
		} finally {
			this.isLoading = false;
		}
	}

	// Web login
	async webLogin(login: string, password: string) {
		this.isLoading = true;
		this.error = null;

		try {
			const response = await api.webLogin(login, password);
			api.setJwtToken(response.token);
			this.user = response.user;
			this.isAuthenticated = true;
			this.authMode = 'web';
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Login failed';
			this.isAuthenticated = false;
			throw err;
		} finally {
			this.isLoading = false;
		}
	}

	// Web register
	async webRegister(data: { email: string; password: string; username?: string; first_name?: string }) {
		this.isLoading = true;
		this.error = null;

		try {
			const response = await api.webRegister(data);
			api.setJwtToken(response.token);
			this.user = response.user;
			this.isAuthenticated = true;
			this.authMode = 'web';
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Registration failed';
			this.isAuthenticated = false;
			throw err;
		} finally {
			this.isLoading = false;
		}
	}

	// Try to restore session from stored JWT
	async tryRestoreSession() {
		if (!api.hasStoredToken) return false;

		this.isLoading = true;
		this.error = null;

		try {
			const user = await api.getCurrentUser();
			this.user = user;
			this.isAuthenticated = true;
			this.authMode = 'web';
			// Cache user data for offline use
			try { localStorage.setItem('cache_user', JSON.stringify(user)); } catch {}
			return true;
		} catch {
			// If offline, try to use cached user data instead of logging out
			if (!navigator.onLine) {
				try {
					const cached = localStorage.getItem('cache_user');
					if (cached) {
						this.user = JSON.parse(cached);
						this.isAuthenticated = true;
						this.authMode = 'web';
						return true;
					}
				} catch {}
			}
			api.clearAuth();
			this.isAuthenticated = false;
			return false;
		} finally {
			this.isLoading = false;
		}
	}

	logout() {
		api.clearAuth();
		this.user = null;
		this.isAuthenticated = false;
		this.authMode = null;
		this.error = null;
	}

	async loadUser() {
		if (!this.isAuthenticated) return;

		try {
			this.user = await api.getCurrentUser();
		} catch (err) {
			// Don't set error when offline — keep using cached user data
			if (navigator.onLine) {
				this.error = err instanceof Error ? err.message : 'Failed to load user';
			}
		}
	}

	async loadStats() {
		if (!this.isAuthenticated) return;

		try {
			this.stats = await api.getUserStats();
			try { localStorage.setItem('cache_user_stats', JSON.stringify(this.stats)); } catch {}
		} catch (err) {
			console.error('Failed to load stats:', err);
			// Offline fallback
			if (!this.stats) {
				try {
					const cached = localStorage.getItem('cache_user_stats');
					if (cached) this.stats = JSON.parse(cached);
				} catch {}
			}
		}
	}

	addXp(amount: number) {
		if (this.user) {
			this.user.total_xp += amount;
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

	/** Buy one streak freeze. Throws on error (not enough coins / at cap). */
	async buyStreakFreeze(): Promise<User> {
		const updated = await api.buyStreakFreeze();
		this.user = updated;
		return updated;
	}

	/** Set the daily activity norm (XP/day). Throws on error. */
	async setActivityNorm(norm: number): Promise<User> {
		const updated = await api.updateUser({ daily_activity_norm: norm });
		this.user = updated;
		return updated;
	}

	/** Toggle 8-bit sound effects (optimistic, syncs to backend). */
	async setSoundEnabled(enabled: boolean): Promise<void> {
		if (!this.user) return;
		this.user.sound_enabled = enabled;
		try {
			await api.updateUser({ sound_enabled: enabled });
		} catch (err) {
			console.error('Failed to update sound setting:', err);
		}
	}

	/** Toggle visibility in the public leaderboard (privacy). Optimistic; reverts on error. */
	async setLeaderboardVisible(visible: boolean): Promise<void> {
		if (!this.user) return;
		const prev = this.user.leaderboard_visible;
		this.user.leaderboard_visible = visible;
		try {
			this.user = await api.updateUser({ leaderboard_visible: visible });
		} catch (err) {
			if (this.user) this.user.leaderboard_visible = prev;
			throw err;
		}
	}

	/** Toggle Telegram push reminders. Optimistic; reverts on error. */
	async setNotificationsEnabled(enabled: boolean): Promise<void> {
		if (!this.user) return;
		const prev = this.user.notifications_enabled;
		this.user.notifications_enabled = enabled;
		try {
			this.user = await api.updateUser({ notifications_enabled: enabled });
		} catch (err) {
			if (this.user) this.user.notifications_enabled = prev;
			throw err;
		}
	}

	/** Set the daily reminder time ("HH:MM"). Throws on error. */
	async setNotificationTime(time: string): Promise<User> {
		const updated = await api.updateUser({ notification_time: time });
		this.user = updated;
		return updated;
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

	async completeOnboarding(leaderboardConsent: boolean) {
		if (this.user) {
			try {
				this.user = await api.completeOnboarding(leaderboardConsent);
			} catch (err) {
				console.error('Failed to complete onboarding:', err);
			}
		}
	}

	// Set password for TMA user
	async setPassword(email: string, password: string) {
		const response = await api.setPassword(email, password);
		api.setJwtToken(response.token);
		this.user = response.user;
	}

	// Link Telegram account
	async linkTelegram(telegramId: number) {
		return await api.linkTelegram(telegramId);
	}
}

export const userStore = new UserStore();
