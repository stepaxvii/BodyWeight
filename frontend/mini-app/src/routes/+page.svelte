<script lang="ts">
	import { base } from '$app/paths';
	import { PixelButton, PixelCard, PixelProgress, PixelIcon } from '$lib/components/ui';
	import QuickExerciseModal from '$lib/components/QuickExerciseModal.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { api } from '$lib/api/client';
	import { onMount } from 'svelte';
	import type { Achievement } from '$lib/types';

	let recentAchievements = $state<Achievement[]>([]);
	let quickModalOpen = $state(false);
	let lastReward = $state<{ xp: number; coins: number } | null>(null);

	onMount(async () => {
		await userStore.loadStats();
		const achievements = await api.getAchievements();
		recentAchievements = achievements.filter(a => a.unlocked).slice(0, 3);
	});

	// Level XP calculation - use store computed values
	const xpInLevel = $derived(userStore.xp - userStore.xpForCurrentLevel);
	const xpNeeded = $derived(userStore.xpForNextLevel - userStore.xpForCurrentLevel);

	function handleQuickSave(xp: number, coins: number) {
		lastReward = { xp, coins };
		setTimeout(() => {
			lastReward = null;
		}, 3000);
	}
</script>

<div class="page container">
	<!-- Header with user info -->
	<header class="page-header">
		<div class="user-greeting">
			<span class="greeting-text">С возвращением,</span>
			<span class="user-name">{userStore.displayName}!</span>
		</div>
	</header>

	<!-- Stats Row -->
	<section class="stats-row">
		<PixelCard padding="sm">
			<div class="stat">
				<PixelIcon name="level" size="lg" color="var(--pixel-accent)" />
				<div class="stat-info">
					<span class="stat-value">{userStore.level}</span>
					<span class="stat-label">Уровень</span>
				</div>
			</div>
		</PixelCard>

		<PixelCard padding="sm">
			<div class="stat">
				<PixelIcon name="streak" size="lg" color="var(--pixel-yellow)" />
				<div class="stat-info">
					<span class="stat-value">{userStore.streak}</span>
					<span class="stat-label">Серия</span>
				</div>
			</div>
		</PixelCard>

		<PixelCard padding="sm">
			<div class="stat">
				<PixelIcon name="coin" size="lg" color="var(--pixel-orange)" />
				<div class="stat-info">
					<span class="stat-value">{userStore.coins}</span>
					<span class="stat-label">Монеты</span>
				</div>
			</div>
		</PixelCard>
	</section>

	<!-- XP Progress -->
	<section class="xp-section">
		<PixelCard>
			<div class="xp-header">
				<div class="xp-title">
					<PixelIcon name="xp" color="var(--pixel-blue)" />
					<span>Опыт</span>
				</div>
				<span class="xp-total">{userStore.xp} XP</span>
			</div>
			<PixelProgress
				value={xpInLevel}
				max={xpNeeded}
				variant="xp"
				showLabel
				size="lg"
			/>
			<div class="xp-footer">
				<span class="text-muted">До следующего уровня: {xpNeeded - xpInLevel} XP</span>
			</div>
		</PixelCard>
	</section>

	<!-- Quick Start Buttons -->
	<section class="action-section">
		<div class="action-buttons">
			<a href="{base}/workout" class="start-workout-link">
				<PixelButton variant="primary" size="lg" fullWidth>
					<PixelIcon name="play" />
					Тренировка
				</PixelButton>
			</a>
			<PixelButton variant="secondary" size="lg" fullWidth onclick={() => quickModalOpen = true}>
				<PixelIcon name="plus" />
				Быстрая запись
			</PixelButton>
		</div>
		{#if lastReward}
			<div class="reward-toast">
				<span>+{lastReward.xp} XP</span>
				<span>+{lastReward.coins} монет</span>
			</div>
		{/if}
	</section>

	<!-- Today's Stats -->
	{#if userStore.stats}
		<section class="today-section">
			<h3 class="section-title">На этой неделе</h3>
			<div class="today-grid">
				<PixelCard padding="sm">
					<div class="today-stat">
						<span class="today-value">{userStore.stats.this_week_workouts}</span>
						<span class="today-label">Тренировок</span>
					</div>
				</PixelCard>
				<PixelCard padding="sm">
					<div class="today-stat">
						<span class="today-value">{userStore.stats.this_week_xp}</span>
						<span class="today-label">Получено XP</span>
					</div>
				</PixelCard>
			</div>
		</section>
	{/if}

	<!-- Recent Achievements -->
	{#if recentAchievements.length > 0}
		<section class="achievements-section">
			<div class="section-header">
				<h3 class="section-title">Последние достижения</h3>
				<a href="{base}/achievements" class="see-all">Все</a>
			</div>
			<div class="achievements-list">
				{#each recentAchievements as achievement}
					<PixelCard padding="sm" hoverable>
						<div class="achievement-item">
							<div class="achievement-icon">
								<PixelIcon name="trophy" size="lg" color="var(--pixel-yellow)" />
							</div>
							<div class="achievement-info">
								<span class="achievement-name">{achievement.name_ru}</span>
								<span class="achievement-desc">{achievement.description_ru}</span>
							</div>
						</div>
					</PixelCard>
				{/each}
			</div>
		</section>
	{/if}
</div>

<QuickExerciseModal
	bind:open={quickModalOpen}
	onclose={() => quickModalOpen = false}
	onsave={handleQuickSave}
/>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	.page-header {
		text-align: center;
		margin-bottom: var(--spacing-lg);
	}

	.user-greeting {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.greeting-text {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.user-name {
		font-size: var(--font-size-lg);
		color: var(--pixel-accent);
	}

	/* Stats Row */
	.stats-row {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-md);
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.stat-info {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: var(--font-size-md);
		color: var(--text-primary);
	}

	.stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	/* XP Section */
	.xp-section {
		margin-bottom: var(--spacing-lg);
	}

	.xp-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-sm);
	}

	.xp-title {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-sm);
		text-transform: uppercase;
	}

	.xp-total {
		font-size: var(--font-size-sm);
		color: var(--pixel-blue);
	}

	.xp-footer {
		margin-top: var(--spacing-xs);
		font-size: var(--font-size-xs);
	}

	/* Action Section */
	.action-section {
		margin-bottom: var(--spacing-lg);
	}

	.action-buttons {
		display: flex;
		gap: var(--spacing-sm);
	}

	.start-workout-link {
		text-decoration: none;
		display: block;
		flex: 1;
	}

	.reward-toast {
		display: flex;
		justify-content: center;
		gap: var(--spacing-md);
		margin-top: var(--spacing-sm);
		padding: var(--spacing-sm);
		background: var(--pixel-green);
		color: var(--pixel-white);
		font-size: var(--font-size-sm);
		animation: slideIn 0.3s ease-out;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* Today Section */
	.today-section {
		margin-bottom: var(--spacing-lg);
	}

	.section-title {
		font-size: var(--font-size-sm);
		margin-bottom: var(--spacing-sm);
		text-transform: uppercase;
	}

	.today-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-sm);
	}

	.today-stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.today-value {
		font-size: var(--font-size-xl);
		color: var(--pixel-green);
	}

	.today-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	/* Achievements Section */
	.achievements-section {
		margin-bottom: var(--spacing-lg);
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-sm);
	}

	.see-all {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
		text-transform: uppercase;
	}

	.achievements-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.achievement-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.achievement-icon {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--pixel-yellow);
	}

	.achievement-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.achievement-name {
		font-size: var(--font-size-xs);
		color: var(--text-primary);
	}

	.achievement-desc {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}
</style>
