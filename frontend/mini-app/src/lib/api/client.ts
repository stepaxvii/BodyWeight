import type {
	User,
	UserStats,
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
	CustomRoutineCreate
} from '$lib/types';

const API_BASE = '/bodyweight/api';

// Mock data for development
const MOCK_USER: User = {
	id: 1,
	telegram_id: 123456789,
	username: 'player1',
	first_name: 'Pixel',
	last_name: 'Hero',
	avatar_id: 'shadow-wolf',
	level: 1,
	total_xp: 0,
	coins: 0,
	current_streak: 0,
	max_streak: 0,
	last_workout_date: new Date().toISOString().split('T')[0],
	notifications_enabled: true,
	notification_time: '09:00',
	is_onboarded: false,
	created_at: '2024-01-01T00:00:00Z',
	updated_at: new Date().toISOString()
};

const MOCK_CATEGORIES: ExerciseCategory[] = [
	{ id: 1, slug: 'chest', name: 'Chest & Triceps', name_ru: 'Грудь и трицепс', icon: 'cat_chest', color: '#d82800', sort_order: 1 },
	{ id: 2, slug: 'back', name: 'Back', name_ru: 'Спина', icon: 'cat_back', color: '#0058f8', sort_order: 2 },
	{ id: 3, slug: 'legs', name: 'Legs & Glutes', name_ru: 'Ноги и ягодицы', icon: 'cat_legs', color: '#00a800', sort_order: 3 },
	{ id: 4, slug: 'core', name: 'Core', name_ru: 'Пресс и кор', icon: 'cat_core', color: '#fcc800', sort_order: 4 },
	{ id: 5, slug: 'stretch', name: 'Stretch', name_ru: 'Растяжка', icon: 'cat_stretch', color: '#00a8a8', sort_order: 5 }
];

const MOCK_EXERCISES: Exercise[] = [
	// Strength exercises
	{
		id: 1, slug: 'pushup-regular', category_id: 1, category_slug: 'strength',
		name: 'Push-up', name_ru: 'Классические отжимания',
		description: 'Lie face down, hands shoulder-width apart.',
		description_ru: 'Лягте лицом вниз, руки на ширине плеч.',
		tags: ['chest', 'triceps', 'shoulders', 'home', 'intermediate'],
		difficulty: 2, base_xp: 5, required_level: 1, equipment: 'none', is_timed: false, is_favorite: false,
		easier_exercise_slug: 'pushup-knee', harder_exercise_slug: 'pushup-diamond'
	},
	{
		id: 2, slug: 'pushup-knee', category_id: 1, category_slug: 'strength',
		name: 'Knee Push-up', name_ru: 'Отжимания с колен',
		tags: ['chest', 'triceps', 'home', 'beginner'],
		difficulty: 1, base_xp: 3, required_level: 1, equipment: 'none', is_timed: false, is_favorite: false,
		harder_exercise_slug: 'pushup-regular'
	},
	{
		id: 3, slug: 'pushup-diamond', category_id: 1, category_slug: 'strength',
		name: 'Diamond Push-up', name_ru: 'Отжимания узким хватом',
		tags: ['chest', 'triceps', 'home', 'advanced'],
		difficulty: 3, base_xp: 6, required_level: 1, equipment: 'none', is_timed: false, is_favorite: false,
		easier_exercise_slug: 'pushup-regular'
	},
	{
		id: 4, slug: 'superman', category_id: 1, category_slug: 'strength',
		name: 'Superman', name_ru: 'Супермен',
		tags: ['back', 'lower-back', 'home', 'beginner'],
		difficulty: 1, base_xp: 4, required_level: 1, equipment: 'none', is_timed: false, is_favorite: false
	},
	{
		id: 5, slug: 'squat-regular', category_id: 1, category_slug: 'strength',
		name: 'Squat', name_ru: 'Классические приседания',
		tags: ['quads', 'glutes', 'home', 'beginner'],
		difficulty: 1, base_xp: 4, required_level: 1, equipment: 'none', is_timed: false, is_favorite: false
	},
	// Static exercises
	{
		id: 6, slug: 'plank', category_id: 3, category_slug: 'static',
		name: 'Plank', name_ru: 'Классическая планка',
		tags: ['core', 'home', 'beginner'],
		difficulty: 1, base_xp: 4, required_level: 1, equipment: 'none', is_timed: true, is_favorite: false
	},
	{
		id: 7, slug: 'plank-side', category_id: 3, category_slug: 'static',
		name: 'Side Plank', name_ru: 'Боковая планка',
		tags: ['core', 'home', 'intermediate'],
		difficulty: 2, base_xp: 5, required_level: 1, equipment: 'none', is_timed: true, is_favorite: false
	},
	// Static stretch
	{
		id: 8, slug: 'child-pose', category_id: 5, category_slug: 'static-stretch',
		name: "Child's Pose", name_ru: 'Поза ребёнка',
		tags: ['lower-back', 'hip-flexors', 'home', 'beginner'],
		difficulty: 1, base_xp: 2, required_level: 1, equipment: 'none', is_timed: true, is_favorite: false
	}
];

