<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { api, type Exercise, type Workout, type WorkoutExercise, type WorkoutResult } from '$lib/api/client';
	import { user } from '$lib/stores/user';

	let exercises: Exercise[] = $state([]);
	let currentWorkout: Workout | null = $state(null);
	let workoutExercises: WorkoutExercise[] = $state([]);
	let selectedCategory: string = $state('all');
	let selectedExercise: Exercise | null = $state(null);
	let isLoading = $state(true);
	let showResult = $state(false);
	let workoutResult: WorkoutResult | null = $state(null);

	// Exercise input
	let inputReps = $state(10);
	let inputSets = $state(1);
	let inputDuration = $state(30);

	const categories = [
		{ id: 'all', name: 'Все', icon: '📋' },
		{ id: 'push', name: 'Жим', icon: '💪' },
		{ id: 'pull', name: 'Тяга', icon: '🏋️' },
		{ id: 'legs', name: 'Ноги', icon: '🦵' },
		{ id: 'core', name: 'Кор', icon: '🎯' },
		{ id: 'static', name: 'Статика', icon: '🧘' },
		{ id: 'cardio', name: 'Кардио', icon: '❤️' },
	];

	onMount(async () => {
		await loadExercises();
	});

	async function loadExercises() {
		try {
			exercises = await api.getExercises();
		} catch (error) {
			console.error('Failed to load exercises:', error);
		} finally {
			isLoading = false;
		}
	}

	async function startWorkout() {
		try {
			currentWorkout = await api.startWorkout();
			workoutExercises = [];
			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
			}
		} catch (error) {
			console.error('Failed to start workout:', error);
		}
	}

	async function addExercise() {
		if (!currentWorkout || !selectedExercise) return;

		try {
			const data: any = {
				exercise_id: selectedExercise.id,
				sets: inputSets,
			};

			if (selectedExercise.metric_type === 'reps') {
				data.reps = inputReps;
			} else {
				data.duration_seconds = inputDuration;
			}

			const result = await api.addExerciseToWorkout(currentWorkout.id, data);
			result.exercise = selectedExercise;
			workoutExercises = [...workoutExercises, result];
			selectedExercise = null;

			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
			}
		} catch (error) {
			console.error('Failed to add exercise:', error);
		}
	}

	async function finishWorkout() {
		if (!currentWorkout) return;

		try {
			workoutResult = await api.finishWorkout(currentWorkout.id);
			showResult = true;

			// Update user data
			if ($user) {
				$user = {
					...$user,
					experience: $user.experience + workoutResult.total_exp,
					level: workoutResult.new_level,
					total_workouts: $user.total_workouts + 1,
				};
			}

			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
			}
		} catch (error) {
			console.error('Failed to finish workout:', error);
		}
	}

	function closeResult() {
		showResult = false;
		workoutResult = null;
		currentWorkout = null;
		workoutExercises = [];
		goto(`${base}/`);
	}

	let filteredExercises = $derived(
		selectedCategory === 'all'
			? exercises
			: exercises.filter(e => e.category === selectedCategory)
	);

	let totalXP = $derived(
		workoutExercises.reduce((sum, we) => sum + we.exp_earned, 0)
	);
</script>

