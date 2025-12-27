<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon, PixelProgress } from '$lib/components/ui';
	import RoutinePlayer from '$lib/components/RoutinePlayer.svelte';
	import { api } from '$lib/api/client';
	import { workoutStore } from '$lib/stores/workout.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { ExerciseCategory, Exercise, Routine, RoutineCategory } from '$lib/types';

	let categories = $state<ExerciseCategory[]>([]);
	let exercises = $state<Exercise[]>([]);
	let routines = $state<Routine[]>([]);
	let selectedCategory = $state<ExerciseCategory | null>(null);
	let selectedRoutine = $state<Routine | null>(null);
	let activeRoutineCategory = $state<RoutineCategory>('morning');
	let showRoutinePlayer = $state(false);
	let view = $state<'categories' | 'exercises' | 'workout' | 'routine'>('categories');

	onMount(async () => {
		categories = await api.getCategories();
		routines = await api.getRoutines();

		if (workoutStore.isActive) {
			view = 'workout';
		}
	});

	async function selectCategory(category: ExerciseCategory) {
		selectedCategory = category;
		exercises = await api.getExercises(category.slug);
		view = 'exercises';
		telegram.hapticImpact('light');
	}

	function selectExercise(exercise: Exercise) {
		workoutStore.selectExercise(exercise);
	}

	async function startWorkout() {
		await workoutStore.startWorkout();
		view = 'workout';
	}

	async function finishWorkout() {
		const session = await workoutStore.completeWorkout();
		if (session) {
			view = 'categories';
		}
	}

	function selectRoutine(routine: Routine) {
		selectedRoutine = routine;
		view = 'routine';
		telegram.hapticImpact('light');
	}

	function startRoutinePlayer() {
		if (selectedRoutine) {
			showRoutinePlayer = true;
			telegram.hapticImpact('medium');
		}
	}

	function handleRoutineComplete(xp: number, coins: number) {
		// Routine completed - reload stats
		userStore.loadStats();
	}

	function handleRoutineClose() {
		showRoutinePlayer = false;
		view = 'categories';
		selectedRoutine = null;
	}

	function selectRoutineCategory(category: RoutineCategory) {
		activeRoutineCategory = category;
		telegram.hapticImpact('light');
	}

	const filteredRoutines = $derived(routines.filter(r => r.category === activeRoutineCategory));

	const routineCategoryTabs: { id: RoutineCategory; name: string; icon: string }[] = [
		{ id: 'morning', name: 'Зарядка', icon: 'streak' },
		{ id: 'home', name: 'Дома', icon: 'home' },
		{ id: 'pullup-bar', name: 'Турник', icon: 'pullup' },
		{ id: 'dip-bars', name: 'Брусья', icon: 'dip' }
	];

	function goBack() {
		if (view === 'exercises') {
			view = 'categories';
			selectedCategory = null;
		} else if (view === 'routine') {
			view = 'categories';
			selectedRoutine = null;
		}
		telegram.hapticImpact('light');
	}

	function getDifficultyLabel(difficulty: number): string {
		switch (difficulty) {
			case 1: return 'Лёгкий';
			case 2: return 'Средний';
			case 3: return 'Активный';
			default: return '';
		}
	}

	function getDifficultyColor(difficulty: number): string {
		switch (difficulty) {
			case 1: return 'var(--pixel-green)';
			case 2: return 'var(--pixel-yellow)';
			case 3: return 'var(--pixel-orange)';
			default: return 'var(--text-secondary)';
		}
	}

	// Category icon colors
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

	function getDifficultyStars(difficulty: number): string[] {
		return Array(5).fill('').map((_, i) => i < difficulty ? 'star' : 'star-empty');
	}
</script>

