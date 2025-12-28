<script lang="ts">
	import { PixelButton, PixelCard, PixelIcon, PixelProgress } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import type { Routine, RoutineExercise, Exercise } from '$lib/types';
	import { onMount, onDestroy } from 'svelte';

	interface Props {
		routine: Routine;
		onclose?: () => void;
		oncomplete?: (xp: number, coins: number) => void;
	}

	let { routine, onclose, oncomplete }: Props = $props();

	// All exercises data for descriptions
	let allExercises = $state<Exercise[]>([]);

	// Current step in the routine
	let currentStep = $state(0);
	let isStarted = $state(false);
	let isPaused = $state(false);
	let isCompleted = $state(false);
	let isSubmitting = $state(false);

	// Timer state
	let timerSeconds = $state(0);
	let exerciseTimerSeconds = $state(0);
	let timerInterval: ReturnType<typeof setInterval> | null = null;
	let isExerciseTimerStarted = $state(false); // User must start timer manually for time-based exercises

	// Workout session
	let workoutSessionId = $state<number | null>(null);
	let totalXpEarned = $state(0);
	let totalCoinsEarned = $state(0);

	const currentExercise = $derived(routine.exercises[currentStep]);
	const exerciseData = $derived(allExercises.find(e => e.slug === currentExercise?.slug));
	const progress = $derived(((currentStep + 1) / routine.exercises.length) * 100);
	const isTimeBased = $derived(!!currentExercise?.duration);
	const targetValue = $derived(currentExercise?.duration || currentExercise?.reps || 0);

	// Format timer display
	function formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
	}

	const formattedTotalTime = $derived(formatTime(timerSeconds));
	const formattedExerciseTime = $derived(formatTime(exerciseTimerSeconds));

	onMount(async () => {
		allExercises = await api.getExercises();
	});

	onDestroy(() => {
		stopTimer();
	});

	function startTimer() {
		if (timerInterval) return;
		timerInterval = setInterval(() => {
			if (!isPaused) {
				timerSeconds++;
				// Only count down exercise timer if user has started it
				if (isTimeBased && isExerciseTimerStarted && exerciseTimerSeconds > 0) {
					exerciseTimerSeconds--;
					if (exerciseTimerSeconds === 0) {
						telegram.hapticNotification('success');
					}
				}
			}
		}, 1000);
	}

	function startExerciseTimer() {
		isExerciseTimerStarted = true;
		telegram.hapticImpact('medium');
	}

	function stopTimer() {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
	}

	async function startRoutine() {
		isStarted = true;
		telegram.hapticImpact('medium');

		// Start the total workout timer immediately
		startTimer();
		resetExerciseTimer();

		try {
			// Start a workout session on the server
			const session = await api.startWorkout();
			workoutSessionId = session.id;
		} catch (err) {
			console.error('Failed to start routine:', err);
			telegram.hapticNotification('error');
		}
	}

	function resetExerciseTimer() {
		isExerciseTimerStarted = false; // Reset - user must start timer again for next exercise
		if (isTimeBased) {
			exerciseTimerSeconds = currentExercise?.duration || 0;
		} else {
			exerciseTimerSeconds = 0;
		}
	}

	function togglePause() {
		isPaused = !isPaused;
		telegram.hapticImpact('light');
	}

	async function completeExercise() {
		if (!workoutSessionId || !currentExercise) return;

		telegram.hapticImpact('medium');

		try {
			// Record the exercise
			const value = isTimeBased
				? Math.ceil((currentExercise.duration || 0) / 10)
				: (currentExercise.reps || 0);

			const result = await api.addExerciseToWorkout(
				workoutSessionId,
				currentExercise.slug,
				value,
				1
			);

			totalXpEarned = result.total_xp_earned;
			totalCoinsEarned = result.total_coins_earned;

			// Move to next exercise or complete
			if (currentStep < routine.exercises.length - 1) {
				currentStep++;
				resetExerciseTimer();
			} else {
				await finishRoutine();
			}
		} catch (err) {
			console.error('Failed to record exercise:', err);
			telegram.hapticNotification('error');
		}
	}

	async function finishRoutine() {
		if (!workoutSessionId) return;

		isSubmitting = true;
		try {
			const completed = await api.completeWorkout(workoutSessionId);
			stopTimer();
			isCompleted = true;
			totalXpEarned = completed.total_xp_earned;
			totalCoinsEarned = completed.total_coins_earned;

			// Update user stats
			userStore.addXp(completed.total_xp_earned);
			userStore.addCoins(completed.total_coins_earned);

			telegram.hapticNotification('success');
		} catch (err) {
			console.error('Failed to complete routine:', err);
			telegram.hapticNotification('error');
		} finally {
			isSubmitting = false;
		}
	}

	function handleClose() {
		stopTimer();
		if (isCompleted) {
			oncomplete?.(totalXpEarned, totalCoinsEarned);
		}
		onclose?.();
	}

	function skipExercise() {
		telegram.hapticImpact('light');
		if (currentStep < routine.exercises.length - 1) {
			currentStep++;
			resetExerciseTimer();
		} else {
			finishRoutine();
		}
	}
