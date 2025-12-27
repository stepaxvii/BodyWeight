<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type AchievementWithStatus } from '$lib/api/client';

	let achievements: AchievementWithStatus[] = $state([]);
	let isLoading = $state(true);
	let selectedCategory = $state('all');

	const categories = [
		{ id: 'all', name: 'Все' },
		{ id: 'streak', name: 'Серия' },
		{ id: 'volume', name: 'Объём' },
		{ id: 'record', name: 'Рекорды' },
		{ id: 'level', name: 'Уровень' },
		{ id: 'special', name: 'Особые' },
	];

	onMount(async () => {
		try {
			achievements = await api.getAchievements();
		} catch (error) {
			console.error('Failed to load achievements:', error);
		} finally {
			isLoading = false;
		}
	});

	let filteredAchievements = $derived(
		selectedCategory === 'all'
			? achievements
			: achievements.filter(a => a.category === selectedCategory)
	);

	let unlockedCount = $derived(
		achievements.filter(a => a.is_unlocked).length
	);
</script>

<div class="container">
	<header class="page-header">
		<h1 class="pixel-title">🏆 ДОСТИЖЕНИЯ</h1>
		<div class="achievements-count">
			{unlockedCount} / {achievements.length} ОТКРЫТО
		</div>
	</header>

	<!-- Categories -->
	<div class="categories-scroll">
		{#each categories as cat}
			<button
				class="category-btn"
				class:active={selectedCategory === cat.id}
				onclick={() => selectedCategory = cat.id}
			>
				{cat.name}
			</button>
		{/each}
	</div>

	{#if isLoading}
		<div class="loading">
			<div class="loading-icon">🏆</div>
			<div class="loading-text">Загрузка достижений...</div>
		</div>
	{:else}
		<div class="achievements-grid">
			{#each filteredAchievements as achievement}
				<div class="achievement-card pixel-card" class:unlocked={achievement.is_unlocked}>
					<div class="achievement-icon-wrapper" class:unlocked={achievement.is_unlocked}>
						<span class="achievement-icon">{achievement.icon}</span>
					</div>
					<div class="achievement-info">
						<div class="achievement-name">{achievement.name}</div>
						<div class="achievement-desc">{achievement.description}</div>
						{#if achievement.is_unlocked}
							<div class="achievement-date">
								✅ Получено
							</div>
						{:else}
							<div class="achievement-reward">
								+{achievement.exp_reward} XP
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.page-header {
		text-align: center;
		margin-bottom: var(--space-md);
	}

	.achievements-count {
		font-size: 10px;
		color: var(--text-muted);
		margin-top: var(--space-sm);
	}

	.categories-scroll {
		display: flex;
		gap: var(--space-xs);
		overflow-x: auto;
		padding: var(--space-sm) 0;
		margin-bottom: var(--space-lg);
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

	.achievements-grid {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.achievement-card {
		display: flex;
		gap: var(--space-md);
		opacity: 0.6;
	}

	.achievement-card.unlocked {
		opacity: 1;
	}

	.achievement-icon-wrapper {
		width: 56px;
		height: 56px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--bg-dark);
		border: 4px solid var(--border);
		flex-shrink: 0;
	}

	.achievement-icon-wrapper.unlocked {
		background: linear-gradient(135deg, var(--accent) 0%, var(--warning) 100%);
		border-color: #cc8800;
		animation: glow 2s infinite;
	}

	.achievement-icon {
		font-size: 28px;
	}

	.achievement-info {
		flex: 1;
	}

	.achievement-name {
		font-size: 10px;
		color: var(--text-primary);
		margin-bottom: var(--space-xs);
	}

	.achievement-desc {
		font-size: 8px;
		color: var(--text-muted);
		line-height: 1.5;
		margin-bottom: var(--space-sm);
	}

	.achievement-date {
		font-size: 8px;
		color: var(--secondary);
	}

	.achievement-reward {
		font-size: 8px;
		color: var(--accent);
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}

	@keyframes glow {
		0%, 100% { box-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }
		50% { box-shadow: 0 0 20px rgba(255, 215, 0, 0.8); }
	}
</style>
