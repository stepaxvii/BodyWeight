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

// Mock data will be imported dynamically only when needed in dev mode
// This ensures tree-shaking in production builds

class ApiClient {
	private initData: string = '';
	private useMocks: boolean = false;
	private mockDataCache: typeof import('./mock-data.dev') | null = null;

	constructor() {
		// Check env variable for mock mode (only in dev)
		this.useMocks = import.meta.env.DEV && import.meta.env.VITE_USE_MOCKS === 'true';
	}

	setInitData(initData: string) {
		this.initData = initData;
	}

	setUseMocks(useMocks: boolean) {
		// Only allow mocks in development
		this.useMocks = import.meta.env.DEV && useMocks;
	}

	private async getMockData() {
		if (!this.useMocks || !import.meta.env.DEV) {
			return null;
		}
		try {
			if (!this.mockDataCache) {
				this.mockDataCache = await import('./mock-data.dev');
			}
			return this.mockDataCache;
		} catch (error) {
			console.warn('[API] Failed to load mock data, falling back to real API:', error);
			return null;
		}
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
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				return { user: mockData.MOCK_USER, token: 'mock-token' };
			}
		}
		return this.request<AuthResponse>('/auth/validate', {
			method: 'POST',
			body: JSON.stringify({ init_data: this.initData })
		});
	}

	// Users
	async getCurrentUser(): Promise<User> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				return mockData.MOCK_USER;
			}
		}
		return this.request<User>('/users/me');
	}

	async getPurchasedAvatars(): Promise<string[]> {
		if (this.useMocks) {
			// Return empty array for mocks
			return [];
		}
		return this.request<string[]>('/users/me/purchased-avatars');
	}

	async getUserStats(): Promise<UserStats> {
		if (this.useMocks) {
			return {
				total_workouts: 23,
				total_reps: 1540,
				total_xp_earned: 2450,
				total_time_minutes: 345,
				favorite_exercise: 'Push-up',
				favorite_category: 'Push',
				this_week_workouts: 5,
				this_week_xp: 420
			};
		}
		return this.request<UserStats>('/users/me/stats');
	}

	async updateUser(data: { avatar_id?: string; notifications_enabled?: boolean }): Promise<User> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				if (data.avatar_id) {
					mockData.MOCK_USER.avatar_id = data.avatar_id as User['avatar_id'];
				}
				return mockData.MOCK_USER;
			}
		}
		return this.request<User>('/users/me', {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	}

	async completeOnboarding(): Promise<User> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				mockData.MOCK_USER.is_onboarded = true;
				return mockData.MOCK_USER;
			}
		}
		return this.request<User>('/users/me/complete-onboarding', {
			method: 'POST'
		});
	}

	async getUserProfile(userId: number): Promise<UserProfile> {
		if (this.useMocks) {
			return {
				id: userId,
				username: 'mock_user',
				first_name: 'Mock User',
				avatar_id: 'shadow-wolf',
				level: 5,
				total_xp: 1500,
				coins: 200,
				current_streak: 3,
				achievements: ['first-blood'],
				is_friend: false,
				friend_request_sent: false,
				friend_request_received: false,
			};
		}
		return this.request<UserProfile>(`/users/${userId}/profile`);
	}

	// Exercises
	async getCategories(): Promise<ExerciseCategory[]> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				return mockData.MOCK_CATEGORIES;
			}
		}
		return this.request<ExerciseCategory[]>('/exercises/categories');
	}

	async getExercises(category?: string): Promise<Exercise[]> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				if (category) {
					return mockData.MOCK_EXERCISES.filter(e => e.category_slug === category);
				}
				return mockData.MOCK_EXERCISES;
			}
		}
		const query = category ? `?category=${category}` : '';
		return this.request<Exercise[]>(`/exercises${query}`);
	}

	async getExercise(slug: string): Promise<Exercise | undefined> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				return mockData.MOCK_EXERCISES.find(e => e.slug === slug);
			}
		}
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
		if (this.useMocks) {
			const totalReps = data.exercises
				.filter(e => !e.is_timed)
				.reduce((sum, e) => sum + e.sets.reduce((s, r) => s + r, 0), 0);
			const totalDuration = data.exercises
				.filter(e => e.is_timed)
				.reduce((sum, e) => sum + e.sets.reduce((s, r) => s + r, 0), 0);
			return {
				workout: {
					id: Date.now(),
					user_id: 1,
					started_at: new Date(Date.now() - data.duration_seconds * 1000).toISOString(),
					finished_at: new Date().toISOString(),
					duration_seconds: data.duration_seconds,
					total_xp_earned: totalReps * 2 + Math.floor(totalDuration / 10) * 2,
					total_coins_earned: 0,
					total_reps: totalReps,
					total_duration_seconds: totalDuration,
					streak_multiplier: 1.0,
					status: 'completed',
					exercises: []
				},
				new_achievements: [],
				level_up: false,
				new_level: null
			};
		}
		return this.request<WorkoutSummaryResponse>('/workouts/submit', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	}

	// Achievements
	async getAchievements(): Promise<Achievement[]> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				return mockData.MOCK_ACHIEVEMENTS;
			}
		}
		return this.request<Achievement[]>('/achievements');
	}

	// Leaderboard
	async getLeaderboard(type: LeaderboardType = 'global'): Promise<LeaderboardEntry[]> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				return mockData.MOCK_LEADERBOARD;
			}
		}
		const endpoint = type === 'global' ? '/leaderboard' : `/leaderboard/${type}`;
		const response = await this.request<{ entries: LeaderboardEntry[], current_user_rank: number | null }>(endpoint);
		return response.entries;
	}

	// Goals
	async getGoals(): Promise<Goal[]> {
		if (this.useMocks) {
			return [
				{
					id: 1, user_id: 1, goal_type: 'weekly_workouts',
					target_value: 5, current_value: 3,
					start_date: '2024-01-22', end_date: '2024-01-28',
					completed: false
				}
			];
		}
		return this.request<Goal[]>('/goals');
	}

	// Friends
	async getFriends(): Promise<Friend[]> {
		if (this.useMocks) {
			return []; // No fake friends - real users only
		}
		return this.request<Friend[]>('/friends');
	}

	async getFriendRequests(): Promise<Friend[]> {
		if (this.useMocks) {
			return [];
		}
		return this.request<Friend[]>('/friends/requests');
	}

	async searchUsers(query: string): Promise<Friend[]> {
		if (this.useMocks) {
			return []; // Search only works with real backend
		}
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
		if (this.useMocks) {
			return [
				{ id: 1, slug: 'title-champion', name: 'Champion', name_ru: 'Чемпион', item_type: 'title', price_coins: 500, required_level: 10 },
				{ id: 2, slug: 'badge-fire', name: 'Fire Badge', name_ru: 'Огненный значок', item_type: 'badge', price_coins: 200, required_level: 5, is_owned: true }
			];
		}
		return this.request<ShopItem[]>('/shop');
	}

	// Routines (workout complexes)
	async getRoutines(): Promise<Routine[]> {
		if (this.useMocks) {
			return [
				{
					slug: 'morning-light',
					name: 'Лёгкая зарядка',
					description: 'Мягкое пробуждение тела. 5-7 минут для бодрого начала дня.',
					category: 'morning',
					duration_minutes: 7,
					difficulty: 1,
					exercises: [
						{ slug: 'cat-cow', reps: 10 },
						{ slug: 'squat-regular', reps: 10 },
						{ slug: 'jumping-jack', reps: 20 },
						{ slug: 'plank', duration: 20 }
					]
				},
				{
					slug: 'home-beginner',
					name: 'Домашняя тренировка (начало)',
					description: 'Базовая тренировка дома без оборудования.',
					category: 'home',
					duration_minutes: 15,
					difficulty: 1,
					exercises: [
						{ slug: 'jumping-jack', reps: 20 },
						{ slug: 'squat-regular', reps: 15 },
						{ slug: 'pushup-knee', reps: 10 },
						{ slug: 'plank', duration: 20 }
					]
				},
				{
					slug: 'pullup-beginner',
					name: 'Турник для начинающих',
					description: 'Освоение турника. Негативы и австралийские подтягивания.',
					category: 'pullup-bar',
					duration_minutes: 20,
					difficulty: 1,
					exercises: [
						{ slug: 'pullup-regular', reps: 5 },
						{ slug: 'plank', duration: 30 }
					]
				},
				{
					slug: 'dips-beginner',
					name: 'Брусья для начинающих',
					description: 'Подготовка к отжиманиям на брусьях.',
					category: 'dip-bars',
					duration_minutes: 20,
					difficulty: 1,
					exercises: [
						{ slug: 'dip-parallel', reps: 8 },
						{ slug: 'pushup-regular', reps: 10 }
					]
				}
			];
		}
		return this.request<Routine[]>('/exercises/routines/all');
	}

	async getRoutine(slug: string): Promise<Routine | undefined> {
		if (this.useMocks) {
			const routines = await this.getRoutines();
			return routines.find(r => r.slug === slug);
		}
		return this.request<Routine>(`/exercises/routines/${slug}`);
	}

	async getRoutinesByCategory(category: string): Promise<Routine[]> {
		if (this.useMocks) {
			const routines = await this.getRoutines();
			return routines.filter(r => r.category === category);
		}
		return this.request<Routine[]>(`/exercises/routines/all?category=${category}`);
	}

	// ============== Favorites ==============

	async toggleFavorite(exerciseId: number): Promise<{ exercise_id: number; is_favorite: boolean }> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				if (mockData.mockFavoriteIds.has(exerciseId)) {
					mockData.mockFavoriteIds.delete(exerciseId);
					return { exercise_id: exerciseId, is_favorite: false };
				} else {
					mockData.mockFavoriteIds.add(exerciseId);
					return { exercise_id: exerciseId, is_favorite: true };
				}
			}
		}
		return this.request<{ exercise_id: number; is_favorite: boolean }>(`/exercises/${exerciseId}/favorite`, {
			method: 'POST'
		});
	}

	async getFavoriteIds(): Promise<number[]> {
		if (this.useMocks) {
			const mockData = await this.getMockData();
			if (mockData) {
				return Array.from(mockData.mockFavoriteIds);
			}
		}
		return this.request<number[]>('/exercises/favorites/list');
	}

	// ============== Custom Routines ==============

	async getCustomRoutines(routineType?: string): Promise<CustomRoutineListItem[]> {
		if (this.useMocks) {
			return [];
		}
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
		if (this.useMocks) {
			return 0;
		}
		const response = await this.request<{ count: number }>('/notifications/unread-count');
		return response.count;
	}

	async markNotificationsRead(): Promise<void> {
		if (this.useMocks) {
			return;
		}
		await this.request('/notifications/mark-read', {
			method: 'POST'
		});
	}

	async getNotifications(limit: number = 20): Promise<Notification[]> {
		if (this.useMocks) {
			return [];
		}
		return this.request<Notification[]>(`/notifications?limit=${limit}`);
	}
}

export const api = new ApiClient();
