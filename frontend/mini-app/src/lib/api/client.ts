import type {
	User,
	UserStats,
	Exercise,
	ExerciseCategory,
	WorkoutSession,
	Achievement,
	LeaderboardEntry,
	LeaderboardType,
	Goal,
	Friend,
	ShopItem,
	AuthResponse,
	Routine
} from '$lib/types';

const API_BASE = '/api';

// Mock data for development
const MOCK_USER: User = {
	id: 1,
	telegram_id: 123456789,
	username: 'player1',
	first_name: 'Pixel',
	last_name: 'Hero',
	avatar_id: 'wolf',
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
	{ id: 1, slug: 'push', name: 'Push', name_ru: 'Толкающие', icon: 'cat_push', color: '#d82800', sort_order: 1 },
	{ id: 2, slug: 'pull', name: 'Pull', name_ru: 'Тянущие', icon: 'cat_pull', color: '#0058f8', sort_order: 2 },
	{ id: 3, slug: 'legs', name: 'Legs', name_ru: 'Ноги', icon: 'cat_legs', color: '#00a800', sort_order: 3 },
	{ id: 4, slug: 'core', name: 'Core', name_ru: 'Кор', icon: 'cat_core', color: '#fcc800', sort_order: 4 },
	{ id: 5, slug: 'static', name: 'Static', name_ru: 'Статика', icon: 'cat_static', color: '#6800a8', sort_order: 5 },
	{ id: 6, slug: 'cardio', name: 'Cardio', name_ru: 'Кардио', icon: 'cat_cardio', color: '#fc7400', sort_order: 6 },
	{ id: 7, slug: 'warmup', name: 'Warm-up', name_ru: 'Разминка', icon: 'cat_warmup', color: '#00a8a8', sort_order: 7 },
	{ id: 8, slug: 'stretch', name: 'Stretch', name_ru: 'Растяжка', icon: 'cat_stretch', color: '#f878f8', sort_order: 8 }
];

const MOCK_EXERCISES: Exercise[] = [
	{
		id: 1, slug: 'pushup-regular', category_id: 1, category_slug: 'push',
		name: 'Push-up', name_ru: 'Отжимания',
		description: 'Classic push-up with hands shoulder-width apart',
		description_ru: 'Классические отжимания, руки на ширине плеч',
		difficulty: 2, base_xp: 10, required_level: 1, equipment: 'none',
		easier_exercise_slug: 'pushup-knee', harder_exercise_slug: 'pushup-diamond'
	},
	{
		id: 2, slug: 'pushup-knee', category_id: 1, category_slug: 'push',
		name: 'Knee Push-up', name_ru: 'Отжимания с колен',
		difficulty: 1, base_xp: 8, required_level: 1, equipment: 'none',
		harder_exercise_slug: 'pushup-regular'
	},
	{
		id: 3, slug: 'pushup-diamond', category_id: 1, category_slug: 'push',
		name: 'Diamond Push-up', name_ru: 'Алмазные отжимания',
		difficulty: 4, base_xp: 15, required_level: 5, equipment: 'none',
		easier_exercise_slug: 'pushup-regular'
	},
	{
		id: 4, slug: 'pullup-regular', category_id: 2, category_slug: 'pull',
		name: 'Pull-up', name_ru: 'Подтягивания',
		difficulty: 3, base_xp: 15, required_level: 3, equipment: 'pullup-bar'
	},
	{
		id: 5, slug: 'squat-regular', category_id: 3, category_slug: 'legs',
		name: 'Squat', name_ru: 'Приседания',
		difficulty: 2, base_xp: 10, required_level: 1, equipment: 'none'
	},
	{
		id: 6, slug: 'plank', category_id: 4, category_slug: 'core',
		name: 'Plank', name_ru: 'Планка',
		difficulty: 2, base_xp: 12, required_level: 1, equipment: 'none'
	},
	{
		id: 7, slug: 'wall-sit', category_id: 5, category_slug: 'static',
		name: 'Wall Sit', name_ru: 'Стенка',
		difficulty: 2, base_xp: 10, required_level: 1, equipment: 'none'
	},
	{
		id: 8, slug: 'jumping-jack', category_id: 6, category_slug: 'cardio',
		name: 'Jumping Jacks', name_ru: 'Джампинг Джек',
		difficulty: 1, base_xp: 8, required_level: 1, equipment: 'none'
	},
	{
		id: 9, slug: 'dip-parallel', category_id: 1, category_slug: 'push',
		name: 'Parallel Bar Dips', name_ru: 'Отжимания на брусьях',
		difficulty: 3, base_xp: 15, required_level: 3, equipment: 'dip-bars'
	}
];

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
	{ rank: 1, user_id: 1, username: 'player1', first_name: 'Pixel', avatar_id: 'wolf', level: 5, total_xp: 2450, current_streak: 7, is_current_user: true }
];

class ApiClient {
	private initData: string = '';
	private useMocks: boolean = true;

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

		const response = await fetch(`${API_BASE}${endpoint}`, {
			...options,
			headers
		});

		if (!response.ok) {
			throw new Error(`API Error: ${response.status}`);
		}

		return response.json();
	}

	// Auth
	async validateAuth(): Promise<AuthResponse> {
		if (this.useMocks) {
			return { user: MOCK_USER, token: 'mock-token' };
		}
		return this.request<AuthResponse>('/auth/validate', { method: 'POST' });
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

	async addExerciseToWorkout(workoutId: number, exerciseSlug: string, reps: number, sets: number = 1): Promise<WorkoutSession> {
		if (this.useMocks) {
			const exercise = MOCK_EXERCISES.find(e => e.slug === exerciseSlug);
			return {
				id: workoutId,
				user_id: 1,
				started_at: new Date().toISOString(),
				total_xp_earned: reps * sets * 2,
				total_coins_earned: Math.floor((reps * sets) / 5),
				total_reps: reps * sets,
				streak_multiplier: 1.12,
				status: 'active',
				exercises: [{
					id: Date.now(),
					workout_session_id: workoutId,
					exercise_id: exercise?.id ?? 0,
					exercise,
					sets_completed: sets,
					total_reps: reps * sets,
					xp_earned: reps * sets * 2,
					coins_earned: Math.floor((reps * sets) / 5),
					completed_at: new Date().toISOString()
				}]
			};
		}
		return this.request<WorkoutSession>(`/workouts/${workoutId}/exercise`, {
			method: 'PUT',
			body: JSON.stringify({ exercise_slug: exerciseSlug, reps, sets })
		});
	}

	async completeWorkout(workoutId: number): Promise<WorkoutSession> {
		if (this.useMocks) {
			return {
				id: workoutId,
				user_id: 1,
				started_at: new Date(Date.now() - 1800000).toISOString(),
				finished_at: new Date().toISOString(),
				duration_seconds: 1800,
				total_xp_earned: 150,
				total_coins_earned: 15,
				total_reps: 75,
				streak_multiplier: 1.12,
				status: 'completed',
				exercises: []
			};
		}
		return this.request<WorkoutSession>(`/workouts/${workoutId}/complete`, { method: 'POST' });
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
		return this.request<LeaderboardEntry[]>(endpoint);
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
}

export const api = new ApiClient();