// Track favorite exercise IDs in mock mode
let mockFavoriteIds: Set<number> = new Set();

const MOCK_ACHIEVEMENTS: Achievement[] = [
	{
		slug: 'first_workout', name: 'First Step', name_ru: 'Первый шаг',
		description: 'Complete your first workout', description_ru: 'Завершите первую тренировку',
		icon: 'ach_first_workout', xp_reward: 50, coin_reward: 100,
		condition: { type: 'total_workouts', value: 1 },
		unlocked: true, unlocked_at: '2024-01-15T10:00:00Z'
	},
	{
		slug: 'streak_7', name: 'Week Warrior', name_ru: 'Недельный воин',
		description: 'Maintain a 7-day streak', description_ru: 'Поддержите серию 7 дней',
		icon: 'ach_streak_7', xp_reward: 200, coin_reward: 300,
		condition: { type: 'streak', value: 7 },
		unlocked: true, unlocked_at: '2024-01-20T10:00:00Z'
	},
	{
		slug: 'streak_30', name: 'Month Master', name_ru: 'Месячный мастер',
		description: 'Maintain a 30-day streak', description_ru: 'Поддержите серию 30 дней',
		icon: 'ach_streak_30', xp_reward: 1000, coin_reward: 1000,
		condition: { type: 'streak', value: 30 },
		unlocked: false, progress: 7
	},
	{
		slug: 'pushup_100', name: 'Push-up Centurion', name_ru: 'Сотня отжиманий',
		description: 'Do 100 push-ups total', description_ru: 'Сделайте 100 отжиманий всего',
		icon: 'ach_100_pushups', xp_reward: 150, coin_reward: 200,
		condition: { type: 'exercise_reps', exercise: 'pushup-*', value: 100 },
		unlocked: false, progress: 67
	},
	{
		slug: 'level_10', name: 'Double Digits', name_ru: 'Двузначный',
		description: 'Reach level 10', description_ru: 'Достигните 10 уровня',
		icon: 'ach_level_10', xp_reward: 500, coin_reward: 500,
		condition: { type: 'level', value: 10 },
		unlocked: false, progress: 5
	}
];

// Leaderboard shows only current user in mocks - real users come from backend
const MOCK_LEADERBOARD: LeaderboardEntry[] = [
	{ rank: 1, user_id: 1, username: 'player1', first_name: 'Pixel', avatar_id: 'shadow-wolf', level: 5, total_xp: 2450, current_streak: 7, is_current_user: true }
];

class ApiClient {
	private initData: string = '';
	private useMocks: boolean = false;

	setInitData(initData: string) {
		this.initData = initData;
	}

