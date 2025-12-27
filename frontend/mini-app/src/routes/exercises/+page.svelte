<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Exercise } from '$lib/api/client';

	let exercises: Exercise[] = $state([]);
	let isLoading = $state(true);
	let selectedCategory = $state('all');
	let selectedExercise: Exercise | null = $state(null);

	const categories = [
		{ id: 'all', name: 'Все', icon: '📋' },
		{ id: 'push', name: 'Жим', icon: '💪' },
		{ id: 'pull', name: 'Тяга', icon: '🏋️' },
		{ id: 'legs', name: 'Ноги', icon: '🦵' },
		{ id: 'core', name: 'Кор', icon: '🎯' },
		{ id: 'static', name: 'Статика', icon: '🧘' },
		{ id: 'cardio', name: 'Кардио', icon: '❤️' },
		{ id: 'warmup', name: 'Разминка', icon: '🔥' },
		{ id: 'stretch', name: 'Растяжка', icon: '🌊' },
	];

	onMount(async () => {
		try {
			exercises = await api.getExercises();
		} catch (error) {
			console.error('Failed to load exercises:', error);
		} finally {
			isLoading = false;
		}
	});

	let filteredExercises = $derived(
		selectedCategory === 'all'
			? exercises
			: exercises.filter(e => e.category === selectedCategory)
	);

	function getDifficultyStars(difficulty: number): string {
		return '⭐'.repeat(difficulty) + '☆'.repeat(5 - difficulty);
	}
</script>

<div class="container">
	<header class="page-header">
		<h1 class="pixel-title">📋 УПРАЖНЕНИЯ</h1>
		<div class="exercises-count">{exercises.length} упражнений</div>
	</header>

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

	{#if selectedExercise}
		<!-- Exercise Detail -->
		<div class="exercise-detail pixel-card">
			<button class="back-btn" onclick={() => selectedExercise = null}>
				← НАЗАД
			</button>

			<div class="detail-header">
				<span class="detail-icon">{selectedExercise.icon}</span>
				<div class="detail-info">
					<div class="detail-name">{selectedExercise.name}</div>
					<div class="detail-category">
						<span class="category-pill {selectedExercise.category}">
							{selectedExercise.category}
						</span>
					</div>
				</div>
			</div>

			<div class="detail-stats">
				<div class="detail-stat">
					<div class="detail-stat-label">СЛОЖНОСТЬ</div>
					<div class="detail-stat-value">
						{getDifficultyStars(selectedExercise.difficulty)}
					</div>
				</div>
				<div class="detail-stat">
					<div class="detail-stat-label">МЕТРИКА</div>
					<div class="detail-stat-value">
						{selectedExercise.metric_type === 'reps' ? '🔢 Повторения' : '⏱️ Время'}
					</div>
				</div>
				<div class="detail-stat">
					<div class="detail-stat-label">ОПЫТ</div>
					<div class="detail-stat-value text-accent">
						{#if selectedExercise.metric_type === 'reps'}
							+{selectedExercise.exp_per_rep} XP/повтор
						{:else}
							+{selectedExercise.exp_per_second} XP/сек
						{/if}
					</div>
				</div>
			</div>

			{#if selectedExercise.description}
				<div class="detail-description">
					<div class="description-title">ОПИСАНИЕ:</div>
					<div class="description-text">{selectedExercise.description}</div>
				</div>
			{/if}
		</div>
	{:else if isLoading}
		<div class="loading">
			<div class="loading-icon">💪</div>
			<div class="loading-text">Загрузка упражнений...</div>
		</div>
	{:else}
		<div class="exercises-list">
			{#each filteredExercises as exercise}
				<button class="exercise-item" onclick={() => selectedExercise = exercise}>
					<span class="exercise-icon">{exercise.icon}</span>
					<div class="exercise-info">
						<div class="exercise-name">{exercise.name}</div>
						<div class="exercise-meta">
							<span class="category-pill {exercise.category}">{exercise.category}</span>
							<span class="difficulty">{getDifficultyStars(exercise.difficulty)}</span>
						</div>
					</div>
					<div class="exercise-xp">
						+{exercise.metric_type === 'reps' ? exercise.exp_per_rep : exercise.exp_per_second} XP
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.page-header {
		text-align: center;
		margin-bottom: var(--space-md);
	}

	.exercises-count {
		font-size: 10px;
		color: var(--text-muted);
		margin-top: var(--space-sm);
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

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 40vh;
	}

	.loading-icon {
		font-size: 48px;
		animation: bounce 1s infinite;
	}

	.loading-text {
		font-size: 10px;
		color: var(--text-muted);
		margin-top: var(--space-md);
	}

	.exercises-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
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
		width: 100%;
		transition: all 0.1s;
	}

	.exercise-item:hover {
		border-color: var(--accent);
	}

	.exercise-icon {
		font-size: 28px;
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

	.difficulty {
		font-size: 8px;
	}

	.exercise-xp {
		font-size: 9px;
		color: var(--accent);
	}

	/* Detail View */
	.exercise-detail {
		animation: fadeIn 0.2s ease-out;
	}

	.back-btn {
		background: none;
		border: none;
		color: var(--text-muted);
		font-family: 'Press Start 2P', monospace;
		font-size: 9px;
		cursor: pointer;
		margin-bottom: var(--space-md);
	}

	.detail-header {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		margin-bottom: var(--space-lg);
	}

	.detail-icon {
		font-size: 48px;
	}

	.detail-name {
		font-size: 14px;
		color: var(--text-primary);
		margin-bottom: var(--space-sm);
	}

	.detail-stats {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
		margin-bottom: var(--space-lg);
	}

	.detail-stat {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--space-sm) 0;
		border-bottom: 2px solid var(--border);
	}

	.detail-stat-label {
		font-size: 8px;
		color: var(--text-muted);
	}

	.detail-stat-value {
		font-size: 9px;
	}

	.detail-description {
		background: var(--bg-dark);
		padding: var(--space-md);
		border: 2px solid var(--border);
	}

	.description-title {
		font-size: 8px;
		color: var(--text-muted);
		margin-bottom: var(--space-sm);
	}

	.description-text {
		font-size: 9px;
		line-height: 1.6;
		color: var(--text-secondary);
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}

	@keyframes fadeIn {
		0% { opacity: 0; transform: translateY(10px); }
		100% { opacity: 1; transform: translateY(0); }
	}
</style>
