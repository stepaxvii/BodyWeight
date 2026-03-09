<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelCard, PixelProgress, PixelIcon, PixelAvatar, PixelModal, AvatarPicker } from '$lib/components/ui';
	import ActivityBarChart from '$lib/components/ActivityBarChart.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Achievement, AvatarId, UserActivity, DayActivity } from '$lib/types';

	let achievements = $state<Achievement[]>([]);
	let showAvatarPicker = $state(false);
	let activityData = $state<UserActivity | null>(null);
	let chartRange = $state<'week' | '2weeks' | 'month'>('week');
	let selectedDay = $state<{ date: string; activity: DayActivity | null } | null>(null);

	onMount(async () => {
		await userStore.loadStats();
		const response = await api.getAllAchievements();
		achievements = response;

		// Load activity data for current year
		try {
			activityData = await api.getUserActivity();
		} catch (err) {
			console.error('Failed to load activity data:', err);
		}
	});

	// Sort by unlock date (newest first)
	const unlockedAchievements = $derived(
		achievements
			.filter(a => a.unlocked)
			.sort((a, b) => {
				if (!a.unlocked_at || !b.unlocked_at) return 0;
				return new Date(b.unlocked_at).getTime() - new Date(a.unlocked_at).getTime();
			})
	);
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

	function handleDayClick(date: string, activity: DayActivity | null) {
		selectedDay = { date, activity };
		telegram.hapticImpact('light');
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('ru-RU', {
			day: 'numeric',
			month: 'long',
			year: 'numeric'
		});
	}
</script>