	setUseMocks(useMocks: boolean) {
		this.useMocks = useMocks;
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
			return { user: MOCK_USER, token: 'mock-token' };
		}
		return this.request<AuthResponse>('/auth/validate', {
			method: 'POST',
			body: JSON.stringify({ init_data: this.initData })
		});
	}

	// Users
	async getCurrentUser(): Promise<User> {
		if (this.useMocks) {
			return MOCK_USER;
		}
		return this.request<User>('/users/me');
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
			if (data.avatar_id) {
				MOCK_USER.avatar_id = data.avatar_id as User['avatar_id'];
			}
			return MOCK_USER;
		}
		return this.request<User>('/users/me', {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	}

	async completeOnboarding(): Promise<User> {
		if (this.useMocks) {
			MOCK_USER.is_onboarded = true;
			return MOCK_USER;
		}
		return this.request<User>('/users/me/complete-onboarding', {
			method: 'POST'
		});
	}

	// Exercises
	async getCategories(): Promise<ExerciseCategory[]> {
		if (this.useMocks) {
			return MOCK_CATEGORIES;
		}
		return this.request<ExerciseCategory[]>('/exercises/categories');
	}

	async getExercises(category?: string): Promise<Exercise[]> {
		if (this.useMocks) {
			if (category) {
				return MOCK_EXERCISES.filter(e => e.category_slug === category);
			}
			return MOCK_EXERCISES;
		}
		const query = category ? `?category=${category}` : '';
		return this.request<Exercise[]>(`/exercises${query}`);
	}

	async getExercise(slug: string): Promise<Exercise | undefined> {
		if (this.useMocks) {
			return MOCK_EXERCISES.find(e => e.slug === slug);
		}
		return this.request<Exercise>(`/exercises/${slug}`);
	}

	// Workouts
	async startWorkout(): Promise<WorkoutSession> {
		if (this.useMocks) {
			return {
				id: Date.now(),
				user_id: 1,
				started_at: new Date().toISOString(),
				total_xp_earned: 0,
				total_coins_earned: 0,
				total_reps: 0,
				streak_multiplier: 1.12,
				status: 'active',
				exercises: []
			};
		}
		return this.request<WorkoutSession>('/workouts', { method: 'POST' });
	}

	async addExerciseToWorkout(
		workoutId: number,
		exerciseSlug: string,
		reps: number = 0,
		sets: number = 1,
		durationSeconds: number = 0
	): Promise<WorkoutSession> {
		if (this.useMocks) {
			const exercise = MOCK_EXERCISES.find(e => e.slug === exerciseSlug);
			const isTimed = exercise?.category_slug === 'static' || exercise?.category_slug === 'stretch';
			return {
				id: workoutId,
				user_id: 1,
				started_at: new Date().toISOString(),
				total_xp_earned: reps * sets * 2,
				total_coins_earned: Math.floor((reps * sets) / 5),
				total_reps: isTimed ? 0 : reps * sets,
				total_duration_seconds: isTimed ? durationSeconds * sets : 0,
				streak_multiplier: 1.12,
				status: 'active',
				exercises: [{
					id: Date.now(),
					workout_session_id: workoutId,
					exercise_id: exercise?.id ?? 0,
					exercise_slug: exerciseSlug,
					exercise_name: exercise?.name ?? '',
					exercise_name_ru: exercise?.name_ru ?? '',
					is_timed: isTimed,
					exercise,
					sets_completed: sets,
					total_reps: isTimed ? 0 : reps * sets,
					total_duration_seconds: isTimed ? durationSeconds * sets : 0,
					xp_earned: reps * sets * 2,
					coins_earned: Math.floor((reps * sets) / 5),
					completed_at: new Date().toISOString()
				}]
			};
		}
		return this.request<WorkoutSession>(`/workouts/${workoutId}/exercise`, {
			method: 'PUT',
			body: JSON.stringify({
				exercise_slug: exerciseSlug,
				reps,
				sets,
				duration_seconds: durationSeconds
			})
		});
	}

	async completeWorkout(workoutId: number): Promise<WorkoutSummaryResponse> {
		if (this.useMocks) {
			return {
				workout: {
					id: workoutId,
					user_id: 1,
					started_at: new Date(Date.now() - 1800000).toISOString(),
					finished_at: new Date().toISOString(),
					duration_seconds: 1800,
					total_xp_earned: 150,
					total_coins_earned: 15,
					total_reps: 75,
					total_duration_seconds: 0,
					streak_multiplier: 1.12,
					status: 'completed',
					exercises: []
				},
				new_achievements: [],
				level_up: false,
				new_level: null
			};
		}
		return this.request<WorkoutSummaryResponse>(`/workouts/${workoutId}/complete`, { method: 'POST' });
	}

	/**
	 * Submit a completed workout with all exercise data at once.
	 * This is the simplified API - no need to start session or track exercises during workout.
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
			return MOCK_ACHIEVEMENTS;
		}
		return this.request<Achievement[]>('/achievements');
	}

	// Leaderboard
	async getLeaderboard(type: LeaderboardType = 'global'): Promise<LeaderboardEntry[]> {
		if (this.useMocks) {
			return MOCK_LEADERBOARD;
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
			if (mockFavoriteIds.has(exerciseId)) {
				mockFavoriteIds.delete(exerciseId);
				return { exercise_id: exerciseId, is_favorite: false };
			} else {
				mockFavoriteIds.add(exerciseId);
				return { exercise_id: exerciseId, is_favorite: true };
			}
		}
		return this.request<{ exercise_id: number; is_favorite: boolean }>(`/exercises/${exerciseId}/favorite`, {
			method: 'POST'
		});
	}

	async getFavoriteIds(): Promise<number[]> {
		if (this.useMocks) {
			return Array.from(mockFavoriteIds);
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
}

export const api = new ApiClient();
