<script lang="ts">
	import { onMount } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon } from '$lib/components/ui';
	import RoutinePlayer from '$lib/components/RoutinePlayer.svelte';
	import { api } from '$lib/api/client';
	import { workoutStore } from '$lib/stores/workout.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { ExerciseCategory, Exercise, Routine, RoutineCategory } from '$lib/types';

	// Data
	let categories = $state<ExerciseCategory[]>([]);
	let exercises = $state<Exercise[]>([]);
	let routines = $state<Routine[]>([]);

	// UI state
	let activeCategory = $state<string | null>(null);
	let selectedRoutine = $state<Routine | null>(null);
	let showRoutinePlayer = $state(false);
	let activeRoutineCategory = $state<RoutineCategory>('morning');

	// Filtered exercises by category
	const filteredExercises = $derived(
		activeCategory ? exercises.filter(e => e.category_slug === activeCategory) : exercises
	);

	// Filtered routines by category
	const filteredRoutines = $derived(
		routines.filter(r => r.category === activeRoutineCategory)
	);

	// Category colors
	const categoryColors: Record<string, string> = {
		push: '#d82800',
		pull: '#0058f8',
		legs: '#00a800',
		core: '#fcc800',
		static: '#6800a8',
		cardio: '#fc7400',
		warmup: '#00a8a8',
		stretch: '#f878f8'
	};

	const routineCategoryTabs: { id: RoutineCategory; name: string }[] = [
		{ id: 'morning', name: 'Зарядка' },
		{ id: 'home', name: 'Дома' },
		{ id: 'pullup-bar', name: 'Турник' },
		{ id: 'dip-bars', name: 'Брусья' }
	];

	onMount(async () => {
		categories = await api.getCategories();
		exercises = await api.getExercises();
		routines = await api.getRoutines();
	});

	function selectCategory(slug: string) {
		activeCategory = activeCategory === slug ? null : slug;
		telegram.hapticImpact('light');
	}

	function toggleExercise(exercise: Exercise) {
		workoutStore.toggleExerciseSelection(exercise);
	}

	async function startWorkout() {
		await workoutStore.startWorkout();
	}

	async function finishWorkout() {
		await workoutStore.completeWorkout();
	}

	function cancelWorkout() {
		workoutStore.cancelWorkout();
	}

	// Routine handling
	function selectRoutine(routine: Routine) {
		selectedRoutine = routine;
		showRoutinePlayer = true;
		telegram.hapticImpact('medium');
	}

	function handleRoutineClose() {
		showRoutinePlayer = false;
		selectedRoutine = null;
	}

	function handleRoutineComplete() {
		showRoutinePlayer = false;
		selectedRoutine = null;
	}

	function getDifficultyStars(difficulty: number): string {
		return '★'.repeat(difficulty) + '☆'.repeat(5 - difficulty);
	}
</script>

