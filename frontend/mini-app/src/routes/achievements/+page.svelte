<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelCard, PixelIcon, PixelProgress, PixelButton, EmptyState, PixelTabs } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Achievement } from '$lib/types';

	let achievements = $state<Achievement[]>([]);
	let filter = $state<'all' | 'unlocked' | 'locked'>('all');
	let isLoading = $state(false);
	let hasMore = $state(false);
	let total = $state(0);
	let skip = $state(0);
	const limit = 20;

	onMount(async () => {
		await loadAchievements();
	});

	async function loadAchievements(reset = false) {
		if (isLoading) return;
		
		isLoading = true;
		try {
			if (reset) {
				skip = 0;
				achievements = [];
			}

			const response = await api.getAchievements({ skip, limit });
			achievements = reset ? response.items : [...achievements, ...response.items];
			hasMore = response.has_more;
			total = response.total;
			skip = achievements.length;
		} catch (error) {
			console.error('Failed to load achievements:', error);
		} finally {
			isLoading = false;
		}
	}

	async function loadMore() {
		await loadAchievements(false);
		telegram.hapticImpact('light');
	}

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
	}

	const achievementTabs = [
		{ id: 'all' as const, label: 'Все' },
		{ id: 'unlocked' as const, label: 'Открыто' },
		{ id: 'locked' as const, label: 'Закрыто' }
	];

	function getProgressPercent(achievement: Achievement): number {
		if (achievement.unlocked) return 100;
		if (!achievement.progress || !achievement.condition.value) return 0;
		return Math.min(100, Math.floor((achievement.progress / achievement.condition.value) * 100));
	}
</script>

<div class="page container">
	<header class="page-header">
		<h1>Достижения</h1>
		<p class="achievement-count">{unlockedCount} / {total || achievements.length} Получено</p>
	</header>

	<!-- Filter Tabs -->
	<PixelTabs tabs={achievementTabs} activeTab={filter} onTabChange={setFilter} />

	<!-- Achievement Grid -->
	<div class="achievements-grid">
		{#each filteredAchievements() as achievement}
			<PixelCard
				variant={achievement.unlocked ? 'success' : 'default'}
				padding="md"
			>
				<div class="achievement" class:unlocked={achievement.unlocked}>
					<div class="achievement-icon" class:locked={!achievement.unlocked}>
						<img
							src="{base}/sprites/badges/{achievement.slug}.svg"
							alt={achievement.name_ru}
							class="achievement-badge-icon"
						/>
						{#if !achievement.unlocked}
							<div class="lock-overlay">
								<PixelIcon name="lock" size="sm" color="var(--text-muted)" />
							</div>
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
								<PixelIcon name="xp" size="sm" color="var(--pixel-accent)" />
								+{achievement.xp_reward}
							</span>
							<span class="reward coins">
								<PixelIcon name="coin" size="sm" color="var(--pixel-yellow)" />
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

	{#if filteredAchievements().length === 0 && !isLoading}
		<EmptyState
			icon="trophy"
			message="Нет достижений для показа"
		/>
	{/if}

	{#if hasMore && filteredAchievements().length > 0}
		<div class="load-more-container">
			<PixelButton
				variant="secondary"
				onclick={loadMore}
				disabled={isLoading}
				fullWidth
			>
				{#if isLoading}
					Загрузка...
				{:else}
					Загрузить ещё
				{/if}
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

	.achievement-count {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		margin-top: var(--spacing-xs);
	}

	/* Achievement Grid */
	.achievements-grid {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.achievement {
		display: grid;
		grid-template-columns: auto 1fr;
		align-items: center;
		column-gap: var(--spacing-md);
		row-gap: var(--spacing-sm);
	}

	.achievement-icon {
		grid-column: 1;
		grid-row: 1 / -1;
		flex: 0 0 auto;
		width: 52px;
		height: 52px;
		background: var(--pixel-yellow);
		border: var(--border-width) solid var(--border-color);
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.achievement-info,
	.achievement-progress,
	.achievement-rewards,
	.unlock-date {
		grid-column: 2;
	}

	.achievement-icon.locked {
		background: var(--pixel-bg-dark);
		border-color: var(--border-light);
	}

	.achievement-badge-icon {
		width: 70%;
		height: 70%;
		image-rendering: pixelated;
	}

	.achievement-icon.locked .achievement-badge-icon {
		filter: grayscale(1);
		opacity: 0.5;
	}

	.lock-overlay {
		position: absolute;
		bottom: -4px;
		right: -4px;
		background: var(--pixel-card);
		border: 1px solid var(--border-color);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2px;
	}

	.achievement:not(.unlocked) {
		opacity: 0.72;
	}

	.achievement.unlocked .achievement-icon {
		animation: pixel-glow 2s ease-in-out infinite;
	}

	.achievement-info {
		flex: 1;
		min-width: 0;
		text-align: left;
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
		justify-content: flex-start;
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
		color: var(--pixel-accent);
	}

	.reward.coins {
		color: var(--pixel-yellow);
	}

	.unlock-date {
		font-size: 8px;
		color: var(--text-muted);
		text-align: left;
		margin-top: var(--spacing-xs);
	}

	@keyframes pixel-glow {
		0%, 100% { box-shadow: 0 0 4px var(--pixel-yellow); }
		50% { box-shadow: 0 0 12px var(--pixel-yellow); }
	}

	.load-more-container {
		margin-top: var(--spacing-lg);
		padding: 0 var(--spacing-md);
	}
</style>
