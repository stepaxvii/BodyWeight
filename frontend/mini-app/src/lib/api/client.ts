import type {
	User,
	UserStats,
	UserProfile,
	UserActivity,
	Exercise,
	ExerciseCategory,
	WorkoutSession,
	WorkoutSummaryResponse,
	Achievement,
	LeaderboardEntry,
	LeaderboardType,
	Goal,
	Friend,
	ShopItem,
	AuthResponse,
	WebAuthResponse,
	Routine,
	CustomRoutine,
	CustomRoutineListItem,
	CustomRoutineCreate,
	Notification,
	PaginatedResponse
} from '$lib/types';

const API_BASE = '/bodyweight/api';
const TOKEN_KEY = 'pixelfit_token';

class ApiClient {
	private initData: string = '';
	private jwtToken: string = '';

	constructor() {
		// Restore JWT token from localStorage
		if (typeof window !== 'undefined') {
			this.jwtToken = localStorage.getItem(TOKEN_KEY) || '';
		}
	}

	setInitData(initData: string) {
		this.initData = initData;
	}

	setJwtToken(token: string) {
		this.jwtToken = token;
		if (typeof window !== 'undefined') {
			localStorage.setItem(TOKEN_KEY, token);
		}
	}

	clearAuth() {
		this.jwtToken = '';
		this.initData = '';
		if (typeof window !== 'undefined') {
			localStorage.removeItem(TOKEN_KEY);
		}
	}

	get hasStoredToken(): boolean {
		return !!this.jwtToken;
	}