<div class="container">
	<header class="page-header">
		<h1 class="pixel-title">💪 ТРЕНИРОВКА</h1>
	</header>

	{#if showResult && workoutResult}
		<!-- Workout Result -->
		<div class="result-overlay">
			<div class="result-card pixel-card">
				{#if workoutResult.level_up}
					<div class="level-up-banner">
						<div class="level-up-text">LEVEL UP!</div>
						<div class="new-level">LVL {workoutResult.new_level}</div>
					</div>
				{/if}

				<div class="result-header">
					<div class="result-icon">🎉</div>
					<div class="result-title">ТРЕНИРОВКА ЗАВЕРШЕНА!</div>
				</div>

				<div class="result-stats">
					<div class="result-stat">
						<div class="result-stat-value text-accent">+{workoutResult.total_exp}</div>
						<div class="result-stat-label">XP ЗАРАБОТАНО</div>
					</div>
					<div class="result-stat">
						<div class="result-stat-value">{workoutExercises.length}</div>
						<div class="result-stat-label">УПРАЖНЕНИЙ</div>
					</div>
				</div>

				{#if workoutResult.new_achievements.length > 0}
					<div class="new-achievements">
						<div class="achievements-title">🏆 НОВЫЕ ДОСТИЖЕНИЯ!</div>
						{#each workoutResult.new_achievements as ach}
							<div class="achievement-item">{ach}</div>
						{/each}
					</div>
				{/if}

				<button class="pixel-btn secondary w-full mt-lg" onclick={closeResult}>
					ОТЛИЧНО!
				</button>
			</div>
		</div>
	{:else if !currentWorkout}
		<!-- Start Workout -->
		<div class="start-screen">
			<div class="start-icon">🎮</div>
			<div class="start-text">
				<div class="start-title">ГОТОВ К БОЮ?</div>
				<div class="start-desc">Начни тренировку и заработай опыт!</div>
			</div>
			<button class="pixel-btn accent" onclick={startWorkout}>
				НАЧАТЬ ТРЕНИРОВКУ
			</button>
		</div>
	{:else if selectedExercise}
		<!-- Exercise Input -->
		<div class="exercise-input pixel-card">
			<div class="input-header">
				<span class="input-icon">{selectedExercise.icon}</span>
				<span class="input-name">{selectedExercise.name}</span>
			</div>

			<div class="input-fields">
				<div class="input-group">
					<label>ПОДХОДЫ</label>
					<div class="number-input">
						<button onclick={() => inputSets = Math.max(1, inputSets - 1)}>-</button>
						<span>{inputSets}</span>
						<button onclick={() => inputSets++}>+</button>
					</div>
				</div>

				{#if selectedExercise.metric_type === 'reps'}
					<div class="input-group">
						<label>ПОВТОРЕНИЯ</label>
						<div class="number-input">
							<button onclick={() => inputReps = Math.max(1, inputReps - 5)}>-</button>
							<span>{inputReps}</span>
							<button onclick={() => inputReps += 5}>+</button>
						</div>
					</div>
				{:else}
					<div class="input-group">
						<label>СЕКУНДЫ</label>
						<div class="number-input">
							<button onclick={() => inputDuration = Math.max(5, inputDuration - 10)}>-</button>
							<span>{inputDuration}</span>
							<button onclick={() => inputDuration += 10}>+</button>
						</div>
					</div>
				{/if}
			</div>

			<div class="input-xp">
				{#if selectedExercise.metric_type === 'reps'}
					+{inputReps * inputSets * selectedExercise.exp_per_rep} XP
				{:else}
					+{inputDuration * inputSets * selectedExercise.exp_per_second} XP
				{/if}
			</div>

			<div class="input-actions">
				<button class="pixel-btn" onclick={() => selectedExercise = null}>ОТМЕНА</button>
				<button class="pixel-btn secondary" onclick={addExercise}>ДОБАВИТЬ</button>
			</div>
		</div>
	{:else}
		<!-- Workout in Progress -->
		<div class="workout-progress">
			<div class="progress-header pixel-card">
				<div class="progress-info">
					<span class="progress-label">ТЕКУЩИЙ XP:</span>
					<span class="progress-value text-accent">+{totalXP}</span>
				</div>
				<div class="progress-info">
					<span class="progress-label">УПРАЖНЕНИЙ:</span>
					<span class="progress-value">{workoutExercises.length}</span>
				</div>
			</div>

			{#if workoutExercises.length > 0}
				<div class="exercises-done">
					<div class="section-title">ВЫПОЛНЕНО:</div>
					{#each workoutExercises as we}
						<div class="exercise-done-item">
							<span class="done-icon">{we.exercise?.icon || '💪'}</span>
							<span class="done-name">{we.exercise?.name || 'Упражнение'}</span>
							<span class="done-value">
								{we.reps ? `${we.sets}x${we.reps}` : `${we.duration_seconds}с`}
							</span>
							{#if we.is_personal_record}
								<span class="pr-badge">PR!</span>
							{/if}
						</div>
					{/each}
				</div>
			{/if}

			<!-- Categories -->
			<div class="categories-scroll">
				{#each categories as cat}
					<button
						class="category-btn"
						class:active={selectedCategory === cat.id}
						onclick={() => selectedCategory = cat.id}
					>
						{cat.icon} {cat.name}
					</button>
				{/each}
			</div>

			<!-- Exercise List -->
			<div class="exercises-list">
				{#if isLoading}
					<div class="loading-text">Загрузка...</div>
				{:else}
					{#each filteredExercises as exercise}
						<button class="exercise-item" onclick={() => {
							selectedExercise = exercise;
							inputReps = 10;
							inputSets = 1;
							inputDuration = 30;
						}}>
							<span class="exercise-icon">{exercise.icon}</span>
							<div class="exercise-info">
								<div class="exercise-name">{exercise.name}</div>
								<div class="exercise-meta">
									<span class="category-pill {exercise.category}">{exercise.category}</span>
									<span class="xp-badge">
										+{exercise.metric_type === 'reps' ? exercise.exp_per_rep : exercise.exp_per_second} XP
									</span>
								</div>
							</div>
							<span class="add-icon">+</span>
						</button>
					{/each}
				{/if}
			</div>

			{#if workoutExercises.length > 0}
				<div class="finish-btn-container">
					<button class="pixel-btn accent w-full" onclick={finishWorkout}>
						🏁 ЗАВЕРШИТЬ ТРЕНИРОВКУ
					</button>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.page-header {
		text-align: center;
		margin-bottom: var(--space-lg);
	}

	.start-screen {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		text-align: center;
	}

	.start-icon {
		font-size: 64px;
		margin-bottom: var(--space-lg);
		animation: bounce 1s infinite;
	}

	.start-title {
		font-size: 16px;
		color: var(--accent);
		margin-bottom: var(--space-sm);
	}

	.start-desc {
		font-size: 10px;
		color: var(--text-muted);
		margin-bottom: var(--space-xl);
	}

	.progress-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: var(--space-md);
	}

	.progress-label {
		font-size: 8px;
		color: var(--text-muted);
	}

	.progress-value {
		font-size: 14px;
	}

	.section-title {
		font-size: 10px;
		color: var(--text-muted);
		margin-bottom: var(--space-sm);
	}

	.exercises-done {
		margin-bottom: var(--space-md);
	}

	.exercise-done-item {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		padding: var(--space-sm);
		background: var(--bg-card);
		border: 2px solid var(--border);
		margin-bottom: var(--space-xs);
		font-size: 9px;
	}

	.done-icon {
		font-size: 16px;
	}

	.done-name {
		flex: 1;
	}

	.done-value {
		color: var(--accent);
	}

	.pr-badge {
		background: var(--secondary);
		color: var(--bg-dark);
		padding: 2px 6px;
		font-size: 7px;
	}

	.categories-scroll {
		display: flex;
		gap: var(--space-xs);
		overflow-x: auto;
		padding: var(--space-sm) 0;
		margin-bottom: var(--space-md);
	}

	.category-btn {
		flex-shrink: 0;
		padding: var(--space-sm) var(--space-md);
		background: var(--bg-card);
		border: 2px solid var(--border);
		color: var(--text-secondary);
		font-family: 'Press Start 2P', monospace;
		font-size: 8px;
		cursor: pointer;
	}

	.category-btn.active {
		border-color: var(--accent);
		color: var(--accent);
	}

	.exercises-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
		margin-bottom: var(--space-xl);
	}

	.exercise-item {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		padding: var(--space-md);
		background: var(--bg-card);
		border: 4px solid var(--border);
		cursor: pointer;
		text-align: left;
		transition: all 0.1s;
	}

	.exercise-item:hover {
		border-color: var(--secondary);
	}

	.exercise-icon {
		font-size: 24px;
	}

	.exercise-info {
		flex: 1;
	}

	.exercise-name {
		font-family: 'Press Start 2P', monospace;
		font-size: 9px;
		color: var(--text-primary);
		margin-bottom: var(--space-xs);
	}

	.exercise-meta {
		display: flex;
		gap: var(--space-sm);
		align-items: center;
	}

	.xp-badge {
		font-size: 7px;
		color: var(--accent);
	}

	.add-icon {
		font-size: 20px;
		color: var(--secondary);
	}

	.exercise-input {
		text-align: center;
	}

	.input-header {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-sm);
		margin-bottom: var(--space-lg);
	}

	.input-icon {
		font-size: 32px;
	}

	.input-name {
		font-size: 12px;
	}

	.input-fields {
		display: flex;
		justify-content: center;
		gap: var(--space-lg);
		margin-bottom: var(--space-md);
	}

	.input-group {
		text-align: center;
	}

	.input-group label {
		display: block;
		font-size: 8px;
		color: var(--text-muted);
		margin-bottom: var(--space-sm);
	}

	.number-input {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
	}

	.number-input button {
		width: 36px;
		height: 36px;
		background: var(--bg-medium);
		border: 2px solid var(--border);
		color: var(--text-primary);
		font-size: 16px;
		cursor: pointer;
	}

	.number-input span {
		min-width: 48px;
		font-size: 16px;
		color: var(--accent);
	}

	.input-xp {
		font-size: 14px;
		color: var(--secondary);
		margin-bottom: var(--space-lg);
	}

	.input-actions {
		display: flex;
		gap: var(--space-md);
		justify-content: center;
	}

	.finish-btn-container {
		position: fixed;
		bottom: 80px;
		left: var(--space-md);
		right: var(--space-md);
		max-width: 448px;
		margin: 0 auto;
	}

	.result-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0,0,0,0.9);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-md);
		z-index: 1000;
	}

	.result-card {
		width: 100%;
		max-width: 320px;
		text-align: center;
		animation: popIn 0.3s ease-out;
	}

	.level-up-banner {
		background: linear-gradient(135deg, var(--accent) 0%, var(--warning) 100%);
		padding: var(--space-md);
		margin: calc(-1 * var(--space-md));
		margin-bottom: var(--space-md);
	}

	.level-up-text {
		font-size: 20px;
		color: var(--bg-dark);
		animation: pulse 0.5s infinite;
	}

	.new-level {
		font-size: 14px;
		color: var(--bg-dark);
		margin-top: var(--space-sm);
	}

	.result-header {
		margin-bottom: var(--space-lg);
	}

	.result-icon {
		font-size: 48px;
		margin-bottom: var(--space-sm);
	}

	.result-title {
		font-size: 12px;
		color: var(--accent);
	}

	.result-stats {
		display: flex;
		justify-content: center;
		gap: var(--space-xl);
		margin-bottom: var(--space-lg);
	}

	.result-stat-value {
		font-size: 20px;
	}

	.result-stat-label {
		font-size: 7px;
		color: var(--text-muted);
		margin-top: var(--space-xs);
	}

	.new-achievements {
		background: var(--bg-medium);
		padding: var(--space-md);
		margin-bottom: var(--space-md);
	}

	.achievements-title {
		font-size: 10px;
		color: var(--accent);
		margin-bottom: var(--space-sm);
	}

	.achievement-item {
		font-size: 9px;
		color: var(--secondary);
	}

	.loading-text {
		text-align: center;
		font-size: 10px;
		color: var(--text-muted);
		padding: var(--space-xl);
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}

	@keyframes popIn {
		0% { transform: scale(0.5); opacity: 0; }
		100% { transform: scale(1); opacity: 1; }
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.1); }
	}
</style>
