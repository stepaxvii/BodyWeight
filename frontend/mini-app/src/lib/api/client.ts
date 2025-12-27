import { get } from 'svelte/store';
import { token } from '$lib/stores/auth';

const API_BASE = import.meta.env.VITE_API_URL || '/bodyweight/api';

interface RequestOptions {
	method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
	body?: unknown;
	headers?: Record<string, string>;
}

class ApiClient {
	private baseUrl: string;

	constructor(baseUrl: string) {
		this.baseUrl = baseUrl;
	}

	private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
		const { method = 'GET', body, headers = {} } = options;

		const accessToken = get(token);

		const requestHeaders: Record<string, string> = {
			'Content-Type': 'application/json',
			...headers,
		};

		if (accessToken) {
			requestHeaders['Authorization'] = `Bearer ${accessToken}`;
		}

		const response = await fetch(`${this.baseUrl}${endpoint}`, {
			method,
			headers: requestHeaders,
			body: body ? JSON.stringify(body) : undefined,
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
			throw new Error(error.detail || `HTTP ${response.status}`);
		}

		if (response.status === 204) {
			return {} as T;
		}

		return response.json();
	}

	// Auth
	async authTelegram(initData: string): Promise<{ access_token: string }> {
		return this.request('/auth/telegram', {
			method: 'POST',
			body: { init_data: initData },
		});
	}

	// Users
	async getMe(): Promise<User> {
		return this.request('/users/me');
	}

	async updateMe(data: Partial<UserUpdate>): Promise<User> {
		return this.request('/users/me', {
			method: 'PATCH',
			body: data,
		});
	}

	// Exercises
	async getExercises(category?: string): Promise<Exercise[]> {
		const params = category ? `?category=${category}` : '';
		return this.request(`/exercises${params}`);
	}

	async getExercise(id: number): Promise<Exercise> {
		return this.request(`/exercises/${id}`);
	}

	// Workouts
	async startWorkout(): Promise<Workout> {
		return this.request('/workouts', { method: 'POST' });
	}

	async addExerciseToWorkout(
		workoutId: number,
		data: WorkoutExerciseCreate
	): Promise<WorkoutExercise> {
		return this.request(`/workouts/${workoutId}/exercises`, {
			method: 'POST',
			body: data,
		});
	}

	async finishWorkout(workoutId: number): Promise<WorkoutResult> {
		return this.request(`/workouts/${workoutId}/finish`, { method: 'POST' });
	}

	async getWorkoutHistory(limit = 20, offset = 0): Promise<Workout[]> {
		return this.request(`/workouts?limit=${limit}&offset=${offset}`);
	}

	async getWorkout(id: number): Promise<Workout> {
		return this.request(`/workouts/${id}`);
	}

	// Goals
	async getGoals(): Promise<Goal[]> {
		return this.request('/goals');
	}

	async createGoal(data: GoalCreate): Promise<Goal> {
		return this.request('/goals', {
			method: 'POST',
			body: data,
		});
	}

	async deleteGoal(id: number): Promise<void> {
		return this.request(`/goals/${id}`, { method: 'DELETE' });
	}

	// Achievements
	async getAchievements(): Promise<AchievementWithStatus[]> {
		return this.request('/achievements');
	}

	async getUnlockedAchievements(): Promise<UserAchievement[]> {
		return this.request('/achievements/unlocked');
	}

	// Leaderboard
	async getLeaderboard(type: 'global' | 'friends' = 'global', limit = 50): Promise<LeaderboardEntry[]> {
		return this.request(`/leaderboard?type=${type}&limit=${limit}`);
	}

	async getMyRank(): Promise<{ rank: number | null; total_users: number }> {
		return this.request('/leaderboard/my-rank');
	}

	// Friends
	async getFriends(): Promise<Friend[]> {
		return this.request('/friends');
	}

	async getFriendRequests(): Promise<Friend[]> {
		return this.request('/friends/requests');
	}

	async addFriend(username: string): Promise<{ message: string }> {
		return this.request('/friends/add', {
			method: 'POST',
			body: { username },
		});
	}

