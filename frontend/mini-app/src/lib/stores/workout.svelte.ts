import type { WorkoutSession, Exercise } from '$lib/types';
import { api } from '$lib/api/client';
import { userStore } from './user.svelte';
import { telegram } from './telegram.svelte';

// Set data for each exercise
interface ExerciseSetData {
	exercise: Exercise;
	sets: number[]; // array of reps per set
	inputReps: number; // current input value
}

// Workout state using Svelte 5 runes
class WorkoutStore {
	session = $state<WorkoutSession | null>(null);
	isActive = $state(false);
	isLoading = $state(false);
	error = $state<string | null>(null);

	// Selected exercises for the workout (before starting)
	selectedExercises = $state<Exercise[]>([]);

	// Exercise sets data during workout
	exerciseData = $state<Map<number, ExerciseSetData>>(new Map());

	// Timer state
	timerSeconds = $state(0);
	isTimerRunning = $state(false);
	private timerInterval: ReturnType<typeof setInterval> | null = null;

	// Computed values
	get selectedCount() {
		return this.selectedExercises.length;
	}

	get totalXp() {
		return this.session?.total_xp_earned ?? 0;
	}

	get totalCoins() {
		return this.session?.total_coins_earned ?? 0;
	}

	get totalReps() {
		let total = 0;
		this.exerciseData.forEach(data => {
			total += data.sets.reduce((sum, reps) => sum + reps, 0);
		});
		return total;
	}

	get totalSets() {
		let total = 0;
		this.exerciseData.forEach(data => {
			total += data.sets.length;
		});
		return total;
	}

	get formattedDuration() {
		const minutes = Math.floor(this.timerSeconds / 60);
		const seconds = this.timerSeconds % 60;
		return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
	}

	// Selection methods (before workout starts)
	toggleExerciseSelection(exercise: Exercise) {
		const index = this.selectedExercises.findIndex(e => e.id === exercise.id);
		if (index >= 0) {
			this.selectedExercises = this.selectedExercises.filter(e => e.id !== exercise.id);
		} else {
			this.selectedExercises = [...this.selectedExercises, exercise];
		}
		telegram.hapticSelection();
	}

	isExerciseSelected(exerciseId: number): boolean {
		return this.selectedExercises.some(e => e.id === exerciseId);
	}

	clearSelection() {
		this.selectedExercises = [];
	}

	// Workout lifecycle
	async startWorkout() {
		if (this.selectedExercises.length === 0) return;

		this.isLoading = true;
		this.error = null;

		try {
			this.session = await api.startWorkout();
			this.isActive = true;

			// Initialize exercise data for each selected exercise
			const newData = new Map<number, ExerciseSetData>();
			for (const exercise of this.selectedExercises) {
				newData.set(exercise.id, {
					exercise,
					sets: [],
					inputReps: 10 // default value
				});
			}
			this.exerciseData = newData;

			this.startTimer();
			telegram.hapticNotification('success');
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to start workout';
			telegram.hapticNotification('error');
		} finally {
			this.isLoading = false;
		}
	}

	// Set input methods
	setInputReps(exerciseId: number, reps: number) {
		const data = this.exerciseData.get(exerciseId);
		if (data) {
			data.inputReps = Math.max(1, reps);
			this.exerciseData = new Map(this.exerciseData);
		}
	}

	incrementReps(exerciseId: number) {
		const data = this.exerciseData.get(exerciseId);
		if (data) {
			data.inputReps++;
			this.exerciseData = new Map(this.exerciseData);
			telegram.hapticImpact('light');
		}
	}

	decrementReps(exerciseId: number) {
		const data = this.exerciseData.get(exerciseId);
		if (data && data.inputReps > 1) {
			data.inputReps--;
			this.exerciseData = new Map(this.exerciseData);
			telegram.hapticImpact('light');
		}
	}

	getExerciseData(exerciseId: number): ExerciseSetData | undefined {
		return this.exerciseData.get(exerciseId);
	}

	// Add set for an exercise
	async addSet(exerciseId: number) {
		if (!this.session) return;

		const data = this.exerciseData.get(exerciseId);
		if (!data || data.inputReps <= 0) return;

		this.isLoading = true;
		try {
			this.session = await api.addExerciseToWorkout(
				this.session.id,
				data.exercise.slug,
				data.inputReps,
				1
			);

			// Add reps to local sets array
			data.sets = [...data.sets, data.inputReps];
			this.exerciseData = new Map(this.exerciseData);

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

			// Update user stats
			userStore.addXp(completedSession.total_xp_earned);
			userStore.addCoins(completedSession.total_coins_earned);

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
		this.selectedExercises = [];
		this.exerciseData = new Map();
		this.isActive = false;
		this.timerSeconds = 0;
	}

	reset() {
		this.cancelWorkout();
		this.error = null;
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