<div class="page container">
	{#if workoutStore.isActive}
		<!-- ACTIVE WORKOUT VIEW -->
		<header class="workout-header">
			<h1>Тренировка</h1>
			<div class="timer">
				<PixelIcon name="timer" color="var(--pixel-accent)" />
				<span class="timer-value">{workoutStore.formattedDuration}</span>
			</div>
		</header>

		<!-- Stats summary -->
		<PixelCard variant="accent" padding="md">
			<div class="workout-stats">
				<div class="stat">
					<span class="stat-value">{workoutStore.totalSets}</span>
					<span class="stat-label">Подходов</span>
				</div>
				<div class="stat">
					<span class="stat-value">{workoutStore.totalReps}</span>
					<span class="stat-label">Повторов</span>
				</div>
				<div class="stat">
					<span class="stat-value text-green">+{workoutStore.totalXp}</span>
					<span class="stat-label">XP</span>
				</div>
			</div>
		</PixelCard>

		<!-- Exercise cards with inline input -->
		<div class="exercise-cards">
			{#each workoutStore.selectedExercises as exercise (exercise.id)}
				{@const data = workoutStore.getExerciseData(exercise.id)}
				<PixelCard padding="md">
					<div class="exercise-card">
						<div class="exercise-header">
							<span class="exercise-name">{exercise.name_ru}</span>
							<span class="exercise-difficulty" style="color: {categoryColors[exercise.category_slug]}">
								{getDifficultyStars(exercise.difficulty)}
							</span>
						</div>

						{#if data && data.sets.length > 0}
							<div class="sets-list">
								{#each data.sets as reps, i}
									<span class="set-badge">{reps}</span>
								{/each}
							</div>
						{/if}

						<div class="input-row">
							<PixelButton
								variant="secondary"
								size="sm"
								onclick={() => workoutStore.decrementReps(exercise.id)}
							>
								<PixelIcon name="minus" size="sm" />
							</PixelButton>
							<span class="reps-input">{data?.inputReps ?? 10}</span>
							<PixelButton
								variant="secondary"
								size="sm"
								onclick={() => workoutStore.incrementReps(exercise.id)}
							>
								<PixelIcon name="plus" size="sm" />
							</PixelButton>
							<PixelButton
								variant="success"
								size="sm"
								onclick={() => workoutStore.addSet(exercise.id)}
								disabled={workoutStore.isLoading}
							>
								<PixelIcon name="check" size="sm" />
								Подход
							</PixelButton>
						</div>
					</div>
				</PixelCard>
			{/each}
		</div>

		<!-- Finish buttons -->
		<div class="workout-actions">
			<PixelButton variant="success" size="lg" fullWidth onclick={finishWorkout}>
				<PixelIcon name="check" />
				Завершить тренировку
			</PixelButton>
			<PixelButton variant="ghost" fullWidth onclick={cancelWorkout}>
				Отменить
			</PixelButton>
		</div>

	{:else}
		<!-- SELECTION VIEW -->

		<!-- Routines section -->
		{#if routines.length > 0}
			<section class="routines-section">
				<h2 class="section-title">Комплексы</h2>
				<div class="routine-tabs">
					{#each routineCategoryTabs as tab}
						<button
							class="routine-tab"
							class:active={activeRoutineCategory === tab.id}
							onclick={() => { activeRoutineCategory = tab.id; telegram.hapticImpact('light'); }}
						>
							{tab.name}
						</button>
					{/each}
				</div>
				<div class="routines-list">
					{#each filteredRoutines as routine}
						<PixelCard hoverable onclick={() => selectRoutine(routine)} padding="sm">
							<div class="routine-item">
								<div class="routine-info">
									<span class="routine-name">{routine.name}</span>
									<span class="routine-meta">{routine.duration_minutes} мин</span>
								</div>
								<PixelIcon name="play" size="sm" color="var(--text-secondary)" />
							</div>
						</PixelCard>
					{/each}
				</div>
			</section>
		{/if}

		<!-- Exercise selection -->
		<section class="selection-section">
			<h2 class="section-title">Свободная тренировка</h2>
			<p class="section-subtitle">Выбери упражнения для тренировки</p>

			<!-- Category tabs -->
			<div class="category-tabs">
				{#each categories as category}
					<button
						class="category-tab"
						class:active={activeCategory === category.slug}
						style="--cat-color: {categoryColors[category.slug]}"
						onclick={() => selectCategory(category.slug)}
					>
						{category.name_ru}
					</button>
				{/each}
			</div>

			<!-- Exercise list with checkboxes -->
			<div class="exercises-list">
				{#each filteredExercises as exercise}
					{@const isSelected = workoutStore.isExerciseSelected(exercise.id)}
					<PixelCard
						hoverable
						onclick={() => toggleExercise(exercise)}
						padding="sm"
					>
						<div class="exercise-row" class:selected={isSelected}>
							<div class="checkbox" class:checked={isSelected}>
								{#if isSelected}
									<PixelIcon name="check" size="sm" color="var(--pixel-bg)" />
								{/if}
							</div>
							<div class="exercise-info">
								<span class="exercise-name">{exercise.name_ru}</span>
								<span class="exercise-meta">
									<span style="color: {categoryColors[exercise.category_slug]}">
										{getDifficultyStars(exercise.difficulty)}
									</span>
									<span class="xp-badge">+{exercise.base_xp} XP</span>
								</span>
							</div>
						</div>
					</PixelCard>
				{/each}
			</div>
		</section>

		<!-- Fixed bottom panel -->
		{#if workoutStore.selectedCount > 0}
			<div class="selection-panel">
				<div class="selection-info">
					<span class="selection-count">Выбрано: {workoutStore.selectedCount}</span>
					<button class="clear-btn" onclick={() => workoutStore.clearSelection()}>
						Очистить
					</button>
				</div>
				<PixelButton variant="primary" size="lg" fullWidth onclick={startWorkout}>
					<PixelIcon name="play" />
					Начать тренировку
				</PixelButton>
			</div>
		{/if}
	{/if}
</div>

{#if showRoutinePlayer && selectedRoutine}
	<RoutinePlayer
		routine={selectedRoutine}
		onclose={handleRoutineClose}
		oncomplete={handleRoutineComplete}
	/>
{/if}

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: 180px; /* Space for fixed panel + nav */
	}

	.section-title {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin-bottom: var(--spacing-sm);
		color: var(--pixel-accent);
	}

	.section-subtitle {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		margin-bottom: var(--spacing-md);
	}

	/* Workout header */
	.workout-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-md);
	}

	.workout-header h1 {
		margin: 0;
	}

	.timer {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.timer-value {
		font-size: var(--font-size-lg);
		color: var(--pixel-accent);
	}

	/* Workout stats */
	.workout-stats {
		display: flex;
		justify-content: space-around;
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
	}

	.stat-value {
		font-size: var(--font-size-lg);
	}

	.stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	/* Exercise cards in workout */
	.exercise-cards {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-md);
	}

	.exercise-card {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.exercise-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.exercise-name {
		font-size: var(--font-size-sm);
	}

	.exercise-difficulty {
		font-size: var(--font-size-xs);
		letter-spacing: 1px;
	}

	.sets-list {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}

	.set-badge {
		background: var(--pixel-accent);
		color: var(--pixel-bg);
		padding: 2px 8px;
		font-size: var(--font-size-xs);
	}

	.input-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.reps-input {
		font-size: var(--font-size-lg);
		min-width: 48px;
		text-align: center;
	}

	.workout-actions {
		margin-top: var(--spacing-xl);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	/* Routines section */
	.routines-section {
		margin-bottom: var(--spacing-xl);
	}

	.routine-tabs {
		display: flex;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-sm);
		overflow-x: auto;
	}

	.routine-tab {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		white-space: nowrap;
	}

	.routine-tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	.routines-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.routine-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.routine-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.routine-name {
		font-size: var(--font-size-sm);
	}

	.routine-meta {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	/* Category tabs */
	.category-tabs {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-md);
	}

	.category-tab {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--cat-color);
		color: var(--cat-color);
		cursor: pointer;
	}

	.category-tab.active {
		background: var(--cat-color);
		color: var(--pixel-bg);
	}

	/* Exercises list */
	.exercises-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.exercise-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.exercise-row.selected {
		background: rgba(var(--pixel-accent-rgb), 0.1);
	}

	.checkbox {
		width: 24px;
		height: 24px;
		border: 2px solid var(--border-color);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.checkbox.checked {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
	}

	.exercise-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.exercise-meta {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		font-size: var(--font-size-xs);
	}

	.xp-badge {
		color: var(--pixel-green);
	}

	/* Selection panel */
	.selection-panel {
		position: fixed;
		bottom: 72px;
		left: 0;
		right: 0;
		background: var(--pixel-bg);
		border-top: 2px solid var(--border-color);
		padding: var(--spacing-md);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.selection-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.selection-count {
		font-size: var(--font-size-sm);
		color: var(--pixel-accent);
	}

	.clear-btn {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		text-decoration: underline;
	}

	.text-green { color: var(--pixel-green); }
</style>
