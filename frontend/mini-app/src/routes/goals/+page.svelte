<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { api, type Goal } from '$lib/api/client';

	let goals: Goal[] = $state([]);
	let isLoading = $state(true);
	let showCreateForm = $state(false);

	// Form state
	let goalType = $state('total_reps');
	let goalTitle = $state('');
	let targetValue = $state(100);

	const goalTypes = [
		{ id: 'total_reps', name: 'Общие повторения', icon: '🔢' },
		{ id: 'workouts_count', name: 'Количество тренировок', icon: '💪' },
		{ id: 'streak_days', name: 'Дней подряд', icon: '🔥' },
	];

	onMount(async () => {
		await loadGoals();
	});

	async function loadGoals() {
		try {
			goals = await api.getGoals();
		} catch (error) {
			console.error('Failed to load goals:', error);
		} finally {
			isLoading = false;
		}
	}

	async function createGoal() {
		if (!goalTitle.trim()) return;

		try {
			await api.createGoal({
				goal_type: goalType,
				title: goalTitle,
				target_value: targetValue,
			});

			showCreateForm = false;
			goalTitle = '';
			targetValue = 100;
			await loadGoals();

			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
			}
		} catch (error) {
			console.error('Failed to create goal:', error);
		}
	}

	async function deleteGoal(id: number) {
		try {
			await api.deleteGoal(id);
			goals = goals.filter(g => g.id !== id);

			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
			}
		} catch (error) {
			console.error('Failed to delete goal:', error);
		}
	}

	function getGoalIcon(type: string): string {
		const found = goalTypes.find(t => t.id === type);
		return found?.icon || '🎯';
	}

	let activeGoals = $derived(goals.filter(g => g.is_active));
	let completedGoals = $derived(goals.filter(g => !g.is_active));
</script>

