<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelCard, PixelProgress, PixelIcon, PixelButton } from '$lib/components/ui';
	import { userStore } from '$lib/stores/user';
	import { api } from '$lib/api/client';
	import type { Achievement } from '$lib/types';

	let achievements = $state<Achievement[]>([]);

	onMount(async () => {
		await userStore.loadStats();
		achievements = await api.getAchievements();
	});

	const unlockedCount = $derived(achievements.filter(a => a.unlocked).length);

	// Level XP calculation
	const currentLevelXp = $derived(100 * userStore.level * userStore.level);
	const nextLevelXp = $derived(100 * (userStore.level + 1) * (userStore.level + 1));
	const xpInLevel = $derived(userStore.xp - currentLevelXp);
	const xpNeeded = $derived(nextLevelXp - currentLevelXp);
</script>

<div class="page container">
	<!-- Profile Header -->
	<header class="profile-header">
		<div class="avatar">
			<div class="avatar-placeholder">
				<PixelIcon name="profile" size="xl" />
			</div>
			<div class="level-badge">Lv.{userStore.level}</div>
		</div>
		<h1 class="username">{userStore.displayName}</h1>
		<p class="user-title">Pixel Warrior</p>
	</header>

	<!-- XP Progress -->
	<section class="xp-section">
		<PixelCard>
			<div class="xp-content">
				<div class="xp-header">
					<span class="xp-label">Level {userStore.level}</span>
					<span class="xp-value">{xpInLevel} / {xpNeeded} XP</span>
				</div>
				<PixelProgress value={xpInLevel} max={xpNeeded} variant="xp" size="lg" />
			</div>
		</PixelCard>
	</section>

	<!-- Stats Grid -->
	<section class="stats-section">
		<h3 class="section-title">Statistics</h3>
		<div class="stats-grid">
			<PixelCard padding="sm">
				<div class="stat-item">
					<PixelIcon name="xp" size="lg" color="var(--pixel-blue)" />
					<span class="stat-value">{userStore.xp}</span>
					<span class="stat-label">Total XP</span>
				</div>
			</PixelCard>
			<PixelCard padding="sm">
				<div class="stat-item">
					<PixelIcon name="coin" size="lg" color="var(--pixel-orange)" />
					<span class="stat-value">{userStore.coins}</span>
					<span class="stat-label">Coins</span>
				</div>
			</PixelCard>
			<PixelCard padding="sm">
				<div class="stat-item">
					<PixelIcon name="streak" size="lg" color="var(--pixel-yellow)" />
					<span class="stat-value">{userStore.streak}</span>
					<span class="stat-label">Streak</span>
				</div>
			</PixelCard>
			<PixelCard padding="sm">
				<div class="stat-item">
					<PixelIcon name="trophy" size="lg" color="var(--pixel-accent)" />
					<span class="stat-value">{unlockedCount}</span>
					<span class="stat-label">Badges</span>
				</div>
			</PixelCard>
		</div>
	</section>

	<!-- Detailed Stats -->
	{#if userStore.stats}
		<section class="detailed-stats">
			<h3 class="section-title">Activity</h3>
			<PixelCard>
				<div class="detail-list">
					<div class="detail-item">
						<span class="detail-label">Total Workouts</span>
						<span class="detail-value">{userStore.stats.total_workouts}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">Total Reps</span>
						<span class="detail-value">{userStore.stats.total_reps}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">Time Trained</span>
						<span class="detail-value">{Math.floor(userStore.stats.total_time_minutes / 60)}h {userStore.stats.total_time_minutes % 60}m</span>
					</div>
					{#if userStore.stats.favorite_exercise}
						<div class="detail-item">
							<span class="detail-label">Favorite</span>
							<span class="detail-value">{userStore.stats.favorite_exercise}</span>
						</div>
					{/if}
				</div>
			</PixelCard>
		</section>
	{/if}

	<!-- Streak Info -->
	<section class="streak-section">
		<h3 class="section-title">Streak</h3>
		<PixelCard variant={userStore.streak >= 7 ? 'success' : 'default'}>
			<div class="streak-display">
				<div class="streak-icon">
					<PixelIcon name="streak" size="xl" color="var(--pixel-yellow)" />
				</div>
				<div class="streak-info">
					<span class="streak-current">{userStore.streak} days</span>
					<span class="streak-max">Best: {userStore.user?.max_streak || 0} days</span>
				</div>
				<div class="streak-visual">
					{#each Array(7) as _, i}
						<div class="streak-day" class:active={i < Math.min(userStore.streak, 7)}>
							{#if i < Math.min(userStore.streak, 7)}
								<PixelIcon name="check" size="sm" color="var(--pixel-green)" />
							{/if}
						</div>
					{/each}
				</div>
			</div>
		</PixelCard>
	</section>

	<!-- Quick Links -->
	<section class="links-section">
		<a href="{base}/achievements" class="link-item">
			<PixelCard hoverable>
				<div class="link-content">
					<PixelIcon name="trophy" color="var(--pixel-yellow)" />
					<span>Achievements</span>
					<span class="link-count">{unlockedCount}/{achievements.length}</span>
				</div>
			</PixelCard>
		</a>
		<a href="{base}/friends" class="link-item">
			<PixelCard hoverable>
				<div class="link-content">
					<PixelIcon name="friend" color="var(--pixel-cyan)" />
					<span>Friends</span>
				</div>
			</PixelCard>
		</a>
	</section>
</div>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	/* Profile Header */
	.profile-header {
		text-align: center;
		margin-bottom: var(--spacing-lg);
	}

	.avatar {
		position: relative;
		display: inline-block;
		margin-bottom: var(--spacing-sm);
	}

	.avatar-placeholder {
		width: 64px;
		height: 64px;
		background: var(--pixel-card);
		border: 2px solid var(--pixel-accent);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.level-badge {
		position: absolute;
		bottom: -8px;
		left: 50%;
		transform: translateX(-50%);
		background: var(--pixel-accent);
		padding: 2px 8px;
		font-size: var(--font-size-xs);
		white-space: nowrap;
	}

	.username {
		font-size: var(--font-size-lg);
		margin-bottom: var(--spacing-xs);
	}

	.user-title {
		font-size: var(--font-size-xs);
		color: var(--pixel-yellow);
		text-transform: uppercase;
	}

	/* Sections */
	.section-title {
		font-size: var(--font-size-sm);
		margin-bottom: var(--spacing-sm);
		text-transform: uppercase;
	}

	/* XP Section */
	.xp-section {
		margin-bottom: var(--spacing-lg);
	}

	.xp-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.xp-header {
		display: flex;
		justify-content: space-between;
		font-size: var(--font-size-xs);
	}

	.xp-label {
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.xp-value {
		color: var(--pixel-blue);
	}

	/* Stats Grid */
	.stats-section {
		margin-bottom: var(--spacing-lg);
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-sm);
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.stat-value {
		font-size: var(--font-size-lg);
	}

	.stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	/* Detailed Stats */
	.detailed-stats {
		margin-bottom: var(--spacing-lg);
	}

	.detail-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.detail-item {
		display: flex;
		justify-content: space-between;
		font-size: var(--font-size-xs);
	}

	.detail-label {
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.detail-value {
		color: var(--text-primary);
	}

	/* Streak Section */
	.streak-section {
		margin-bottom: var(--spacing-lg);
	}

	.streak-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
	}

	.streak-icon {
		animation: pixel-pulse 2s ease-in-out infinite;
	}

	.streak-info {
		text-align: center;
	}

	.streak-current {
		display: block;
		font-size: var(--font-size-lg);
		color: var(--pixel-yellow);
	}

	.streak-max {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.streak-visual {
		display: flex;
		gap: var(--spacing-xs);
	}

	.streak-day {
		width: 24px;
		height: 24px;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.streak-day.active {
		border-color: var(--pixel-green);
		background: rgba(0, 168, 0, 0.2);
	}

	/* Links Section */
	.links-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.link-item {
		text-decoration: none;
	}

	.link-content {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		font-size: var(--font-size-sm);
		text-transform: uppercase;
	}

	.link-count {
		margin-left: auto;
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	@keyframes pixel-pulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.1); }
	}
</style>
