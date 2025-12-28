import type { WorkoutSession, Exercise, WorkoutExercise } from '$lib/types';
import { api } from '$lib/api/client';
import { userStore } from './user.svelte';
import { telegram } from './telegram.svelte';

// Set data for each exercise
interface ExerciseSetData {
	exercise: Exercise | null;
	exerciseId: number;
	exerciseSlug: string;
	exerciseName: string;
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

	// Load active workout from server (if any)
	async loadActiveWorkout() {
		try {
			const response = await fetch('/bodyweight/api/workouts/active', {
				headers: {
					'Authorization': `tma ${api['initData'] || ''}`
				}
			});
			if (response.ok) {
				const workout = await response.json() as WorkoutSession | null;
				if (workout) {
					this.session = workout;
					this.isActive = true;
					this.startTimer();

					// Initialize exercise data from workout exercises
					const newData = new Map<number, ExerciseSetData>();
					for (const we of workout.exercises) {
						newData.set(we.exercise_id, {
							exercise: null,
							exerciseId: we.exercise_id,
							exerciseSlug: we.exercise_slug,
							exerciseName: we.exercise_name_ru,
							sets: [], // We don't know individual sets, only totals
							inputReps: 10
						});
					}
					this.exerciseData = newData;
				}
			}
		} catch (err) {
			console.error('Failed to load active workout:', err);
		}
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
					exerciseId: exercise.id,
					exerciseSlug: exercise.slug,
					exerciseName: exercise.name_ru,
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
			const newData = new Map(this.exerciseData);
			newData.set(exerciseId, { ...data, inputReps: Math.max(1, reps) });
			this.exerciseData = newData;
		}
	}

	incrementReps(exerciseId: number) {
		const data = this.exerciseData.get(exerciseId);
		if (data) {
			const newData = new Map(this.exerciseData);
			newData.set(exerciseId, { ...data, inputReps: data.inputReps + 1 });
			this.exerciseData = newData;
			telegram.hapticImpact('light');
		}
	}

	decrementReps(exerciseId: number) {
		const data = this.exerciseData.get(exerciseId);
		if (data && data.inputReps > 1) {
			const newData = new Map(this.exerciseData);
			newData.set(exerciseId, { ...data, inputReps: data.inputReps - 1 });
			this.exerciseData = newData;
			telegram.hapticImpact('light');
		}
	}

	getExerciseData(exerciseId: number): ExerciseSetData | undefined {
		return this.exerciseData.get(exerciseId);
	}

	// Add set for an exercise
	async addSet(exerciseId: number) {
		if (!this.session) {
			console.error('[addSet] No active session');
			return;
		}

		const data = this.exerciseData.get(exerciseId);
		if (!data) {
			console.error('[addSet] No data for exercise:', exerciseId);
			return;
		}
		if (data.inputReps <= 0) {
			console.error('[addSet] Invalid reps:', data.inputReps);
			return;
		}

		// Capture the reps value before any async operations
		const repsToAdd = data.inputReps;
		console.log('[addSet] Adding set:', {
			sessionId: this.session.id,
			exerciseId,
			slug: data.exerciseSlug,
			reps: repsToAdd
		});

		this.isLoading = true;
		try {
			const result = await api.addExerciseToWorkout(
				this.session.id,
				data.exerciseSlug,
				repsToAdd,
				1
			);
			console.log('[addSet] API response:', result);
			this.session = result;

			// Add reps to local sets array - create new object for reactivity
			const newData = new Map(this.exerciseData);
			newData.set(exerciseId, { ...data, sets: [...data.sets, repsToAdd] });
			this.exerciseData = newData;

			telegram.hapticNotification('success');
		} catch (err) {
			console.error('[addSet] Error:', err);
			this.error = err instanceof Error ? err.message : 'Failed to add set';
			telegram.hapticNotification('error');
		} finally {
			this.isLoading = false;
		}
	}

	async completeWorkout(): Promise<WorkoutSession | null> {
		if (!this.session) {
			console.error('[completeWorkout] No active session');
			return null;
		}

		console.log('[completeWorkout] Starting completion for session:', this.session.id);
		console.log('[completeWorkout] Session exercises:', this.session.exercises);

		this.isLoading = true;
		try {
			this.stopTimer();
			const response = await api.completeWorkout(this.session.id);
			console.log('[completeWorkout] API response:', response);

			// Update user stats from the completed workout
			userStore.addXp(response.workout.total_xp_earned);
			userStore.addCoins(response.workout.total_coins_earned);

			// Handle level up
			if (response.level_up && response.new_level) {
				console.log(`Level up! New level: ${response.new_level}`);
			}

			this.session = response.workout;
			this.isActive = false;
			telegram.hapticNotification('success');
			return response.workout;
		} catch (err) {
			console.error('[completeWorkout] Error:', err);
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
