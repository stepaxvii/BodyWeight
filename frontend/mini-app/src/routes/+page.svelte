<script lang="ts">
	import { base } from '$app/paths';
	import { PixelButton, PixelCard, PixelProgress, PixelIcon } from '$lib/components/ui';
	import QuickExerciseModal from '$lib/components/QuickExerciseModal.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { api } from '$lib/api/client';
	import { onMount } from 'svelte';
	import type { Achievement, Notification } from '$lib/types';

	let recentAchievements = $state<Achievement[]>([]);
	let quickModalOpen = $state(false);
	let lastReward = $state<{ xp: number; coins: number } | null>(null);
	let unreadNotifications = $state(0);
	let notifications = $state<Notification[]>([]);
	let notificationsOpen = $state(false);
	let notificationsLoading = $state(false);

	onMount(async () => {
		await userStore.loadStats();
		const achievements = await api.getAchievements();
		recentAchievements = achievements.filter(a => a.unlocked).slice(0, 3);

		// Load unread notifications count
		try {
			unreadNotifications = await api.getUnreadNotificationCount();
		} catch (e) {
			console.error('Failed to load notifications count:', e);
		}
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

	async function toggleNotifications() {
		notificationsOpen = !notificationsOpen;

		if (notificationsOpen && notifications.length === 0) {
			notificationsLoading = true;
			try {
				notifications = await api.getNotifications(10);
				// Mark as read when opened
				if (unreadNotifications > 0) {
					await api.markNotificationsRead();
					unreadNotifications = 0;
				}
			} catch (e) {
				console.error('Failed to load notifications:', e);
			} finally {
				notificationsLoading = false;
			}
		}
	}

	function closeNotifications() {
		notificationsOpen = false;
	}

	function getNotificationIcon(type: string): string {
		switch (type) {
			case 'friend_request': return 'friend';
			case 'friend_accepted': return 'check';
			case 'daily_reminder': return 'bell';
			case 'inactivity_reminder': return 'warning';
			case 'level_up': return 'level';
			case 'achievement': return 'trophy';
			case 'welcome': return 'star';
			default: return 'bell';
		}
	}
</script>

<div class="page container">
	<!-- Header with user info -->
	<header class="page-header">
		<div class="header-content">
			<div class="user-greeting">
				<span class="greeting-text">С возвращением,</span>
				<span class="user-name">{userStore.displayName}!</span>
			</div>
			<div class="notification-wrapper">
				<button
					type="button"
					class="notification-badge"
					class:has-notifications={unreadNotifications > 0}
					onclick={toggleNotifications}
				>
					<PixelIcon name="bell" size="md" />
					{#if unreadNotifications > 0}
						<span class="badge-count">{unreadNotifications > 9 ? '9+' : unreadNotifications}</span>
					{/if}
				</button>

				{#if notificationsOpen}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div class="notification-overlay" onclick={closeNotifications}></div>
					<div class="notification-dropdown">
						<div class="dropdown-header">
							<span>Уведомления</span>
							<button type="button" class="close-btn" onclick={closeNotifications}>
								<PixelIcon name="close" size="sm" />
							</button>
						</div>
						<div class="dropdown-content">
							{#if notificationsLoading}
								<div class="dropdown-empty">Загрузка...</div>
							{:else if notifications.length === 0}
								<div class="dropdown-empty">Нет уведомлений</div>
							{:else}
								{#each notifications as notification}
									<div class="notification-item" class:unread={!notification.is_read}>
										<div class="notification-icon">
											<PixelIcon name={getNotificationIcon(notification.notification_type)} size="sm" />
										</div>
										<div class="notification-content">
											<span class="notification-title">{notification.title}</span>
											<span class="notification-message">{notification.message}</span>
										</div>
									</div>
								{/each}
							{/if}
						</div>
						{#if notifications.some(n => n.notification_type === 'friend_request' || n.notification_type === 'friend_accepted')}
							<a href="{base}/friends" class="dropdown-footer" onclick={closeNotifications}>
								Перейти к друзьям
							</a>
						{/if}
					</div>
				{/if}
			</div>
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
		margin-bottom: var(--spacing-lg);
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
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

	.notification-wrapper {
		position: relative;
	}

	.notification-badge {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--pixel-border);
		text-decoration: none;
		color: var(--text-secondary);
		transition: all 0.2s;
		cursor: pointer;
	}

	.notification-badge:hover {
		border-color: var(--pixel-accent);
		color: var(--pixel-accent);
	}

	.notification-badge.has-notifications {
		color: var(--pixel-yellow);
		border-color: var(--pixel-yellow);
	}

	.badge-count {
		position: absolute;
		top: -4px;
		right: -4px;
		min-width: 18px;
		height: 18px;
		padding: 0 4px;
		background: var(--pixel-red);
		color: var(--pixel-white);
		font-size: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 2px solid var(--pixel-bg);
	}

	.notification-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		z-index: 100;
	}

	.notification-dropdown {
		position: absolute;
		top: calc(100% + 8px);
		right: 0;
		width: 280px;
		max-height: 400px;
		background: var(--pixel-bg);
		border: 2px solid var(--pixel-border);
		z-index: 101;
		display: flex;
		flex-direction: column;
	}

	.dropdown-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-sm);
		border-bottom: 2px solid var(--pixel-border);
		font-size: var(--font-size-sm);
		text-transform: uppercase;
	}

	.close-btn {
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		padding: 4px;
	}

	.close-btn:hover {
		color: var(--pixel-accent);
	}

	.dropdown-content {
		flex: 1;
		overflow-y: auto;
		max-height: 300px;
	}

	.dropdown-empty {
		padding: var(--spacing-lg);
		text-align: center;
		color: var(--text-secondary);
		font-size: var(--font-size-sm);
	}

	.notification-item {
		display: flex;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm);
		border-bottom: 1px solid var(--pixel-border);
	}

	.notification-item.unread {
		background: var(--pixel-bg-dark);
	}

	.notification-icon {
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--pixel-accent);
		flex-shrink: 0;
	}

	.notification-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}

	.notification-title {
		font-size: var(--font-size-xs);
		color: var(--text-primary);
		font-weight: 500;
	}

	.notification-message {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.dropdown-footer {
		display: block;
		padding: var(--spacing-sm);
		text-align: center;
		color: var(--pixel-accent);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		text-decoration: none;
		border-top: 2px solid var(--pixel-border);
	}

	.dropdown-footer:hover {
		background: var(--pixel-bg-dark);
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