<div class="page container">
	<!-- Profile Header - Avatar left, Level info right -->
	<header class="profile-header">
		<button class="avatar-btn" onclick={openAvatarPicker}>
			<PixelAvatar
				avatarId={userStore.user?.avatar_id || 'shadow-wolf'}
				size="xl"
				borderColor="var(--pixel-accent)"
			/>
			<div class="avatar-edit">
				<PixelIcon name="settings" size="sm" />
			</div>
		</button>
		<div class="header-info">
			<h1 class="username">{userStore.displayName}</h1>
			<p class="user-title">Пиксельный воин</p>
			<div class="level-info">
				<span class="level-badge">Ур.{userStore.level}</span>
				<div class="xp-mini">
					<PixelProgress value={xpInLevel} max={xpNeeded} variant="xp" size="sm" />
					<span class="xp-text">{xpInLevel}/{xpNeeded} XP</span>
				</div>
			</div>
		</div>
	</header>

	<!-- Avatar Picker Modal -->
	<AvatarPicker
		open={showAvatarPicker}
		currentAvatarId={userStore.user?.avatar_id || 'shadow-wolf'}
		onselect={handleAvatarSelect}
		onclose={() => showAvatarPicker = false}
	/>

	<!-- Activity bar chart: week / 2 weeks / month -->
	{#if activityData}
		<section class="activity-chart-section">
			<h3 class="chart-section-title">Активность</h3>
			<div class="chart-controls">
				<div class="chart-range-btns">
					<button
						class="range-btn"
						class:active={chartRange === 'week'}
						onclick={() => { chartRange = 'week'; telegram.hapticImpact('light'); }}
					>
						7 дней
					</button>
					<button
						class="range-btn"
						class:active={chartRange === '2weeks'}
						onclick={() => { chartRange = '2weeks'; telegram.hapticImpact('light'); }}
					>
						14 дней
					</button>
					<button
						class="range-btn"
						class:active={chartRange === 'month'}
						onclick={() => { chartRange = 'month'; telegram.hapticImpact('light'); }}
					>
						30 дней
					</button>
				</div>
			</div>
			<PixelCard padding="md">
				<ActivityBarChart
					activityData={activityData.days}
					range={chartRange}
					onDayClick={handleDayClick}
				/>
			</PixelCard>
		</section>
	{/if}

	<!-- Stats Row - compact horizontal -->
	<section class="stats-section">
		<div class="stats-row">
			<div class="stat-item">
				<PixelIcon name="xp" size="md" color="var(--pixel-blue)" />
				<span class="stat-value">{userStore.xp}</span>
			</div>
			<div class="stat-item">
				<PixelIcon name="coin" size="md" color="var(--pixel-orange)" />
				<span class="stat-value">{userStore.coins}</span>
			</div>
			<div class="stat-item">
				<PixelIcon name="streak" size="md" color="var(--pixel-yellow)" />
				<span class="stat-value">{userStore.streak}</span>
			</div>
			<div class="stat-item">
				<PixelIcon name="trophy" size="md" color="var(--pixel-accent)" />
				<span class="stat-value">{unlockedCount}</span>
			</div>
		</div>
	</section>

	<!-- Unlocked Badges -->
	{#if unlockedAchievements.length > 0}
		<section class="badges-section">
			<div class="badges-card">
				<div class="badges-header">
					<PixelIcon name="trophy" size="md" color="var(--pixel-accent)" />
					<span class="badges-title">Значки</span>
					<span class="badges-count">{unlockedCount}/{achievements.length}</span>
				</div>
				<div class="badges-grid">
					{#each unlockedAchievements.slice(0, 16) as achievement}
						<div class="badge-item" title={achievement.name_ru}>
							<img
								src="{base}/sprites/badges/{achievement.slug}.svg"
								alt={achievement.name_ru}
								class="badge-icon"
							/>
						</div>
					{/each}
					{#if achievements.length - unlockedCount > 0 || unlockedAchievements.length > 16}
						<a href="{base}/achievements" class="badge-item badge-more">
							<span>+{achievements.length - Math.min(unlockedCount, 16)}</span>
						</a>
					{/if}
				</div>
			</div>
		</section>
	{/if}

	<!-- Streak Info - Compact -->
	<section class="streak-section">
		<div class="streak-card">
			<div class="streak-left">
				<PixelIcon name="streak" size="lg" color="var(--pixel-yellow)" />
				<div class="streak-numbers">
					<span class="streak-current">{userStore.streak} дней</span>
					<span class="streak-max">Рекорд: {userStore.user?.max_streak || 0}</span>
				</div>
			</div>
			<div class="streak-visual">
				{#each Array(7) as _, i}
					<div class="streak-day" class:active={i < Math.min(userStore.streak, 7)}></div>
				{/each}
			</div>
		</div>
	</section>

	<!-- Quick Link - Friends only -->
	<section class="links-section">
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

<!-- Day details modal (from bar chart click) -->
<PixelModal
	open={selectedDay !== null}
	title={selectedDay ? formatDate(selectedDay.date) : ''}
	onclose={() => selectedDay = null}
>
	{#if selectedDay?.activity}
		<div class="day-details">
			<div class="day-stat">
				<PixelIcon name="workout" size="md" color="var(--pixel-accent)" />
				<div class="day-stat-content">
					<span class="day-stat-label">Тренировки</span>
					<span class="day-stat-value">{selectedDay.activity.workouts}</span>
				</div>
			</div>
			<div class="day-stat">
				<PixelIcon name="xp" size="md" color="var(--pixel-blue)" />
				<div class="day-stat-content">
					<span class="day-stat-label">XP заработано</span>
					<span class="day-stat-value">{selectedDay.activity.total_xp}</span>
				</div>
			</div>
		</div>
	{:else}
		<div class="no-activity">
			<PixelIcon name="close" size="lg" color="var(--text-muted)" />
			<p>Нет тренировок в этот день</p>
		</div>
	{/if}
</PixelModal>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	/* Profile Header - horizontal layout */
	.profile-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		margin-bottom: var(--spacing-md);
	}

	.avatar-btn {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		position: relative;
		flex-shrink: 0;
	}

	.avatar-btn:hover .avatar-edit {
		opacity: 1;
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

	.header-info {
		flex: 1;
		min-width: 0;
	}

	.username {
		font-size: var(--font-size-md);
		margin: 0 0 2px 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.user-title {
		font-size: var(--font-size-xs);
		color: var(--pixel-yellow);
		text-transform: uppercase;
		margin: 0 0 var(--spacing-xs) 0;
	}

	.level-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.level-badge {
		background: var(--pixel-accent);
		padding: 2px 8px;
		font-size: var(--font-size-xs);
		white-space: nowrap;
		flex-shrink: 0;
	}

	.xp-mini {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}

	.xp-text {
		font-size: 10px;
		color: var(--text-secondary);
	}

	/* Sections */
	.section-title {
		font-size: var(--font-size-sm);
		margin-bottom: var(--spacing-sm);
		text-transform: uppercase;
	}

	/* Activity chart section */
	.activity-chart-section {
		margin-bottom: var(--spacing-md);
	}

	.chart-section-title {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin: 0 0 var(--spacing-sm) 0;
	}

	.chart-controls {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-sm);
	}

	.chart-range-btns {
		display: flex;
		gap: 4px;
	}

	.range-btn {
		padding: 6px 10px;
		font-size: var(--font-size-xs);
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all 0.15s;
	}

	.range-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.range-btn.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	/* Stats Row - compact horizontal */
	.stats-section {
		margin-bottom: var(--spacing-md);
	}

	.stats-row {
		display: flex;
		justify-content: space-between;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.stat-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.stat-value {
		font-size: var(--font-size-sm);
	}

	/* Badges Section */
	.badges-section {
		margin-bottom: var(--spacing-md);
	}

	.badges-card {
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.badges-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-sm);
	}

	.badges-title {
		font-size: var(--font-size-sm);
		flex: 1;
	}

	.badges-count {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.badges-grid {
		display: grid;
		grid-template-columns: repeat(9, 1fr);
		gap: 4px;
	}

	.badge-item {
		aspect-ratio: 1;
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
		width: 70%;
		height: 70%;
		image-rendering: pixelated;
	}

	.badge-more {
		text-decoration: none;
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.badge-more:hover {
		color: var(--pixel-accent);
		border-color: var(--pixel-accent);
	}

	/* Streak Section - Compact */
	.streak-section {
		margin-bottom: var(--spacing-md);
	}

	.streak-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.streak-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.streak-numbers {
		display: flex;
		flex-direction: column;
	}

	.streak-current {
		font-size: var(--font-size-sm);
		color: var(--pixel-yellow);
	}

	.streak-max {
		font-size: 10px;
		color: var(--text-secondary);
	}

	.streak-visual {
		display: flex;
		gap: 4px;
	}

	.streak-day {
		width: 16px;
		height: 16px;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
	}

	.streak-day.active {
		border-color: var(--pixel-green);
		background: var(--pixel-green);
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

	/* Day details modal */
	.day-details {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-sm) 0;
	}

	.day-stat {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
	}

	.day-stat-content {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.day-stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.day-stat-value {
		font-size: var(--font-size-md);
		color: var(--text-primary);
	}

	.no-activity {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-muted);
		text-align: center;
	}

	.no-activity p {
		margin: 0;
		font-size: var(--font-size-sm);
	}
</style>
