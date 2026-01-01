// Badge types (unlocked via achievements)
// Badge slugs use kebab-case to match SVG filenames
export type BadgeId =
	| 'first-blood'      // First workout
	| 'workout-10'       // 10 workouts
	| 'workout-50'       // 50 workouts
	| 'centurion'        // 100 workouts total
	| 'workout-365'      // 365 workouts
	| 'streak-3'         // 3 day streak
	| 'week-warrior'     // 7 day streak
	| 'streak-14'        // 14 day streak
	| 'month-master'     // 30 day streak
	| 'iron-will'        // 60 day streak
	| 'unstoppable'      // 100 day streak
	| 'streak-365'       // 365 day streak
	| 'level-5'          // Level 5
	| 'level-10'         // Level 10
	| 'legend'           // Level 25
	| 'level-50'         // Level 50
	| 'level-100'        // Level 100
	| 'early-bird'       // Workout before 7am
	| 'night-owl'        // Workout after 10pm
	| 'perfectionist'    // Complete 10 perfect workouts
	| 'pushup-100'       // 100 pushups total
	| 'pushup-500'       // 500 pushups total
	| 'pushup-1000'      // 1000 pushups total
	| 'squat-100'        // 100 squats total
	| 'squat-500'        // 500 squats total
	| 'squat-1000'       // 1000 squats total
	| 'burpee-50'        // 50 burpees total
	| 'burpee-100'       // 100 burpees total
	| 'burpee-500'       // 500 burpees total
	| 'pullup-100'       // 100 pullups total
	| 'pullup-500'       // 500 pullups total
	| 'xp-1000'          // 1000 XP total
	| 'xp-10000'         // 10000 XP total
	| 'xp-100000';       // 100000 XP total

