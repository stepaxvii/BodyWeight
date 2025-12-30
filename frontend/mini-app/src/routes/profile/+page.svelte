<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelCard, PixelProgress, PixelIcon, PixelAvatar, AvatarPicker } from '$lib/components/ui';
	import { userStore } from '$lib/stores/user.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Achievement, AvatarId } from '$lib/types';

	let achievements = $state<Achievement[]>([]);
	let showAvatarPicker = $state(false);

	onMount(async () => {
		await userStore.loadStats();
		achievements = await api.getAchievements();
	});

	const unlockedAchievements = $derived(achievements.filter(a => a.unlocked));
	const unlockedCount = $derived(unlockedAchievements.length);

	// Level XP calculation - use store computed values
	const xpInLevel = $derived(userStore.xp - userStore.xpForCurrentLevel);
	const xpNeeded = $derived(userStore.xpForNextLevel - userStore.xpForCurrentLevel);

	function openAvatarPicker() {
		showAvatarPicker = true;
		telegram.hapticImpact('light');
	}

	function handleAvatarSelect(avatarId: AvatarId) {
		userStore.setAvatar(avatarId);
	}
</script>

<div class="page container">
	<!-- Profile Header -->
	<header class="profile-header">
		<button class="avatar-btn" onclick={openAvatarPicker}>
			<div class="avatar">
				<PixelAvatar
					avatarId={userStore.user?.avatar_id || 'shadow-wolf'}
					size="xl"
					borderColor="var(--pixel-accent)"
				/>
				<div class="avatar-edit">
					<PixelIcon name="settings" size="sm" />
				</div>
			</div>
			<div class="level-badge">Ур.{userStore.level}</div>
		</button>
		<h1 class="username">{userStore.displayName}</h1>
		<p class="user-title">Пиксельный воин</p>
	</header>

	<!-- Avatar Picker Modal -->
	<AvatarPicker
		open={showAvatarPicker}
		currentAvatarId={userStore.user?.avatar_id || 'shadow-wolf'}
		onselect={handleAvatarSelect}
		onclose={() => showAvatarPicker = false}
	/>

	<!-- XP Progress -->
	<section class="xp-section">
		<PixelCard>
			<div class="xp-content">
				<div class="xp-header">
					<span class="xp-label">Уровень {userStore.level}</span>
					<span class="xp-value">{xpInLevel} / {xpNeeded} XP</span>
				</div>
				<PixelProgress value={xpInLevel} max={xpNeeded} variant="xp" size="lg" />
			</div>
		</PixelCard>
	</section>

	<!-- Stats Grid -->
	<section class="stats-section">
		<h3 class="section-title">Статистика</h3>
		<div class="stats-grid">
			<PixelCard padding="sm">
				<div class="stat-item">
					<PixelIcon name="xp" size="lg" color="var(--pixel-blue)" />
					<span class="stat-value">{userStore.xp}</span>
					<span class="stat-label">Всего XP</span>
				</div>
			</PixelCard>
			<PixelCard padding="sm">
				<div class="stat-item">
					<PixelIcon name="coin" size="lg" color="var(--pixel-orange)" />
					<span class="stat-value">{userStore.coins}</span>
					<span class="stat-label">Монеты</span>
				</div>
			</PixelCard>
			<PixelCard padding="sm">
				<div class="stat-item">
					<PixelIcon name="streak" size="lg" color="var(--pixel-yellow)" />
					<span class="stat-value">{userStore.streak}</span>
					<span class="stat-label">Серия</span>
				</div>
			</PixelCard>
			<PixelCard padding="sm">
				<div class="stat-item">
					<PixelIcon name="trophy" size="lg" color="var(--pixel-accent)" />
					<span class="stat-value">{unlockedCount}</span>
					<span class="stat-label">Значки</span>
				</div>
			</PixelCard>
		</div>
	</section>

	<!-- Unlocked Badges -->
	{#if unlockedAchievements.length > 0}
		<section class="badges-section">
			<h3 class="section-title">Значки</h3>
			<div class="badges-grid">
				{#each unlockedAchievements as achievement}
					<div class="badge-item" title={achievement.name_ru}>
						<img
							src="{base}/sprites/badges/{achievement.slug}.svg"
							alt={achievement.name_ru}
							class="badge-icon"
						/>
					</div>
				{/each}
			</div>
			{#if achievements.length > unlockedAchievements.length}
				<a href="{base}/achievements" class="badges-more">
					+{achievements.length - unlockedAchievements.length} ещё
				</a>
			{/if}
		</section>
	{/if}

	<!-- Detailed Stats -->
	{#if userStore.stats}
		<section class="detailed-stats">
			<h3 class="section-title">Активность</h3>
			<PixelCard>
				<div class="detail-list">
					<div class="detail-item">
						<span class="detail-label">Всего тренировок</span>
						<span class="detail-value">{userStore.stats.total_workouts}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">Всего повторений</span>
						<span class="detail-value">{userStore.stats.total_reps}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">Время тренировок</span>
						<span class="detail-value">{Math.floor((userStore.stats.total_time_minutes || 0) / 60)}ч {(userStore.stats.total_time_minutes || 0) % 60}м</span>
					</div>
					{#if userStore.stats.favorite_exercise}
						<div class="detail-item">
							<span class="detail-label">Любимое</span>
							<span class="detail-value">{userStore.stats.favorite_exercise}</span>
						</div>
					{/if}
				</div>
			</PixelCard>
		</section>
	{/if}

	<!-- Streak Info -->
	<section class="streak-section">
		<h3 class="section-title">Серия</h3>
		<PixelCard variant={userStore.streak >= 7 ? 'success' : 'default'}>
			<div class="streak-display">
				<div class="streak-icon">
					<PixelIcon name="streak" size="xl" color="var(--pixel-yellow)" />
				</div>
				<div class="streak-info">
					<span class="streak-current">{userStore.streak} дней</span>
					<span class="streak-max">Рекорд: {userStore.user?.max_streak || 0} дней</span>
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
					<span>Достижения</span>
					<span class="link-count">{unlockedCount}/{achievements.length}</span>
				</div>
			</PixelCard>
		</a>
		<a href="{base}/friends" class="link-item">
			<PixelCard hoverable>
				<div class="link-content">
					<PixelIcon name="friend" color="var(--pixel-cyan)" />
					<span>Друзья</span>
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

	.avatar-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		position: relative;
		display: inline-block;
		margin-bottom: var(--spacing-sm);
	}

	.avatar-btn:hover .avatar-edit {
		opacity: 1;
	}

	.avatar {
		position: relative;
	}

	.avatar-edit {
		position: absolute;
		bottom: 0;
		right: 0;
		width: 20px;
		height: 20px;
		background: var(--pixel-accent);
		border: 2px solid var(--pixel-bg);
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0.8;
		transition: opacity var(--transition-fast);
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

	/* Badges Section */
	.badges-section {
		margin-bottom: var(--spacing-lg);
	}

	.badges-grid {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-sm);
		justify-content: center;
	}

	.badge-item {
		width: 48px;
		height: 48px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		transition: transform var(--transition-fast);
	}

	.badge-item:hover {
		transform: scale(1.1);
		border-color: var(--pixel-accent);
	}

	.badge-icon {
		width: 32px;
		height: 32px;
		image-rendering: pixelated;
	}

	.badges-more {
		display: block;
		text-align: center;
		margin-top: var(--spacing-sm);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-decoration: none;
	}

	.badges-more:hover {
		color: var(--pixel-accent);
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
