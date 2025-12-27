import type { WorkoutSession, Exercise, WorkoutExercise } from '$lib/types';
import { api } from '$lib/api/client';
import { userStore } from './user';
import { telegram } from './telegram';

// Workout state using Svelte 5 runes
class WorkoutStore {
	session = $state<WorkoutSession | null>(null);
	currentExercise = $state<Exercise | null>(null);
	isActive = $state(false);
	isLoading = $state(false);
	error = $state<string | null>(null);

	// Timer state
	timerSeconds = $state(0);
	isTimerRunning = $state(false);
	private timerInterval: ReturnType<typeof setInterval> | null = null;

	// Current set
	currentReps = $state(0);

	get totalXp() {
		return this.session?.total_xp_earned ?? 0;
	}

	get totalCoins() {
		return this.session?.total_coins_earned ?? 0;
	}

	get totalReps() {
		return this.session?.total_reps ?? 0;
	}

	get exerciseCount() {
		return this.session?.exercises?.length ?? 0;
	}

	get duration() {
		return this.timerSeconds;
	}

	get formattedDuration() {
		const minutes = Math.floor(this.timerSeconds / 60);
		const seconds = this.timerSeconds % 60;
		return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
	}

	async startWorkout() {
		this.isLoading = true;
		this.error = null;

		try {
			this.session = await api.startWorkout();
			this.isActive = true;
			this.startTimer();
			telegram.hapticNotification('success');
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to start workout';
			telegram.hapticNotification('error');
		} finally {
			this.isLoading = false;
		}
	}

	selectExercise(exercise: Exercise) {
		this.currentExercise = exercise;
		this.currentReps = 0;
		telegram.hapticSelection();
	}

	setReps(reps: number) {
		this.currentReps = Math.max(0, reps);
	}

	incrementReps() {
		this.currentReps++;
		telegram.hapticImpact('light');
	}

	decrementReps() {
		if (this.currentReps > 0) {
			this.currentReps--;
			telegram.hapticImpact('light');
		}
	}

	async addSet() {
		if (!this.session || !this.currentExercise || this.currentReps <= 0) return;

		this.isLoading = true;
		try {
			this.session = await api.addExerciseToWorkout(
				this.session.id,
				this.currentExercise.slug,
				this.currentReps,
				1 // sets
			);

			// Update user stats
			userStore.addXp(this.session.total_xp_earned);
			userStore.addCoins(this.session.total_coins_earned);

			// Reset for next set
			this.currentReps = 0;
			telegram.hapticNotification('success');
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to add set';
			telegram.hapticNotification('error');
		} finally {
			this.isLoading = false;
		}
	}

	async completeWorkout(): Promise<WorkoutSession | null> {
		if (!this.session) return null;

		this.isLoading = true;
		try {
			this.stopTimer();
			const completedSession = await api.completeWorkout(this.session.id);
			this.session = completedSession;
			this.isActive = false;
			telegram.hapticNotification('success');
			return completedSession;
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to complete workout';
			telegram.hapticNotification('error');
			return null;
		} finally {
			this.isLoading = false;
		}
	}

	cancelWorkout() {
		this.stopTimer();
		this.session = null;
		this.currentExercise = null;
		this.currentReps = 0;
		this.isActive = false;
		this.timerSeconds = 0;
	}

	private startTimer() {
		this.isTimerRunning = true;
		this.timerSeconds = 0;
		this.timerInterval = setInterval(() => {
			this.timerSeconds++;
		}, 1000);
	}

	private stopTimer() {
		this.isTimerRunning = false;
		if (this.timerInterval) {
			clearInterval(this.timerInterval);
			this.timerInterval = null;
		}
	}

	// Rest timer for between sets
	restTimerSeconds = $state(0);
	isRestTimerRunning = $state(false);
	private restTimerInterval: ReturnType<typeof setInterval> | null = null;

	startRestTimer(seconds: number = 60) {
		this.restTimerSeconds = seconds;
		this.isRestTimerRunning = true;
		this.restTimerInterval = setInterval(() => {
			if (this.restTimerSeconds > 0) {
				this.restTimerSeconds--;
			} else {
				this.stopRestTimer();
				telegram.hapticNotification('warning');
			}
		}, 1000);
	}

	stopRestTimer() {
		this.isRestTimerRunning = false;
		if (this.restTimerInterval) {
			clearInterval(this.restTimerInterval);
			this.restTimerInterval = null;
		}
	}

	get formattedRestTimer() {
		const minutes = Math.floor(this.restTimerSeconds / 60);
		const seconds = this.restTimerSeconds % 60;
		return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
	}
}

export const workoutStore = new WorkoutStore();
