<script lang="ts">
	import { onMount } from 'svelte';
	import { PixelCard, PixelIcon, PixelProgress } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Achievement } from '$lib/types';

	let achievements = $state<Achievement[]>([]);
	let filter = $state<'all' | 'unlocked' | 'locked'>('all');

	onMount(async () => {
		const response = await api.getAllAchievements();
		achievements = response;
	});

	const filteredAchievements = $derived(() => {
		switch (filter) {
			case 'unlocked':
				return achievements.filter(a => a.unlocked);
			case 'locked':
				return achievements.filter(a => !a.unlocked);
			default:
				return achievements;
		}
	});

	const unlockedCount = $derived(achievements.filter(a => a.unlocked).length);

	function setFilter(newFilter: 'all' | 'unlocked' | 'locked') {
		filter = newFilter;
		telegram.hapticImpact('light');
	}

	function getProgressPercent(achievement: Achievement): number {
		if (achievement.unlocked) return 100;
		if (!achievement.progress || !achievement.condition.value) return 0;
		return Math.min(100, Math.floor((achievement.progress / achievement.condition.value) * 100));
	}
</script>

<div class="page container">
	<header class="page-header">
		<h1>Достижения</h1>
		<p class="achievement-count">{unlockedCount} / {achievements.length} Получено</p>
	</header>

	<!-- Filter Tabs -->
	<div class="filters">
		<button
			class="filter-btn"
			class:active={filter === 'all'}
			onclick={() => setFilter('all')}
		>
			Все
		</button>
		<button
			class="filter-btn"
			class:active={filter === 'unlocked'}
			onclick={() => setFilter('unlocked')}
		>
			<PixelIcon name="check" size="sm" />
			Открыто
		</button>
		<button
			class="filter-btn"
			class:active={filter === 'locked'}
			onclick={() => setFilter('locked')}
		>
			<PixelIcon name="lock" size="sm" />
			Закрыто
		</button>
	</div>

	<!-- Achievement Grid -->
	<div class="achievements-grid">
		{#each filteredAchievements() as achievement}
			<PixelCard
				variant={achievement.unlocked ? 'success' : 'default'}
				padding="md"
			>
				<div class="achievement" class:unlocked={achievement.unlocked}>
					<div class="achievement-icon" class:locked={!achievement.unlocked}>
						{#if achievement.unlocked}
							<PixelIcon name="trophy" size="xl" color="var(--pixel-yellow)" />
						{:else}
							<PixelIcon name="lock" size="xl" color="var(--text-muted)" />
						{/if}
					</div>

					<div class="achievement-info">
						<span class="achievement-name">{achievement.name_ru}</span>
						<span class="achievement-desc">{achievement.description_ru}</span>
					</div>

					{#if !achievement.unlocked && achievement.progress !== undefined && achievement.condition.value}
						<div class="achievement-progress">
							<PixelProgress
								value={achievement.progress}
								max={achievement.condition.value}
								size="sm"
								showLabel
							/>
						</div>
					{/if}

					{#if achievement.unlocked}
						<div class="achievement-rewards">
							<span class="reward xp">
								<PixelIcon name="xp" size="sm" color="var(--pixel-blue)" />
								+{achievement.xp_reward}
							</span>
							<span class="reward coins">
								<PixelIcon name="coin" size="sm" color="var(--pixel-orange)" />
								+{achievement.coin_reward}
							</span>
						</div>
					{:else}
						<div class="achievement-rewards locked">
							<span class="reward">
								<PixelIcon name="xp" size="sm" />
								{achievement.xp_reward} XP
							</span>
							<span class="reward">
								<PixelIcon name="coin" size="sm" />
								{achievement.coin_reward}
							</span>
						</div>
					{/if}

					{#if achievement.unlocked && achievement.unlocked_at}
						<div class="unlock-date">
							{new Date(achievement.unlocked_at).toLocaleDateString('ru-RU')}
						</div>
					{/if}
				</div>
			</PixelCard>
		{/each}
	</div>

	{#if filteredAchievements().length === 0}
		<div class="empty-state">
			<PixelIcon name="trophy" size="xl" color="var(--text-muted)" />
			<p>Нет достижений для показа</p>
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

	.achievement-count {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		margin-top: var(--spacing-xs);
	}

	/* Filters */
	.filters {
		display: flex;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-lg);
	}

	.filter-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.filter-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.filter-btn.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent-hover);
		color: var(--text-primary);
	}

	/* Achievement Grid */
	.achievements-grid {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.achievement {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.achievement-icon {
		width: 48px;
		height: 48px;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--pixel-yellow);
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto;
	}

	.achievement-icon.locked {
		border-color: var(--border-color);
		opacity: 0.6;
	}

	.achievement.unlocked .achievement-icon {
		animation: pixel-glow 2s ease-in-out infinite;
	}

	.achievement-info {
		text-align: center;
	}

	.achievement-name {
		display: block;
		font-size: var(--font-size-sm);
		margin-bottom: var(--spacing-xs);
	}

	.achievement:not(.unlocked) .achievement-name {
		color: var(--text-secondary);
	}

	.achievement-desc {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.achievement-progress {
		margin-top: var(--spacing-xs);
	}

	.achievement-rewards {
		display: flex;
		justify-content: center;
		gap: var(--spacing-md);
		margin-top: var(--spacing-xs);
	}

	.achievement-rewards.locked {
		opacity: 0.5;
	}

	.reward {
		display: flex;
		align-items: center;
		gap: 4px;
		font-size: var(--font-size-xs);
	}

	.reward.xp {
		color: var(--pixel-blue);
	}

	.reward.coins {
		color: var(--pixel-orange);
	}

	.unlock-date {
		font-size: 8px;
		color: var(--text-muted);
		text-align: center;
		margin-top: var(--spacing-xs);
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-muted);
		font-size: var(--font-size-sm);
		text-align: center;
	}

	@keyframes pixel-glow {
		0%, 100% { box-shadow: 0 0 4px var(--pixel-yellow); }
		50% { box-shadow: 0 0 12px var(--pixel-yellow); }
	}
</style>
