// Avatar types
// Animals (free/cheap) and Mythical Creatures (premium)
export type AvatarId =
	// Free animals (level 1)
	| 'shadow-wolf' | 'iron-bear' | 'fire-fox' | 'night-panther'
	// Paid mythical (increasing price/level)
	| 'phoenix' | 'griffin' | 'cerberus' | 'hydra'
	| 'minotaur' | 'kraken' | 'leviathan' | 'titan';

export interface Avatar {
	id: AvatarId;
	name: string;
	name_ru: string;
	requiredLevel: number;
	price: number; // 0 = free
}

// User types
export interface User {
	id: number;
	telegram_id: number;
	username?: string;
	first_name: string;
	last_name?: string;
	avatar_id: AvatarId;
	level: number;
	total_xp: number;
	coins: number;
	current_streak: number;
	max_streak: number;
	last_workout_date?: string;
	notifications_enabled: boolean;
	notification_time?: string;
	is_onboarded: boolean;
	created_at: string;
	updated_at: string;
}

export interface UserStats {
	total_workouts: number;
	total_reps: number;
	total_xp_earned: number;
	total_time_minutes: number;
	favorite_exercise?: string;
	favorite_category?: string;
	this_week_workouts: number;
	this_week_xp: number;
}

// Exercise types
export interface ExerciseCategory {
	id: number;
	slug: string;
	name: string;
	name_ru: string;
	icon: string;
	color: string;
	sort_order: number;
}

export type EquipmentType = 'none' | 'pullup-bar' | 'dip-bars' | 'bench' | 'wall';

export interface Exercise {
	id: number;
	slug: string;
	category_id: number;
	category_slug: string;
	name: string;
	name_ru: string;
	description?: string;
	description_ru?: string;
	tags: string[]; // Tags for filtering (muscle groups, level, equipment)
	difficulty: 1 | 2 | 3 | 4 | 5;
	base_xp: number;
	required_level: number;
	equipment: EquipmentType;
	is_timed: boolean; // True for time-based exercises (planks, stretches)
	gif_url?: string;
	thumbnail_url?: string;
	easier_exercise_slug?: string;
	harder_exercise_slug?: string;
	is_favorite: boolean; // Whether user has favorited this exercise
}

export interface ExerciseProgress {
	exercise_id: number;
	total_reps_ever: number;
	best_single_set: number;
	times_performed: number;
	last_performed_at?: string;
	recommended_upgrade: boolean;
}

// Workout types
export interface WorkoutSession {
	id: number;
	user_id: number;
	started_at: string;
	finished_at?: string;
	duration_seconds?: number;
	total_xp_earned: number;
	total_coins_earned: number;
	total_reps: number;
	total_duration_seconds: number; // Total time for time-based exercises
	streak_multiplier: number;
	status: 'active' | 'completed' | 'cancelled';
	exercises: WorkoutExercise[];
}

export interface WorkoutExercise {
	id: number;
	workout_session_id?: number;
	exercise_id: number;
	exercise_slug: string;
	exercise_name: string;
	exercise_name_ru: string;
	is_timed: boolean; // True for time-based exercises
	exercise?: Exercise;
	sets_completed: number;
	total_reps: number;
	total_duration_seconds: number; // Duration for time-based exercises
	xp_earned: number;
	coins_earned: number;
	completed_at?: string;
}

export interface WorkoutSet {
	exercise_id: number;
	reps: number;
}

export interface WorkoutSummaryResponse {
	workout: WorkoutSession;
	new_achievements: Achievement[];
	level_up: boolean;
	new_level: number | null;
}

// Achievement types
export interface Achievement {
	slug: string;
	name: string;
	name_ru: string;
	description: string;
	description_ru: string;
	icon: string;
	xp_reward: number;
	coin_reward: number;
	condition: AchievementCondition;
	unlocked?: boolean;
	unlocked_at?: string;
	progress?: number;
}

export interface AchievementCondition {
	type: 'total_workouts' | 'streak' | 'level' | 'exercise_reps' | 'time_of_day';
	value?: number;
	exercise?: string;
	before?: string;
	after?: string;
}

// Leaderboard types
export interface LeaderboardEntry {
	rank: number;
	user_id: number;
	username?: string;
	first_name: string;
	avatar_id: AvatarId;
	level: number;
	total_xp: number;
	current_streak: number;
	is_current_user: boolean;
}

export interface LeaderboardResponse {
	entries: LeaderboardEntry[];
	current_user_rank: number | null;
}

export type LeaderboardType = 'global' | 'friends' | 'weekly';

// Goal types
export interface Goal {
	id: number;
	user_id: number;
	goal_type: 'weekly_workouts' | 'daily_xp' | 'specific_exercise';
	target_value: number;
	current_value: number;
	start_date: string;
	end_date: string;
	completed: boolean;
	completed_at?: string;
}

// Friend types
export interface Friend {
	id: number;
	user_id: number;
	username?: string;
	first_name: string;
	last_name?: string;
	avatar_id: AvatarId;
	level: number;
	current_streak: number;
	status: 'pending' | 'accepted' | 'blocked';
}

// Shop types
export interface ShopItem {
	id: number;
	slug: string;
	name: string;
	name_ru: string;
	item_type: 'title' | 'badge' | 'theme';
	price_coins: number;
	required_level: number;
	sprite_url?: string;
	is_owned?: boolean;
	is_equipped?: boolean;
}

// API Response types
export interface ApiResponse<T> {
	data: T;
	success: boolean;
	message?: string;
}

export interface AuthResponse {
	user: User;
	token: string;
}

// Navigation
export type NavItem = 'home' | 'workout' | 'profile' | 'leaderboard';

// Routine types (workout complexes)
export type RoutineCategory = 'morning' | 'home' | 'pullup-bar' | 'dip-bars';

export interface RoutineExercise {
	slug: string;
	reps?: number;
	duration?: number; // duration in seconds
}

export interface Routine {
	slug: string;
	name: string;
	description: string;
	category: RoutineCategory;
	duration_minutes: number;
	difficulty: 1 | 2 | 3;
	exercises: RoutineExercise[];
}

// Custom routine types (user-created)
export type CustomRoutineType = 'morning' | 'workout' | 'stretch';

export interface CustomRoutineExercise {
	id: number;
	exercise_id: number;
	exercise_slug: string;
	exercise_name_ru: string;
	is_timed: boolean;
	sort_order: number;
	target_reps?: number;
	target_duration?: number;
	rest_seconds: number;
}

export interface CustomRoutine {
	id: number;
	name: string;
	description?: string;
	routine_type: CustomRoutineType;
	duration_minutes: number;
	is_active: boolean;
	exercises: CustomRoutineExercise[];
}

export interface CustomRoutineListItem {
	id: number;
	name: string;
	routine_type: CustomRoutineType;
	duration_minutes: number;
	exercises_count: number;
}

export interface CustomRoutineCreate {
	name: string;
	description?: string;
	routine_type: CustomRoutineType;
	exercises: {
		exercise_id: number;
		target_reps?: number;
		target_duration?: number;
		rest_seconds?: number;
	}[];
}

// Notification types
export type NotificationType = 'friend_request' | 'friend_accepted' | 'daily_reminder' | 'inactivity_reminder';

export interface Notification {
	id: number;
	notification_type: NotificationType;
	title: string;
	message: string;
	is_read: boolean;
	related_user_id?: number;
	created_at: string;
}