	async acceptFriend(friendshipId: number): Promise<{ message: string }> {
		return this.request(`/friends/${friendshipId}/accept`, { method: 'POST' });
	}

	async rejectFriend(friendshipId: number): Promise<{ message: string }> {
		return this.request(`/friends/${friendshipId}/reject`, { method: 'POST' });
	}

	async removeFriend(friendId: number): Promise<{ message: string }> {
		return this.request(`/friends/${friendId}`, { method: 'DELETE' });
	}

	// Groups
	async getGroups(): Promise<Group[]> {
		return this.request('/groups');
	}

	async createGroup(name: string, description?: string): Promise<Group> {
		return this.request('/groups', {
			method: 'POST',
			body: { name, description },
		});
	}

	async joinGroup(inviteCode: string): Promise<{ message: string; group_name: string }> {
		return this.request(`/groups/join/${inviteCode}`, { method: 'POST' });
	}

	async leaveGroup(groupId: number): Promise<{ message: string }> {
		return this.request(`/groups/${groupId}/leave`, { method: 'DELETE' });
	}

	async getGroupMembers(groupId: number): Promise<GroupMember[]> {
		return this.request(`/groups/${groupId}/members`);
	}
}

export const api = new ApiClient(API_BASE);

// Types
export interface User {
	id: number;
	telegram_id: number;
	username: string | null;
	first_name: string | null;
	level: number;
	experience: number;
	streak_days: number;
	last_workout_date: string | null;
	total_workouts: number;
	total_reps: number;
	total_time_seconds: number;
	notifications_enabled: boolean;
	created_at: string;
}

export interface UserUpdate {
	notifications_enabled?: boolean;
	reminder_time?: string;
}

export interface Exercise {
	id: number;
	name: string;
	category: string;
	metric_type: 'reps' | 'time';
	description: string | null;
	icon: string;
	difficulty: number;
	exp_per_rep: number;
	exp_per_second: number;
}

export interface Workout {
	id: number;
	started_at: string;
	completed_at: string | null;
	notes: string | null;
	total_exp: number;
	exercises: WorkoutExercise[];
}

export interface WorkoutExercise {
	id: number;
	exercise_id: number;
	exercise?: Exercise;
	sets: number;
	reps: number | null;
	duration_seconds: number | null;
	is_personal_record: boolean;
	exp_earned: number;
}

export interface WorkoutExerciseCreate {
	exercise_id: number;
	sets?: number;
	reps?: number;
	duration_seconds?: number;
}

export interface WorkoutResult {
	workout: Workout;
	total_exp: number;
	level_up: boolean;
	new_level: number;
	new_achievements: string[];
}

export interface Goal {
	id: number;
	goal_type: string;
	title: string;
	target_value: number;
	current_value: number;
	deadline: string | null;
	is_active: boolean;
	progress_percent: number;
}

export interface GoalCreate {
	goal_type: string;
	title: string;
	target_value: number;
	exercise_id?: number;
	deadline?: string;
}

export interface Achievement {
	id: string;
	name: string;
	description: string;
	icon: string;
	category: string;
	threshold: number;
	exp_reward: number;
}

export interface AchievementWithStatus extends Achievement {
	is_unlocked: boolean;
	unlocked_at: string | null;
}

export interface UserAchievement {
	achievement_id: string;
	unlocked_at: string;
	achievement: Achievement;
}

export interface LeaderboardEntry {
	rank: number;
	user_id: number;
	username: string | null;
	first_name: string | null;
	level: number;
	experience: number;
	streak_days: number;
	is_current_user: boolean;
}

export interface Friend {
	id: number;
	user_id: number;
	username: string | null;
	first_name: string | null;
	level: number;
	experience: number;
	streak_days: number;
	total_workouts: number;
	status: string;
}

export interface Group {
	id: number;
	name: string;
	description: string | null;
	invite_code: string;
	member_count: number;
	is_owner: boolean;
	role: string;
}

export interface GroupMember {
	id: number;
	user_id: number;
	username: string | null;
	first_name: string | null;
	level: number;
	experience: number;
	streak_days: number;
	total_workouts: number;
	role: string;
	joined_at: string;
}