export interface Badge {
	id: BadgeId;
	name: string;
	name_ru: string;
	description: string;
	description_ru: string;
	rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

// Avatar types
// Animals (free/cheap) and Mythical Creatures (premium)
export type AvatarId =
	// Free animals (level 1)
	| 'shadow-wolf' | 'iron-bear' | 'fire-fox' | 'night-panther'
	// Paid mythical (increasing price/level)
	| 'phoenix' | 'griffin' | 'cerberus' | 'thunder-fang' | 'cyber-ape' | 'hydra'
	| 'minotaur' | 'kraken' | 'leviathan' | 'titan';

export interface Avatar {
	id: AvatarId;
	name: string;
	name_ru: string;
	requiredLevel: number;
	price: number; // 0 = free
}

// User types (matches backend UserResponse)
export interface User {
	id: number;
	telegram_id: number;
	username?: string;
	first_name?: string;
	last_name?: string;
	avatar_id: AvatarId;
	level: number;
	total_xp: number;
	coins: number;
	current_streak: number;
	max_streak: number;
	last_workout_date?: string;
	notification_time?: string;
	notifications_enabled: boolean;
	is_onboarded: boolean;
	created_at: string;
	updated_at: string;
}

// UserStats (matches backend UserStatsResponse)
export interface UserStats {
	total_workouts: number;
	total_xp: number;
	total_reps: number;
	total_time_minutes: number;
	current_level: number;
	xp_for_next_level: number;
	xp_progress_percent: number;
	current_streak: number;
	max_streak: number;
	achievements_count: number;
	coins: number;
	this_week_workouts: number;
	this_week_xp: number;
}

// UserProfile (matches backend UserProfileResponse)
export interface UserProfile {
	id: number;
	username?: string;
	first_name?: string;
	avatar_id: AvatarId;
	level: number;
	total_xp: number;
	coins: number;
	current_streak: number;
	achievements: string[];  // List of unlocked achievement slugs
	is_friend: boolean;
	friend_request_sent: boolean;      // Current user sent request to this user
	friend_request_received: boolean;  // This user sent request to current user
	friendship_id?: number;            // Friendship ID for accept/decline actions
}

// Exercise types (matches backend CategoryResponse)
export interface ExerciseCategory {
	id: number;
	slug: string;
	name: string;
	name_ru: string;
	icon?: string;
	color?: string;
	sort_order: number;
	exercises_count: number;
}

export type EquipmentType = 'none' | 'pullup-bar' | 'dip-bars' | 'bench' | 'wall';

// Exercise (matches backend ExerciseResponse)
export interface Exercise {
	id: number;
	slug: string;
	name: string;
	name_ru: string;
	description?: string;
	description_ru?: string;
	tags: string[]; // Tags for filtering (muscle groups, level, equipment)
	difficulty: number; // 1-5
	base_xp: number;
	required_level: number;
	equipment: EquipmentType;
	is_timed: boolean; // True for time-based exercises (planks, stretches)
	gif_url?: string;
	thumbnail_url?: string;
	category_slug: string;
	easier_exercise_slug?: string;
	harder_exercise_slug?: string;
	is_favorite: boolean; // Whether user has favorited this exercise
}

// ExerciseProgress (matches backend ExerciseProgressResponse)
export interface ExerciseProgress {
	total_reps_ever: number;
	best_single_set: number;
	times_performed: number;
	recommended_upgrade: boolean;
}

// Workout types (matches backend WorkoutResponse)
export interface WorkoutSession {
	id: number;
	started_at: string;
	finished_at?: string;
	duration_seconds?: number;
	total_xp_earned: number;
	total_coins_earned: number;
	total_reps: number;
	total_duration_seconds: number; // Total time for time-based exercises
	streak_multiplier: number;
	status: string; // 'active' | 'completed' | 'cancelled'
	exercises: WorkoutExercise[];
}

// WorkoutExercise (matches backend WorkoutExerciseResponse)
export interface WorkoutExercise {
	id: number;
	exercise_id: number;
	exercise_slug: string;
	exercise_name: string;
	exercise_name_ru: string;
	is_timed: boolean; // True for time-based exercises
	sets_completed: number;
	total_reps: number;
	total_duration_seconds: number; // Duration for time-based exercises
	xp_earned: number;
	coins_earned: number;
}

export interface WorkoutSet {
	exercise_id: number;
	reps: number;
}

// WorkoutSummaryResponse (matches backend WorkoutSummaryResponse)
export interface WorkoutSummaryResponse {
	workout: WorkoutSession;
	new_achievements: Array<Record<string, unknown>>; // list[dict] from backend
	level_up: boolean;
	new_level: number | null;
}

// Achievement types (matches backend AchievementResponse)
export interface Achievement {
	slug: string;
	name: string;
	name_ru: string;
	description: string;
	description_ru: string;
	icon: string;
	xp_reward: number;
	coin_reward: number;
	unlocked: boolean;
	unlocked_at?: string;
	condition: Record<string, unknown>; // dict from backend
}

export interface AchievementCondition {
	type: 'total_workouts' | 'streak' | 'level' | 'exercise_reps' | 'time_of_day';
	value?: number;
	exercise?: string;
	before?: string;
	after?: string;
}

// Leaderboard types (matches backend LeaderboardEntry/Response)
export interface LeaderboardEntry {
	rank: number;
	user_id: number;
	username?: string;
	first_name?: string;
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

// Goal types (matches backend GoalResponse)
export interface Goal {
	id: number;
	goal_type: string; // 'weekly_workouts' | 'daily_xp' | 'weekly_xp' | 'streak_days'
	target_value: number;
	current_value: number;
	start_date: string;
	end_date: string;
	completed: boolean;
	completed_at?: string;
	progress_percent: number;
}

// Friend types (matches backend FriendResponse)
export interface Friend {
	id: number;
	user_id: number;
	username?: string;
	first_name?: string;
	avatar_id: AvatarId;
	level: number;
	total_xp: number;
	current_streak: number;
	status: string; // 'pending' | 'accepted' | 'blocked'
}

// Shop types (matches backend ShopItemResponse)
export interface ShopItem {
	id: number;
	slug: string;
	name: string;
	name_ru: string;
	item_type: string; // 'title' | 'badge' | 'theme'
	price_coins: number;
	required_level: number;
	sprite_url?: string;
	owned: boolean;
	equipped: boolean;
}

// API Response types
export interface ApiResponse<T> {
	data: T;
	success: boolean;
	message?: string;
}

// AuthResponse (matches backend AuthResponse)
export interface AuthResponse {
	user: User;
	is_new: boolean;
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

// Notification types (matches backend NotificationResponse)
export type NotificationType = 'friend_request' | 'friend_accepted' | 'daily_reminder' | 'inactivity_reminder' | 'welcome';

export interface Notification {
	id: number;
	notification_type: string; // NotificationType from backend
	title: string;
	message: string;
	is_read: boolean;
	related_user_id?: number;
	created_at: string;
}