	private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...(options.headers as Record<string, string>)
		};

		if (this.initData) {
			headers['Authorization'] = `tma ${this.initData}`;
		} else if (this.jwtToken) {
			headers['Authorization'] = `Bearer ${this.jwtToken}`;
		}

		const url = `${API_BASE}${endpoint}`;
		const response = await fetch(url, {
			...options,
			headers
		});

		if (!response.ok) {
			const errorText = await response.text();
			console.error(`[API] Error ${response.status}:`, errorText);
			let errorMessage = `API Error: ${response.status}`;
			try {
				const errorJson = JSON.parse(errorText);
				errorMessage = errorJson.detail || errorMessage;
			} catch {
				// Ignore JSON parse errors
			}
			throw new Error(errorMessage);
		}

		if (response.status === 204) {
			return undefined as T;
		}

		const data = await response.json();
		return data;
	}

	// Auth - Telegram
	async validateAuth(): Promise<AuthResponse> {
		return this.request<AuthResponse>('/auth/validate', {
			method: 'POST',
			body: JSON.stringify({ init_data: this.initData })
		});
	}

	// Auth - Web
	async webRegister(data: { email: string; password: string; username?: string; first_name?: string }): Promise<WebAuthResponse> {
		return this.request<WebAuthResponse>('/auth/register', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	async webLogin(login: string, password: string): Promise<WebAuthResponse> {
		return this.request<WebAuthResponse>('/auth/login', {
			method: 'POST',
			body: JSON.stringify({ login, password })
		});
	}

	async setPassword(email: string, password: string): Promise<WebAuthResponse> {
		return this.request<WebAuthResponse>('/auth/set-password', {
			method: 'POST',
			body: JSON.stringify({ email, password })
		});
	}

	async linkTelegram(telegramId: number): Promise<{ message: string }> {
		return this.request<{ message: string }>('/auth/link-telegram', {
			method: 'POST',
			body: JSON.stringify({ telegram_id: telegramId })
		});
	}

	// Users
	async getCurrentUser(): Promise<User> {
		return this.request<User>('/users/me');
	}

	async getPurchasedAvatars(): Promise<string[]> {
		return this.request<string[]>('/users/me/purchased-avatars');
	}

	async getUserStats(): Promise<UserStats> {
		return this.request<UserStats>('/users/me/stats');
	}

	async updateUser(data: { avatar_id?: string; notifications_enabled?: boolean; leaderboard_visible?: boolean }): Promise<User> {
		return this.request<User>('/users/me', {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	}

	async completeOnboarding(leaderboardConsent: boolean): Promise<User> {
		return this.request<User>('/users/me/complete-onboarding', {
			method: 'POST',
			body: JSON.stringify({ leaderboard_consent: leaderboardConsent })
		});
	}

	async getUserProfile(userId: number): Promise<UserProfile> {
		return this.request<UserProfile>(`/users/${userId}/profile`);
	}

	async getUserActivity(year?: number): Promise<UserActivity> {
		const query = year ? `?year=${year}` : '';
		return this.request<UserActivity>(`/users/me/activity${query}`);
	}

	// Exercises
	async getCategories(): Promise<ExerciseCategory[]> {
		return this.request<ExerciseCategory[]>('/exercises/categories');
	}

	async getExercises(
		category?: string,
		options?: { skip?: number; limit?: number }
	): Promise<PaginatedResponse<Exercise>> {
		const params = new URLSearchParams();
		if (category) params.append('category', category);
		if (options?.skip !== undefined) params.append('skip', options.skip.toString());
		if (options?.limit !== undefined) params.append('limit', options.limit.toString());
		const query = params.toString() ? `?${params.toString()}` : '';
		return this.request<PaginatedResponse<Exercise>>(`/exercises${query}`);
	}

	async getAllExercises(category?: string): Promise<Exercise[]> {
		const allExercises: Exercise[] = [];
		let skip = 0;
		const limit = 100;
		let hasMore = true;

		while (hasMore) {
			const response = await this.getExercises(category, { skip, limit });
			allExercises.push(...response.items);
			hasMore = response.has_more;
			skip += limit;
		}

		return allExercises;
	}

	async getExercise(slug: string): Promise<Exercise | undefined> {
		return this.request<Exercise>(`/exercises/${slug}`);
	}

	// Workouts
	async submitWorkout(data: {
		duration_seconds: number;
		exercises: Array<{
			exercise_slug: string;
			sets: number[];
			is_timed: boolean;
		}>;
		completed_at?: string;
	}): Promise<WorkoutSummaryResponse> {
		return this.request<WorkoutSummaryResponse>('/workouts/submit', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	// Achievements
	async getAchievements(options?: { skip?: number; limit?: number }): Promise<PaginatedResponse<Achievement>> {
		const params = new URLSearchParams();
		if (options?.skip !== undefined) params.append('skip', options.skip.toString());
		if (options?.limit !== undefined) params.append('limit', options.limit.toString());
		const query = params.toString() ? `?${params.toString()}` : '';
		return this.request<PaginatedResponse<Achievement>>(`/achievements${query}`);
	}

	async getAllAchievements(): Promise<Achievement[]> {
		const allAchievements: Achievement[] = [];
		let skip = 0;
		const limit = 100;
		let hasMore = true;

		while (hasMore) {
			const response = await this.getAchievements({ skip, limit });
			allAchievements.push(...response.items);
			hasMore = response.has_more;
			skip += limit;
		}

		return allAchievements;
	}

	// Leaderboard
	async getLeaderboard(type: LeaderboardType = 'global'): Promise<LeaderboardEntry[]> {
		const endpoint = type === 'global' ? '/leaderboard' : `/leaderboard/${type}`;
		const response = await this.request<{ entries: LeaderboardEntry[]; current_user_rank: number | null }>(endpoint);
		return Array.isArray(response?.entries) ? response.entries : [];
	}

	// Goals
	async getGoals(): Promise<Goal[]> {
		return this.request<Goal[]>('/goals');
	}

	// Friends
	async getFriends(): Promise<Friend[]> {
		return this.request<Friend[]>('/friends');
	}

	async getFriendRequests(): Promise<Friend[]> {
		return this.request<Friend[]>('/friends/requests');
	}

	async searchUsers(query: string): Promise<Friend[]> {
		return this.request<Friend[]>(`/friends/search?q=${encodeURIComponent(query)}`);
	}

	async addFriend(usernameOrId: string | number): Promise<Friend> {
		const body =
			typeof usernameOrId === 'number'
				? { user_id: usernameOrId }
				: { username: usernameOrId };

		return this.request<Friend>('/friends/add', {
			method: 'POST',
			body: JSON.stringify(body)
		});
	}

	async getInviteLink(): Promise<{ invite_link: string; user_id: number }> {
		return this.request('/friends/invite-link');
	}

	async acceptFriendRequest(friendshipId: number): Promise<Friend> {
		return this.request<Friend>(`/friends/accept/${friendshipId}`, {
			method: 'POST'
		});
	}

	async removeFriend(friendshipId: number): Promise<void> {
		await this.request(`/friends/${friendshipId}`, {
			method: 'DELETE'
		});
	}

	// Shop
	async getShopItems(): Promise<ShopItem[]> {
		return this.request<ShopItem[]>('/shop');
	}

	// Routines (workout complexes)
	async getRoutines(): Promise<Routine[]> {
		return this.request<Routine[]>('/exercises/routines/all');
	}

	async getRoutine(slug: string): Promise<Routine | undefined> {
		return this.request<Routine>(`/exercises/routines/${slug}`);
	}

	async getRoutinesByCategory(category: string): Promise<Routine[]> {
		return this.request<Routine[]>(`/exercises/routines/all?category=${category}`);
	}

	// ============== Favorites ==============

	async toggleFavorite(exerciseId: number): Promise<{ exercise_slug: string; is_favorite: boolean }> {
		return this.request<{ exercise_slug: string; is_favorite: boolean }>(`/exercises/${exerciseId}/favorite`, {
			method: 'POST'
		});
	}

	async getFavoriteIds(): Promise<number[]> {
		return this.request<number[]>('/exercises/favorites/list');
	}

	// ============== Custom Routines ==============

	async getCustomRoutines(routineType?: string): Promise<CustomRoutineListItem[]> {
		const query = routineType ? `?routine_type=${routineType}` : '';
		return this.request<CustomRoutineListItem[]>(`/custom-routines${query}`);
	}

	async getCustomRoutine(routineId: number): Promise<CustomRoutine> {
		return this.request<CustomRoutine>(`/custom-routines/${routineId}`);
	}

	async createCustomRoutine(data: CustomRoutineCreate): Promise<CustomRoutine> {
		return this.request<CustomRoutine>('/custom-routines', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	async updateCustomRoutine(routineId: number, data: Partial<CustomRoutineCreate>): Promise<CustomRoutine> {
		return this.request<CustomRoutine>(`/custom-routines/${routineId}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	}

	async deleteCustomRoutine(routineId: number): Promise<void> {
		await this.request(`/custom-routines/${routineId}`, {
			method: 'DELETE'
		});
	}

	async duplicateCustomRoutine(routineId: number): Promise<CustomRoutine> {
		return this.request<CustomRoutine>(`/custom-routines/${routineId}/duplicate`, {
			method: 'POST'
		});
	}

	// ============== Notifications ==============

	async getUnreadNotificationCount(): Promise<number> {
		const response = await this.request<{ count: number }>('/notifications/unread-count');
		return response.count;
	}

	async markNotificationsRead(): Promise<void> {
		await this.request('/notifications/mark-read', {
			method: 'POST'
		});
	}

	async getNotifications(limit: number = 20): Promise<Notification[]> {
		return this.request<Notification[]>(`/notifications?limit=${limit}`);
	}
}

export const api = new ApiClient();
