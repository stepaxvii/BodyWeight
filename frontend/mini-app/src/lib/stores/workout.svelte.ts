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
	isTimed: boolean; // True for time-based exercises
	sets: number[]; // array of reps per set (or seconds for timed exercises)
	inputReps: number; // current input value (reps or seconds)
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
	isPaused = $state(false);
	private timerInterval: ReturnType<typeof setInterval> | null = null;

	// Computed values
	get selectedCount() {
		return this.selectedExercises.length;
	}

	get totalXp() {
		// If workout completed, use session total from backend
		if (this.session?.total_xp_earned) {
			return this.session.total_xp_earned;
		}
		// During workout: return 0 or estimated value
		// NOTE: Accurate XP calculation requires backend data (streak, isFirstToday)
		// We don't calculate locally to avoid showing incorrect values
		// Frontend will show XP only after workout completion
		return 0;
	}

	/**
	 * Get estimated XP for preview (approximate, not accurate)
	 * Uses simplified formula without streak and first workout bonuses
	 * Only for display purposes - actual XP comes from backend
	 * NOTE: This getter is not reactive in Svelte 5. Use $derived in components instead.
	 */
	get estimatedXp(): number {
		if (this.session?.total_xp_earned) {
			return this.session.total_xp_earned;
		}
		// Simplified estimate (without streak/first bonus) for preview only
		// Only count exercises that have at least one set
		let total = 0;
		this.exerciseData.forEach(data => {
			// Must have exercise data AND at least one set
			if (!data.exercise || data.sets.length === 0) {
				return;
			}
			
			const baseXp = data.exercise.base_xp;
			const difficulty = data.exercise.difficulty || 1;
			const difficultyMult = 1 + (difficulty - 1) * 0.25;

			// For timed exercises, convert seconds to "rep equivalent" (10 sec = 1 rep)
			// For rep-based exercises, use reps directly
			let totalValue: number;
			if (data.isTimed) {
				// Sum all seconds and convert to rep equivalent
				const totalSeconds = data.sets.reduce((sum, seconds) => sum + seconds, 0);
				totalValue = Math.max(1, Math.floor(totalSeconds / 10)); // 10 sec = 1 rep equivalent
			} else {
				// Sum all reps
				totalValue = data.sets.reduce((sum, reps) => sum + reps, 0);
			}
			
			// Volume multiplier based on total value
			let volumeMult: number;
			if (totalValue <= 20) {
				volumeMult = 1 + totalValue * 0.02;
			} else {
				volumeMult = 1.4 + (totalValue - 20) * 0.01;
			}
			
			total += baseXp * difficultyMult * volumeMult;
		});
		return Math.floor(total);
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
							isTimed: we.is_timed ?? false,
							sets: [], // We don't know individual sets, only totals
							inputReps: we.is_timed ? 30 : 10 // Default 30 sec for timed, 10 reps otherwise
						});
					}
					this.exerciseData = newData;
				}
			}
		} catch (err) {
			console.error('Failed to load active workout:', err);
		}
	}

	// Helper to check if exercise is time-based
	private isTimedExercise(exercise: Exercise): boolean {
		// Use is_timed flag from backend if available
		if (exercise.is_timed !== undefined) {
			return exercise.is_timed;
		}
		// Fallback to category check
		return exercise.category_slug === 'static' || exercise.category_slug === 'stretch';
	}

	// Workout lifecycle - now purely local, no backend call
	async startWorkout() {
		if (this.selectedExercises.length === 0) return;

		this.isActive = true;

		// Initialize exercise data for each selected exercise
		const newData = new Map<number, ExerciseSetData>();
		for (const exercise of this.selectedExercises) {
			const isTimed = this.isTimedExercise(exercise);
			newData.set(exercise.id, {
				exercise,
				exerciseId: exercise.id,
				exerciseSlug: exercise.slug,
				exerciseName: exercise.name_ru,
				isTimed,
				sets: [],
				inputReps: isTimed ? 30 : 10 // default 30 sec for timed, 10 reps otherwise
			});
		}
		this.exerciseData = newData;

		this.startTimer();
		telegram.hapticNotification('success');
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

	// Add set for an exercise - now purely local, no API call
	addSet(exerciseId: number) {
		const data = this.exerciseData.get(exerciseId);
		if (!data) {
			console.error('[addSet] No data for exercise:', exerciseId);
			return;
		}
		if (data.inputReps <= 0) {
			console.error('[addSet] Invalid value:', data.inputReps);
			return;
		}

		const valueToAdd = data.inputReps;

		// Add value to local sets array - create new object for reactivity
		const newData = new Map(this.exerciseData);
		newData.set(exerciseId, { ...data, sets: [...data.sets, valueToAdd] });
		this.exerciseData = newData;

		telegram.hapticNotification('success');
	}

	async completeWorkout(): Promise<WorkoutSession | null> {
		// Check we have exercise data
		if (this.exerciseData.size === 0) {
			console.error('[completeWorkout] No exercises');
			return null;
		}

		// Build exercises array for API
		const exercises: Array<{
			exercise_slug: string;
			sets: number[];
			is_timed: boolean;
		}> = [];

		this.exerciseData.forEach((data: ExerciseSetData) => {
			if (data.sets.length > 0) {
				exercises.push({
					exercise_slug: data.exerciseSlug,
					sets: data.sets,
					is_timed: data.isTimed
				});
			}
		});

		if (exercises.length === 0) {
			console.error('[completeWorkout] No sets recorded');
			return null;
		}

		console.log('[completeWorkout] Submitting workout:', {
			duration: this.timerSeconds,
			exercises
		});

		this.isLoading = true;
		try {
			this.stopTimer();

			// Use new simplified API
			const response = await api.submitWorkout({
				duration_seconds: this.timerSeconds,
				exercises
			});
			console.log('[completeWorkout] API response:', response);

			// Reload user data from server to get updated XP, level, coins, streak
			await userStore.loadUser();

			// Handle level up notification
			if (response.level_up && response.new_level) {
				console.log(`Level up! New level: ${response.new_level}`);
			}

			this.session = response.workout;
			this.isActive = false;
			this.selectedExercises = [];
			this.exerciseData = new Map();
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
		this.isPaused = false;
		this.timerSeconds = 0;
		this.timerInterval = setInterval(() => {
			this.timerSeconds++;
		}, 1000);
	}

	private stopTimer() {
		this.isTimerRunning = false;
		this.isPaused = false;
		if (this.timerInterval) {
			clearInterval(this.timerInterval);
			this.timerInterval = null;
		}
	}

	// Pause timer when leaving page
	pauseTimer() {
		if (this.isTimerRunning && !this.isPaused) {
			this.isPaused = true;
			if (this.timerInterval) {
				clearInterval(this.timerInterval);
				this.timerInterval = null;
			}
		}
	}

	// Resume timer when returning to page
	resumeTimer() {
		if (this.isActive && this.isPaused) {
			this.isPaused = false;
			this.isTimerRunning = true;
			this.timerInterval = setInterval(() => {
				this.timerSeconds++;
			}, 1000);
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