<div class="page container">
	{#if view === 'categories'}
		<!-- Routines Section with Category Tabs -->
		{#if routines.length > 0}
			<section class="routines-section">
				<h2 class="section-header">Комплексы</h2>
				<div class="routine-tabs">
					{#each routineCategoryTabs as tab}
						<button
							class="routine-tab"
							class:active={activeRoutineCategory === tab.id}
							onclick={() => selectRoutineCategory(tab.id)}
						>
							{tab.name}
						</button>
					{/each}
				</div>
				<div class="routines-list">
					{#each filteredRoutines as routine}
						<PixelCard
							hoverable
							onclick={() => selectRoutine(routine)}
							padding="md"
						>
							<div class="routine-item">
								<div class="routine-icon">
									<PixelIcon name="streak" size="lg" color={getDifficultyColor(routine.difficulty)} />
								</div>
								<div class="routine-info">
									<span class="routine-name">{routine.name}</span>
									<div class="routine-meta">
										<span class="routine-duration">{routine.duration_minutes} мин</span>
										<span class="routine-difficulty" style="color: {getDifficultyColor(routine.difficulty)}">
											{getDifficultyLabel(routine.difficulty)}
										</span>
									</div>
								</div>
								<PixelIcon name="play" color="var(--text-secondary)" />
							</div>
						</PixelCard>
					{/each}
					{#if filteredRoutines.length === 0}
						<p class="no-routines">Нет комплексов в этой категории</p>
					{/if}
				</div>
			</section>
		{/if}

		<!-- Category Selection -->
		<header class="page-header">
			<h1>Выбери категорию</h1>
		</header>

		<div class="categories-grid">
			{#each categories as category}
				<PixelCard
					hoverable
					onclick={() => selectCategory(category)}
					padding="md"
				>
					<div class="category-item" style="--cat-color: {categoryColors[category.slug] || 'var(--pixel-accent)'}">
						<div class="category-icon">
							<PixelIcon name="play" size="xl" color={categoryColors[category.slug]} />
						</div>
						<span class="category-name">{category.name_ru}</span>
					</div>
				</PixelCard>
			{/each}
		</div>

		{#if !workoutStore.isActive}
			<div class="start-section">
				<PixelButton variant="primary" size="lg" fullWidth onclick={startWorkout}>
					<PixelIcon name="play" />
					Начать тренировку
				</PixelButton>
			</div>
		{:else}
			<div class="continue-section">
				<PixelCard variant="accent">
					<div class="active-workout-info">
						<div class="workout-status">
							<PixelIcon name="timer" color="var(--pixel-accent)" />
							<span>Тренировка идёт</span>
						</div>
						<span class="workout-time">{workoutStore.formattedDuration}</span>
					</div>
				</PixelCard>
				<div class="workout-actions">
					<PixelButton variant="secondary" onclick={() => view = 'workout'}>
						Продолжить
					</PixelButton>
					<PixelButton variant="success" onclick={finishWorkout}>
						Завершить
					</PixelButton>
				</div>
			</div>
		{/if}

	{:else if view === 'exercises'}
		<!-- Exercise List -->
		<header class="page-header with-back">
			<button class="back-btn" onclick={goBack}>
				<PixelIcon name="back" />
			</button>
			<h1 style="color: {categoryColors[selectedCategory?.slug || '']}">{selectedCategory?.name_ru}</h1>
		</header>

		<div class="exercises-list">
			{#each exercises as exercise}
				<PixelCard
					hoverable
					onclick={() => selectExercise(exercise)}
					padding="md"
				>
					<div class="exercise-item" class:selected={workoutStore.currentExercise?.id === exercise.id}>
						<div class="exercise-info">
							<span class="exercise-name">{exercise.name_ru}</span>
							<div class="exercise-meta">
								<div class="difficulty">
									{#each getDifficultyStars(exercise.difficulty) as star}
										<PixelIcon name={star} size="sm" color="var(--pixel-yellow)" />
									{/each}
								</div>
								<span class="base-xp">+{exercise.base_xp} XP</span>
							</div>
						</div>
						{#if workoutStore.currentExercise?.id === exercise.id}
							<PixelIcon name="check" color="var(--pixel-green)" />
						{/if}
					</div>
				</PixelCard>
			{/each}
		</div>

		{#if workoutStore.currentExercise}
			<div class="selected-exercise">
				<PixelCard variant="accent">
					<div class="rep-counter">
						<span class="rep-label">Повторений</span>
						<div class="rep-controls">
							<PixelButton variant="secondary" size="sm" onclick={() => workoutStore.decrementReps()}>
								<PixelIcon name="minus" />
							</PixelButton>
							<span class="rep-value">{workoutStore.currentReps}</span>
							<PixelButton variant="secondary" size="sm" onclick={() => workoutStore.incrementReps()}>
								<PixelIcon name="plus" />
							</PixelButton>
						</div>
					</div>
					<PixelButton
						variant="success"
						fullWidth
						onclick={() => workoutStore.addSet()}
						disabled={workoutStore.currentReps <= 0}
					>
						<PixelIcon name="check" />
						Добавить подход
					</PixelButton>
				</PixelCard>
			</div>
		{/if}

	{:else if view === 'routine'}
		<!-- Routine Details -->
		<header class="page-header with-back">
			<button class="back-btn" onclick={goBack}>
				<PixelIcon name="back" />
			</button>
			<h1>{selectedRoutine?.name}</h1>
		</header>

		{#if selectedRoutine}
			<PixelCard variant="accent" padding="md">
				<div class="routine-details">
					<p class="routine-description">{selectedRoutine.description}</p>
					<div class="routine-stats">
						<div class="routine-stat">
							<PixelIcon name="timer" size="sm" color="var(--text-secondary)" />
							<span>{selectedRoutine.duration_minutes} мин</span>
						</div>
						<div class="routine-stat">
							<PixelIcon name="streak" size="sm" color={getDifficultyColor(selectedRoutine.difficulty)} />
							<span style="color: {getDifficultyColor(selectedRoutine.difficulty)}">
								{getDifficultyLabel(selectedRoutine.difficulty)}
							</span>
						</div>
						<div class="routine-stat">
							<PixelIcon name="play" size="sm" color="var(--text-secondary)" />
							<span>{selectedRoutine.exercises.length} упр.</span>
						</div>
					</div>
				</div>
			</PixelCard>

			<section class="routine-exercises">
				<h3 class="section-title">Упражнения</h3>
				<div class="routine-exercise-list">
					{#each selectedRoutine.exercises as routineEx, i}
						<PixelCard padding="sm">
							<div class="routine-exercise-item">
								<span class="routine-exercise-number">{i + 1}</span>
								<span class="routine-exercise-name">{routineEx.slug.replace(/-/g, ' ')}</span>
								<span class="routine-exercise-amount">
									{#if routineEx.reps}
										{routineEx.reps} повт.
									{:else if routineEx.duration}
										{routineEx.duration} сек
									{/if}
								</span>
							</div>
						</PixelCard>
					{/each}
				</div>
			</section>

			<div class="start-routine-section">
				<PixelButton variant="primary" size="lg" fullWidth onclick={startRoutinePlayer}>
					<PixelIcon name="play" />
					Начать комплекс
				</PixelButton>
			</div>
		{/if}

	{:else if view === 'workout'}
		<!-- Active Workout -->
		<header class="page-header">
			<h1>Тренировка</h1>
		</header>

		<!-- Timer and Stats -->
		<PixelCard variant="accent">
			<div class="workout-stats">
				<div class="timer-display">
					<PixelIcon name="timer" size="lg" color="var(--pixel-accent)" />
					<span class="timer-value">{workoutStore.formattedDuration}</span>
				</div>
				<div class="workout-totals">
					<div class="total-item">
						<span class="total-value">{workoutStore.totalReps}</span>
						<span class="total-label">Повторы</span>
					</div>
					<div class="total-item">
						<span class="total-value text-green">+{workoutStore.totalXp}</span>
						<span class="total-label">XP</span>
					</div>
					<div class="total-item">
						<span class="total-value text-yellow">+{workoutStore.totalCoins}</span>
						<span class="total-label">Монеты</span>
					</div>
				</div>
			</div>
		</PixelCard>

		<!-- Category selection -->
		<section class="workout-categories">
			<h3 class="section-title">Добавить упражнение</h3>
			<div class="categories-row">
				{#each categories as category}
					<button
						class="category-chip"
						style="--cat-color: {categoryColors[category.slug]}"
						onclick={() => selectCategory(category)}
					>
						{category.name_ru}
					</button>
				{/each}
			</div>
		</section>

		<!-- Workout exercises log -->
		{#if workoutStore.session?.exercises && workoutStore.session.exercises.length > 0}
			<section class="workout-log">
				<h3 class="section-title">Выполненные подходы</h3>
				<div class="log-list">
					{#each workoutStore.session.exercises as we}
						<PixelCard padding="sm">
							<div class="log-item">
								<span class="log-exercise">{we.exercise?.name_ru || 'Упражнение'}</span>
								<span class="log-reps">{we.total_reps} повт.</span>
								<span class="log-xp text-green">+{we.xp_earned} XP</span>
							</div>
						</PixelCard>
					{/each}
				</div>
			</section>
		{/if}

		<!-- Finish button -->
		<div class="finish-section">
			<PixelButton variant="success" size="lg" fullWidth onclick={finishWorkout}>
				<PixelIcon name="check" />
				Завершить тренировку
			</PixelButton>
			<PixelButton variant="ghost" fullWidth onclick={() => workoutStore.cancelWorkout()}>
				Отменить
			</PixelButton>
		</div>
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
		padding-bottom: var(--spacing-lg);
	}

	.page-header {
		text-align: center;
		margin-bottom: var(--spacing-lg);
	}

	.page-header.with-back {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		text-align: left;
	}

	.back-btn {
		background: none;
		border: 2px solid var(--border-color);
		padding: var(--spacing-xs);
		cursor: pointer;
		color: var(--text-primary);
	}

	.back-btn:hover {
		border-color: var(--pixel-accent);
	}

	/* Categories Grid */
	.categories-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-lg);
	}

	.category-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm);
	}

	.category-icon {
		width: 48px;
		height: 48px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--cat-color);
	}

	.category-name {
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		color: var(--cat-color);
	}

	/* Exercise List */
	.exercises-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-lg);
	}

	.exercise-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.exercise-item.selected {
		border-left: 4px solid var(--pixel-green);
		margin-left: -4px;
		padding-left: var(--spacing-sm);
	}

	.exercise-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.exercise-name {
		font-size: var(--font-size-sm);
	}

	.exercise-meta {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.difficulty {
		display: flex;
		gap: 2px;
	}

	.base-xp {
		font-size: var(--font-size-xs);
		color: var(--pixel-green);
	}

	/* Selected Exercise */
	.selected-exercise {
		position: fixed;
		bottom: 80px;
		left: 0;
		right: 0;
		padding: var(--spacing-md);
		background: var(--pixel-bg);
		border-top: 2px solid var(--border-color);
	}

	.rep-counter {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-md);
	}

	.rep-label {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
	}

	.rep-controls {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.rep-value {
		font-size: var(--font-size-xl);
		min-width: 48px;
		text-align: center;
	}

	/* Active Workout */
	.workout-stats {
		text-align: center;
	}

	.timer-display {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-md);
	}

	.timer-value {
		font-size: var(--font-size-2xl);
		color: var(--pixel-accent);
	}

	.workout-totals {
		display: flex;
		justify-content: space-around;
	}

	.total-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.total-value {
		font-size: var(--font-size-lg);
	}

	.total-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	/* Workout Categories Row */
	.workout-categories {
		margin-top: var(--spacing-lg);
	}

	.section-title {
		font-size: var(--font-size-sm);
		margin-bottom: var(--spacing-sm);
		text-transform: uppercase;
	}

	.categories-row {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}

	.category-chip {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--cat-color);
		color: var(--cat-color);
		cursor: pointer;
		text-transform: uppercase;
	}

	.category-chip:hover {
		background: var(--pixel-card-hover);
	}

	/* Workout Log */
	.workout-log {
		margin-top: var(--spacing-lg);
	}

	.log-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.log-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: var(--font-size-xs);
	}

	.log-exercise {
		flex: 1;
	}

	.log-reps {
		color: var(--text-secondary);
		margin-right: var(--spacing-md);
	}

	/* Start/Continue Section */
	.start-section,
	.continue-section,
	.finish-section {
		margin-top: var(--spacing-lg);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.active-workout-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.workout-status {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
	}

	.workout-time {
		font-size: var(--font-size-lg);
		color: var(--pixel-accent);
	}

	.workout-actions {
		display: flex;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-sm);
	}

	.workout-actions > :global(*) {
		flex: 1;
	}

	.text-green { color: var(--pixel-green); }
	.text-yellow { color: var(--pixel-yellow); }

	/* Routines Section */
	.routines-section {
		margin-bottom: var(--spacing-xl);
	}

	.section-header {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin-bottom: var(--spacing-md);
		color: var(--pixel-yellow);
	}

	.routine-tabs {
		display: flex;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-md);
		overflow-x: auto;
		-webkit-overflow-scrolling: touch;
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
		transition: all var(--transition-fast);
	}

	.routine-tab:hover {
		border-color: var(--pixel-accent);
	}

	.routine-tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	.routines-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.no-routines {
		font-size: var(--font-size-sm);
		color: var(--text-muted);
		text-align: center;
		padding: var(--spacing-lg);
	}

	.routine-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.routine-icon {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
	}

	.routine-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.routine-name {
		font-size: var(--font-size-sm);
	}

	.routine-meta {
		display: flex;
		gap: var(--spacing-md);
		font-size: var(--font-size-xs);
	}

	.routine-duration {
		color: var(--text-secondary);
	}

	/* Routine Details View */
	.routine-details {
		text-align: center;
	}

	.routine-description {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		margin-bottom: var(--spacing-md);
		line-height: 1.4;
	}

	.routine-stats {
		display: flex;
		justify-content: center;
		gap: var(--spacing-lg);
	}

	.routine-stat {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-xs);
	}

	.routine-exercises {
		margin-top: var(--spacing-lg);
	}

	.routine-exercise-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.routine-exercise-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		font-size: var(--font-size-xs);
	}

	.routine-exercise-number {
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
		font-size: 10px;
		color: var(--text-secondary);
	}

	.routine-exercise-name {
		flex: 1;
		text-transform: capitalize;
	}

	.routine-exercise-amount {
		color: var(--pixel-green);
	}

	.start-routine-section {
		margin-top: var(--spacing-xl);
	}
</style>