</script>

<div class="routine-player">
	{#if !isStarted}
		<!-- Pre-start screen -->
		<div class="pre-start">
			<div class="routine-header">
				<button class="close-btn" onclick={handleClose}>
					<PixelIcon name="close" />
				</button>
				<h2 class="routine-title">{routine.name}</h2>
			</div>

			<PixelCard variant="accent" padding="lg">
				<div class="routine-info">
					<p class="routine-description">{routine.description}</p>
					<div class="routine-stats">
						<div class="stat">
							<PixelIcon name="timer" color="var(--text-secondary)" />
							<span>{routine.duration_minutes} мин</span>
						</div>
						<div class="stat">
							<PixelIcon name="play" color="var(--text-secondary)" />
							<span>{routine.exercises.length} упр.</span>
						</div>
					</div>
				</div>
			</PixelCard>

			<section class="exercise-preview">
				<h3 class="section-title">Упражнения</h3>
				<div class="exercise-list">
					{#each routine.exercises as ex, i}
						<div class="exercise-preview-item">
							<span class="exercise-number">{i + 1}</span>
							<span class="exercise-name">{allExercises.find(e => e.slug === ex.slug)?.name_ru || ex.slug}</span>
							<span class="exercise-target">
								{#if ex.duration}
									{ex.duration} сек
								{:else if ex.reps}
									{ex.reps} повт.
								{/if}
							</span>
						</div>
					{/each}
				</div>
			</section>

			<div class="start-section">
				<PixelButton variant="primary" size="lg" fullWidth onclick={startRoutine}>
					<PixelIcon name="play" />
					Начать
				</PixelButton>
			</div>
		</div>

	{:else if isCompleted}
		<!-- Completion screen -->
		<div class="completion-screen">
			<div class="completion-header">
				<PixelIcon name="trophy" size="xl" color="var(--pixel-yellow)" />
				<h2 class="completion-title">Отлично!</h2>
				<p class="completion-subtitle">Комплекс выполнен</p>
			</div>

			<PixelCard variant="accent" padding="lg">
				<div class="completion-stats">
					<div class="completion-stat">
						<span class="stat-value">{formattedTotalTime}</span>
						<span class="stat-label">Время</span>
					</div>
					<div class="completion-stat">
						<span class="stat-value text-green">+{totalXpEarned}</span>
						<span class="stat-label">XP</span>
					</div>
					<div class="completion-stat">
						<span class="stat-value text-yellow">+{totalCoinsEarned}</span>
						<span class="stat-label">Монеты</span>
					</div>
				</div>
			</PixelCard>

			<div class="completion-actions">
				<PixelButton variant="success" size="lg" fullWidth onclick={handleClose}>
					<PixelIcon name="check" />
					Готово
				</PixelButton>
			</div>
		</div>

	{:else}
		<!-- Active exercise screen -->
		<div class="active-exercise">
			<!-- Header with progress -->
			<div class="player-header">
				<button class="close-btn" onclick={handleClose}>
					<PixelIcon name="close" />
				</button>
				<div class="progress-info">
					<span class="step-counter">{currentStep + 1} / {routine.exercises.length}</span>
					<span class="total-time">{formattedTotalTime}</span>
				</div>
			</div>

			<!-- Progress bar -->
			<div class="progress-section">
				<PixelProgress value={currentStep + 1} max={routine.exercises.length} variant="xp" size="sm" />
			</div>

			<!-- Current exercise -->
			<div class="exercise-display">
				<PixelCard variant="accent" padding="lg">
					<div class="exercise-content">
						<h3 class="current-exercise-name">{exerciseData?.name_ru || currentExercise?.slug}</h3>

						{#if exerciseData?.description_ru}
							<p class="exercise-description">{exerciseData.description_ru}</p>
						{/if}

						<div class="target-display">
							{#if isTimeBased}
								<div class="timer-circle" class:complete={exerciseTimerSeconds === 0} class:waiting={!isExerciseTimerStarted}>
									<span class="timer-value">{formattedExerciseTime}</span>
									<span class="timer-label">
										{#if !isExerciseTimerStarted}
											нажмите старт
										{:else if exerciseTimerSeconds === 0}
											готово!
										{:else}
											осталось
										{/if}
									</span>
								</div>
							{:else}
								<div class="reps-display">
									<span class="reps-value">{targetValue}</span>
									<span class="reps-label">повторений</span>
								</div>
							{/if}
						</div>
					</div>
				</PixelCard>
			</div>

			<!-- Next exercise preview -->
			{#if currentStep < routine.exercises.length - 1}
				{@const nextEx = routine.exercises[currentStep + 1]}
				{@const nextExData = allExercises.find(e => e.slug === nextEx.slug)}
				<div class="next-preview">
					<span class="next-label">Далее:</span>
					<span class="next-name">{nextExData?.name_ru || nextEx.slug}</span>
				</div>
			{/if}

			<!-- Controls -->
			<div class="player-controls">
				<div class="control-row">
					<PixelButton variant="ghost" onclick={skipExercise}>
						Пропустить
					</PixelButton>
					{#if isTimeBased && !isExerciseTimerStarted}
						<!-- Show Start Timer button for time-based exercises -->
						<PixelButton variant="primary" size="lg" onclick={startExerciseTimer}>
							<PixelIcon name="play" />
							Старт
						</PixelButton>
					{:else if isTimeBased && exerciseTimerSeconds > 0}
						<!-- Show Pause button while timer is running -->
						<PixelButton variant="secondary" size="lg" onclick={togglePause}>
							<PixelIcon name={isPaused ? 'play' : 'pause'} />
						</PixelButton>
					{:else}
						<!-- Show Done button for reps or when timer finished -->
						<PixelButton
							variant="success"
							size="lg"
							onclick={completeExercise}
						>
							<PixelIcon name="check" />
							Готово
						</PixelButton>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.routine-player {
		position: fixed;
		inset: 0;
		background: var(--pixel-bg);
		z-index: 1000;
		display: flex;
		flex-direction: column;
		overflow-y: auto;
	}

	/* Pre-start screen */
	.pre-start {
		padding: var(--spacing-md);
		display: flex;
		flex-direction: column;
		min-height: 100%;
	}

	.routine-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		margin-bottom: var(--spacing-lg);
	}

	.close-btn {
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-xs);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-btn:hover {
		border-color: var(--pixel-accent);
	}

	.routine-title {
		font-size: var(--font-size-lg);
		margin: 0;
	}

	.routine-info {
		text-align: center;
	}

	.routine-description {
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		margin: 0 0 var(--spacing-md) 0;
		line-height: 1.4;
	}

	.routine-stats {
		display: flex;
		justify-content: center;
		gap: var(--spacing-lg);
	}

	.stat {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.exercise-preview {
		flex: 1;
		margin-top: var(--spacing-lg);
	}

	.section-title {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin-bottom: var(--spacing-sm);
		color: var(--text-secondary);
	}

	.exercise-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.exercise-preview-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		font-size: var(--font-size-xs);
	}

	.exercise-number {
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
		color: var(--text-secondary);
	}

	.exercise-name {
		flex: 1;
	}

	.exercise-target {
		color: var(--pixel-green);
	}

	.start-section {
		margin-top: var(--spacing-xl);
		padding-bottom: var(--spacing-lg);
	}

	/* Active exercise screen */
	.active-exercise {
		display: flex;
		flex-direction: column;
		min-height: 100%;
		padding: var(--spacing-md);
	}

	.player-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-md);
	}

	.progress-info {
		display: flex;
		gap: var(--spacing-md);
		font-size: var(--font-size-sm);
	}

	.step-counter {
		color: var(--pixel-accent);
	}

	.total-time {
		color: var(--text-secondary);
	}

	.progress-section {
		margin-bottom: var(--spacing-lg);
	}

	.exercise-display {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.exercise-content {
		text-align: center;
		width: 100%;
	}

	.current-exercise-name {
		font-size: var(--font-size-lg);
		margin: 0 0 var(--spacing-sm) 0;
		color: var(--pixel-accent);
	}

	.exercise-description {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		margin: 0 0 var(--spacing-lg) 0;
		line-height: 1.4;
	}

	.target-display {
		margin-top: var(--spacing-lg);
	}

	.timer-circle {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 150px;
		height: 150px;
		margin: 0 auto;
		border: 4px solid var(--pixel-accent);
		border-radius: 50%;
		background: var(--pixel-bg-dark);
	}

	.timer-circle.complete {
		border-color: var(--pixel-green);
	}

	.timer-circle.waiting {
		border-color: var(--text-secondary);
	}

	.timer-circle.waiting .timer-value {
		color: var(--text-secondary);
	}

	.timer-value {
		font-size: var(--font-size-2xl);
		color: var(--pixel-accent);
	}

	.timer-circle.complete .timer-value {
		color: var(--pixel-green);
	}

	.timer-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.reps-display {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.reps-value {
		font-size: 64px;
		color: var(--pixel-accent);
		line-height: 1;
	}

	.reps-label {
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		text-transform: uppercase;
		margin-top: var(--spacing-xs);
	}

	.next-preview {
		display: flex;
		justify-content: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.next-name {
		color: var(--text-primary);
	}

	.player-controls {
		margin-top: auto;
		padding: var(--spacing-md) 0;
	}

	.control-row {
		display: flex;
		gap: var(--spacing-sm);
		align-items: center;
		justify-content: center;
	}

	.control-row > :global(:last-child) {
		flex: 1;
	}

	/* Completion screen */
	.completion-screen {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100%;
		padding: var(--spacing-lg);
		text-align: center;
	}

	.completion-header {
		margin-bottom: var(--spacing-xl);
	}

	.completion-title {
		font-size: var(--font-size-xl);
		margin: var(--spacing-md) 0 0 0;
		color: var(--pixel-yellow);
	}

	.completion-subtitle {
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		margin: var(--spacing-xs) 0 0 0;
	}

	.completion-stats {
		display: flex;
		justify-content: space-around;
		width: 100%;
	}

	.completion-stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.stat-value {
		font-size: var(--font-size-lg);
	}

	.stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.completion-actions {
		margin-top: var(--spacing-xl);
		width: 100%;
	}

	.text-green { color: var(--pixel-green); }
	.text-yellow { color: var(--pixel-yellow); }
</style>
