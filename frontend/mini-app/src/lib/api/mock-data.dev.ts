/**
 * Mock data для разработки без бэкенда.
 * Используется только в режиме DEV при VITE_USE_MOCKS=true.
 * Этот файл не попадает в production bundle благодаря tree-shaking.
 */

import type {
	User,
	ExerciseCategory,
	Exercise,
	Achievement,
	LeaderboardEntry
} from '$lib/types';

export const MOCK_USER: User = {
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

export const MOCK_CATEGORIES: ExerciseCategory[] = [
	{ id: 1, slug: 'chest', name: 'Chest & Triceps', name_ru: 'Грудь и трицепс', icon: 'cat_chest', color: '#d82800', sort_order: 1 },
	{ id: 2, slug: 'back', name: 'Back', name_ru: 'Спина', icon: 'cat_back', color: '#0058f8', sort_order: 2 },
	{ id: 3, slug: 'legs', name: 'Legs & Glutes', name_ru: 'Ноги и ягодицы', icon: 'cat_legs', color: '#00a800', sort_order: 3 },
	{ id: 4, slug: 'core', name: 'Core', name_ru: 'Пресс и кор', icon: 'cat_core', color: '#fcc800', sort_order: 4 },
	{ id: 5, slug: 'stretch', name: 'Stretch', name_ru: 'Растяжка', icon: 'cat_stretch', color: '#00a8a8', sort_order: 5 }
];

export const MOCK_EXERCISES: Exercise[] = [
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
export let mockFavoriteIds: Set<number> = new Set();

export const MOCK_ACHIEVEMENTS: Achievement[] = [
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
export const MOCK_LEADERBOARD: LeaderboardEntry[] = [
	{ rank: 1, user_id: 1, username: 'player1', first_name: 'Pixel', avatar_id: 'shadow-wolf', level: 5, total_xp: 2450, current_streak: 7, is_current_user: true }
];

