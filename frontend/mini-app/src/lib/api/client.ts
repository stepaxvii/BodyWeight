import type {
	User,
	UserStats,
	UserProfile,
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
	Routine,
	CustomRoutine,
	CustomRoutineListItem,
	CustomRoutineCreate,
	Notification
} from '$lib/types';

const API_BASE = '/bodyweight/api';

class ApiClient {
	private initData: string = '';

	setInitData(initData: string) {
		this.initData = initData;
	}

	private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...(options.headers as Record<string, string>)
		};

		if (this.initData) {
			headers['Authorization'] = `tma ${this.initData}`;
		}

		const url = `${API_BASE}${endpoint}`;
		console.log(`[API] ${options.method || 'GET'} ${url}`, options.body ? JSON.parse(options.body as string) : '');

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

		const data = await response.json();
		console.log(`[API] Response:`, data);
		return data;
	}

	// Auth
	async validateAuth(): Promise<AuthResponse> {
		return this.request<AuthResponse>('/auth/validate', {
			method: 'POST',
			body: JSON.stringify({ init_data: this.initData })
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

	async updateUser(data: { avatar_id?: string; notifications_enabled?: boolean }): Promise<User> {
		return this.request<User>('/users/me', {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	}

	async completeOnboarding(): Promise<User> {
		return this.request<User>('/users/me/complete-onboarding', {
			method: 'POST'
		});
	}

	async getUserProfile(userId: number): Promise<UserProfile> {
		return this.request<UserProfile>(`/users/${userId}/profile`);
	}

	// Exercises
	async getCategories(): Promise<ExerciseCategory[]> {
		return this.request<ExerciseCategory[]>('/exercises/categories');
	}

	async getExercises(category?: string): Promise<Exercise[]> {
		const query = category ? `?category=${category}` : '';
		return this.request<Exercise[]>(`/exercises${query}`);
	}

	async getExercise(slug: string): Promise<Exercise | undefined> {
		return this.request<Exercise>(`/exercises/${slug}`);
	}

	// Workouts
	/**
	 * Submit a completed workout with all exercise data at once.
	 * This is the unified API - no need to start session or track exercises during workout.
	 */
	async submitWorkout(data: {
		duration_seconds: number;
		exercises: Array<{
			exercise_slug: string;
			sets: number[];
			is_timed: boolean;
		}>;
	}): Promise<WorkoutSummaryResponse> {
		return this.request<WorkoutSummaryResponse>('/workouts/submit', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	// Achievements
	async getAchievements(): Promise<Achievement[]> {
		return this.request<Achievement[]>('/achievements');
	}

	// Leaderboard
	async getLeaderboard(type: LeaderboardType = 'global'): Promise<LeaderboardEntry[]> {
		const endpoint = type === 'global' ? '/leaderboard' : `/leaderboard/${type}`;
		const response = await this.request<{ entries: LeaderboardEntry[], current_user_rank: number | null }>(endpoint);
		return response.entries;
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

	async addFriend(username: string): Promise<Friend> {
		return this.request<Friend>('/friends/add', {
			method: 'POST',
			body: JSON.stringify({ username })
		});
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