<div class="container">
	<header class="page-header">
		<h1 class="pixel-title">🎯 ЦЕЛИ</h1>
	</header>

	{#if showCreateForm}
		<!-- Create Goal Form -->
		<div class="create-form pixel-card">
			<div class="form-title">НОВАЯ ЦЕЛЬ</div>

			<div class="form-group">
				<label>ТИП ЦЕЛИ</label>
				<div class="goal-types">
					{#each goalTypes as type}
						<button
							class="goal-type-btn"
							class:active={goalType === type.id}
							onclick={() => goalType = type.id}
						>
							{type.icon} {type.name}
						</button>
					{/each}
				</div>
			</div>

			<div class="form-group">
				<label>НАЗВАНИЕ</label>
				<input
					type="text"
					bind:value={goalTitle}
					placeholder="Например: 1000 отжиманий"
					class="pixel-input"
				/>
			</div>

			<div class="form-group">
				<label>ЦЕЛЕВОЕ ЗНАЧЕНИЕ</label>
				<div class="number-input">
					<button onclick={() => targetValue = Math.max(1, targetValue - 10)}>-</button>
					<span>{targetValue}</span>
					<button onclick={() => targetValue += 10}>+</button>
				</div>
			</div>

			<div class="form-actions">
				<button class="pixel-btn" onclick={() => showCreateForm = false}>ОТМЕНА</button>
				<button class="pixel-btn secondary" onclick={createGoal}>СОЗДАТЬ</button>
			</div>
		</div>
	{:else}
		<button class="pixel-btn accent w-full mb-lg" onclick={() => showCreateForm = true}>
			+ НОВАЯ ЦЕЛЬ
		</button>
	{/if}

	{#if isLoading}
		<div class="loading">
			<div class="loading-icon">🎯</div>
			<div class="loading-text">Загрузка целей...</div>
		</div>
	{:else}
		<!-- Active Goals -->
		{#if activeGoals.length > 0}
			<div class="goals-section">
				<h2 class="section-title">📍 АКТИВНЫЕ</h2>
				<div class="goals-list">
					{#each activeGoals as goal}
						<div class="goal-card pixel-card">
							<div class="goal-header">
								<span class="goal-icon">{getGoalIcon(goal.goal_type)}</span>
								<div class="goal-info">
									<div class="goal-title">{goal.title}</div>
									<div class="goal-progress-text">
										{goal.current_value} / {goal.target_value}
									</div>
								</div>
								<button class="delete-btn" onclick={() => deleteGoal(goal.id)}>✕</button>
							</div>
							<div class="pixel-progress">
								<div
									class="pixel-progress-fill"
									style="width: {Math.min(100, goal.progress_percent || 0)}%"
								></div>
							</div>
							<div class="goal-percent">{goal.progress_percent || 0}%</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Completed Goals -->
		{#if completedGoals.length > 0}
			<div class="goals-section">
				<h2 class="section-title">✅ ВЫПОЛНЕННЫЕ</h2>
				<div class="goals-list">
					{#each completedGoals as goal}
						<div class="goal-card pixel-card completed">
							<div class="goal-header">
								<span class="goal-icon">✅</span>
								<div class="goal-info">
									<div class="goal-title">{goal.title}</div>
									<div class="goal-completed-text">Выполнено!</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if activeGoals.length === 0 && completedGoals.length === 0 && !showCreateForm}
			<div class="empty-state">
				<div class="empty-icon">🎯</div>
				<div class="empty-text">У тебя пока нет целей</div>
				<div class="empty-hint">Создай свою первую цель!</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.page-header {
		text-align: center;
		margin-bottom: var(--space-lg);
	}

	.create-form {
		margin-bottom: var(--space-lg);
	}

	.form-title {
		font-size: 12px;
		color: var(--accent);
		text-align: center;
		margin-bottom: var(--space-lg);
	}

	.form-group {
		margin-bottom: var(--space-lg);
	}

	.form-group label {
		display: block;
		font-size: 8px;
		color: var(--text-muted);
		margin-bottom: var(--space-sm);
	}

	.goal-types {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
	}

	.goal-type-btn {
		padding: var(--space-sm) var(--space-md);
		background: var(--bg-dark);
		border: 2px solid var(--border);
		color: var(--text-secondary);
		font-family: 'Press Start 2P', monospace;
		font-size: 8px;
		cursor: pointer;
		text-align: left;
	}

	.goal-type-btn.active {
		border-color: var(--accent);
		color: var(--accent);
	}

	.pixel-input {
		width: 100%;
		padding: var(--space-md);
		background: var(--bg-dark);
		border: 4px solid var(--border);
		color: var(--text-primary);
		font-family: 'Press Start 2P', monospace;
		font-size: 9px;
	}

	.pixel-input::placeholder {
		color: var(--text-muted);
	}

	.number-input {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-md);
	}

	.number-input button {
		width: 40px;
		height: 40px;
		background: var(--bg-dark);
		border: 2px solid var(--border);
		color: var(--text-primary);
		font-size: 16px;
		cursor: pointer;
	}

	.number-input span {
		min-width: 80px;
		text-align: center;
		font-size: 18px;
		color: var(--accent);
	}

	.form-actions {
		display: flex;
		gap: var(--space-md);
		justify-content: center;
	}

	.section-title {
		font-size: 10px;
		color: var(--accent);
		margin-bottom: var(--space-md);
	}

	.goals-section {
		margin-bottom: var(--space-lg);
	}

	.goals-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.goal-card {
		position: relative;
	}

	.goal-card.completed {
		opacity: 0.7;
	}

	.goal-header {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		margin-bottom: var(--space-sm);
	}

	.goal-icon {
		font-size: 24px;
	}

	.goal-info {
		flex: 1;
	}

	.goal-title {
		font-size: 10px;
		color: var(--text-primary);
	}

	.goal-progress-text {
		font-size: 8px;
		color: var(--text-muted);
		margin-top: var(--space-xs);
	}

	.goal-completed-text {
		font-size: 8px;
		color: var(--secondary);
		margin-top: var(--space-xs);
	}

	.delete-btn {
		width: 24px;
		height: 24px;
		background: var(--bg-dark);
		border: 2px solid var(--border);
		color: var(--primary);
		cursor: pointer;
		font-size: 12px;
	}

	.goal-percent {
		font-size: 9px;
		color: var(--secondary);
		text-align: right;
		margin-top: var(--space-xs);
	}

	.loading, .empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 40vh;
		text-align: center;
	}

	.loading-icon, .empty-icon {
		font-size: 48px;
		margin-bottom: var(--space-md);
	}

	.loading-icon {
		animation: bounce 1s infinite;
	}

	.loading-text, .empty-text {
		font-size: 10px;
		color: var(--text-muted);
	}

	.empty-hint {
		font-size: 8px;
		color: var(--text-muted);
		margin-top: var(--space-sm);
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}
</style>
