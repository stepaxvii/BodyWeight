<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon, PixelProgress } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { workoutStore } from '$lib/stores/workout.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { ExerciseCategory, Exercise } from '$lib/types';

	let categories = $state<ExerciseCategory[]>([]);
	let exercises = $state<Exercise[]>([]);
	let selectedCategory = $state<ExerciseCategory | null>(null);
	let view = $state<'categories' | 'exercises' | 'workout'>('categories');

	onMount(async () => {
		categories = await api.getCategories();

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

	function goBack() {
		if (view === 'exercises') {
			view = 'categories';
			selectedCategory = null;
		}
		telegram.hapticImpact('light');
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
		<!-- Category Selection -->
		<header class="page-header">
			<h1>Choose Category</h1>
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
					Start New Workout
				</PixelButton>
			</div>
		{:else}
			<div class="continue-section">
				<PixelCard variant="accent">
					<div class="active-workout-info">
						<div class="workout-status">
							<PixelIcon name="timer" color="var(--pixel-accent)" />
							<span>Workout in progress</span>
						</div>
						<span class="workout-time">{workoutStore.formattedDuration}</span>
					</div>
				</PixelCard>
				<div class="workout-actions">
					<PixelButton variant="secondary" onclick={() => view = 'workout'}>
						Continue
					</PixelButton>
					<PixelButton variant="success" onclick={finishWorkout}>
						Finish
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
						<span class="rep-label">Reps</span>
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
						Add Set
					</PixelButton>
				</PixelCard>
			</div>
		{/if}

	{:else if view === 'workout'}
		<!-- Active Workout -->
		<header class="page-header">
			<h1>Workout</h1>
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
						<span class="total-label">Reps</span>
					</div>
					<div class="total-item">
						<span class="total-value text-green">+{workoutStore.totalXp}</span>
						<span class="total-label">XP</span>
					</div>
					<div class="total-item">
						<span class="total-value text-yellow">+{workoutStore.totalCoins}</span>
						<span class="total-label">Coins</span>
					</div>
				</div>
			</div>
		</PixelCard>

		<!-- Category selection -->
		<section class="workout-categories">
			<h3 class="section-title">Add Exercise</h3>
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
				<h3 class="section-title">Completed Sets</h3>
				<div class="log-list">
					{#each workoutStore.session.exercises as we}
						<PixelCard padding="sm">
							<div class="log-item">
								<span class="log-exercise">{we.exercise?.name_ru || 'Exercise'}</span>
								<span class="log-reps">{we.total_reps} reps</span>
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
				Complete Workout
			</PixelButton>
			<PixelButton variant="ghost" fullWidth onclick={() => workoutStore.cancelWorkout()}>
				Cancel
			</PixelButton>
		</div>
	{/if}
</div>

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
</style>
