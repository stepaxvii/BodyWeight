// User types
export interface User {
	id: number;
	telegram_id: number;
	username?: string;
	first_name: string;
	last_name?: string;
	photo_url?: string;
	level: number;
	total_xp: number;
	coins: number;
	current_streak: number;
	max_streak: number;
	last_workout_date?: string;
	notifications_enabled: boolean;
	notification_time?: string;
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

export interface Exercise {
	id: number;
	slug: string;
	category_id: number;
	category_slug: string;
	name: string;
	name_ru: string;
	description?: string;
	description_ru?: string;
	difficulty: 1 | 2 | 3 | 4 | 5;
	base_xp: number;
	required_level: number;
	gif_url?: string;
	thumbnail_url?: string;
	easier_exercise_slug?: string;
	harder_exercise_slug?: string;
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
	streak_multiplier: number;
	status: 'active' | 'completed' | 'cancelled';
	exercises: WorkoutExercise[];
}

export interface WorkoutExercise {
	id: number;
	workout_session_id: number;
	exercise_id: number;
	exercise?: Exercise;
	sets_completed: number;
	total_reps: number;
	xp_earned: number;
	coins_earned: number;
	completed_at: string;
}

export interface WorkoutSet {
	exercise_id: number;
	reps: number;
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
	photo_url?: string;
	level: number;
	total_xp: number;
	current_streak: number;
	is_current_user: boolean;
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
	photo_url?: string;
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
