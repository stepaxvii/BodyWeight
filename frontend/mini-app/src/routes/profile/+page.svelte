<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { user, getLevelProgress, getXPForNextLevel } from '$lib/stores/user';
	import { api, type Workout } from '$lib/api/client';

	let workoutHistory: Workout[] = $state([]);
	let isLoading = $state(true);

	onMount(async () => {
		try {
			workoutHistory = await api.getWorkoutHistory(10);
		} catch (error) {
			console.error('Failed to load history:', error);
		} finally {
			isLoading = false;
		}
	});

	let levelProgress = $derived($user ? getLevelProgress($user.experience, $user.level) : 0);
	let xpForNext = $derived($user ? getXPForNextLevel($user.level) : 200);

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('ru-RU', {
			day: 'numeric',
			month: 'short',
		});
	}

	function formatTime(seconds: number): string {
		const hours = Math.floor(seconds / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);
		if (hours > 0) {
			return `${hours}ч ${minutes}м`;
		}
		return `${minutes}м`;
	}
</script>

<div class="container">
	{#if $user}
		<!-- Profile Header -->
		<div class="profile-header pixel-card">
			<div class="profile-avatar">⚔️</div>
			<div class="profile-info">
				<div class="profile-name">{$user.first_name || $user.username || 'ВОИН'}</div>
				{#if $user.username}
					<div class="profile-username">@{$user.username}</div>
				{/if}
			</div>
		</div>

		<!-- Level Progress -->
		<div class="level-section pixel-card">
			<div class="level-header">
				<div class="level-badge-xl">
					<span class="level-label">LVL</span>
					<span class="level-value">{$user.level}</span>
				</div>
				<div class="level-info">
					<div class="level-title">УРОВЕНЬ {$user.level}</div>
					<div class="xp-text">{$user.experience} / {xpForNext} XP</div>
					<div class="pixel-progress mt-sm">
						<div class="pixel-progress-fill xp" style="width: {levelProgress}%"></div>
					</div>
				</div>
			</div>
		</div>

		<!-- Stats -->
		<div class="stats-section">
			<h2 class="section-title">📊 СТАТИСТИКА</h2>
			<div class="stats-grid">
				<div class="stat-card">
					<div class="stat-icon">🔥</div>
					<div class="stat-value">{$user.streak_days}</div>
					<div class="stat-label">ДНЕЙ ПОДРЯД</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon">💪</div>
					<div class="stat-value">{$user.total_workouts}</div>
					<div class="stat-label">ТРЕНИРОВОК</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon">🔢</div>
					<div class="stat-value">{$user.total_reps}</div>
					<div class="stat-label">ПОВТОРЕНИЙ</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon">⏱️</div>
					<div class="stat-value">{formatTime($user.total_time_seconds)}</div>
					<div class="stat-label">ВРЕМЕНИ</div>
				</div>
			</div>
		</div>

		<!-- Recent Workouts -->
		<div class="history-section">
			<h2 class="section-title">📋 ПОСЛЕДНИЕ ТРЕНИРОВКИ</h2>

			{#if isLoading}
				<div class="loading-text">Загрузка...</div>
			{:else if workoutHistory.length === 0}
				<div class="empty-text">Тренировок пока нет</div>
			{:else}
				<div class="history-list">
					{#each workoutHistory as workout}
						<div class="history-item pixel-card">
							<div class="history-date">
								{formatDate(workout.completed_at || workout.started_at)}
							</div>
							<div class="history-info">
								<div class="history-exercises">
									{workout.exercises?.length || 0} упражнений
								</div>
							</div>
							<div class="history-xp">
								+{workout.total_exp} XP
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Settings -->
		<div class="settings-section">
			<h2 class="section-title">⚙️ НАСТРОЙКИ</h2>
			<div class="setting-item pixel-card">
				<span class="setting-label">🔔 Уведомления</span>
				<button
					class="toggle-btn"
					class:active={$user.notifications_enabled}
					onclick={async () => {
						if ($user) {
							try {
								const updated = await api.updateMe({
									notifications_enabled: !$user.notifications_enabled
								});
								$user = updated;
								if (browser) {
									window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
								}
							} catch (e) {
								console.error(e);
							}
						}
					}}
				>
					{$user.notifications_enabled ? 'ВКЛ' : 'ВЫКЛ'}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.profile-header {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-light) 100%);
	}

	.profile-avatar {
		width: 64px;
		height: 64px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--bg-medium);
		border: 4px solid var(--accent);
		font-size: 32px;
	}

	.profile-name {
		font-size: 14px;
		color: var(--text-primary);
	}

	.profile-username {
		font-size: 9px;
		color: var(--text-muted);
		margin-top: var(--space-xs);
	}

	.level-section {
		margin-top: var(--space-md);
	}

	.level-header {
		display: flex;
		gap: var(--space-md);
	}

	.level-badge-xl {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 72px;
		height: 72px;
		background: linear-gradient(180deg, var(--accent) 0%, #cc8800 100%);
		border: 4px solid #996600;
		box-shadow:
			inset 4px 4px 0 rgba(255,255,255,0.4),
			4px 4px 0 rgba(0,0,0,0.3);
	}

	.level-label {
		font-size: 8px;
		color: var(--bg-dark);
	}

	.level-value {
		font-size: 24px;
		color: var(--bg-dark);
	}

	.level-info {
		flex: 1;
	}

	.level-title {
		font-size: 12px;
		color: var(--accent);
		margin-bottom: var(--space-xs);
	}

	.xp-text {
		font-size: 9px;
		color: var(--text-muted);
	}

	.section-title {
		font-size: 10px;
		color: var(--accent);
		margin-bottom: var(--space-md);
		margin-top: var(--space-lg);
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--space-sm);
	}

	.stat-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: var(--space-md);
		background: var(--bg-card);
		border: 4px solid var(--border);
		text-align: center;
	}

	.stat-icon {
		font-size: 24px;
		margin-bottom: var(--space-xs);
	}

	.stat-value {
		font-size: 14px;
		color: var(--accent);
	}

	.stat-label {
		font-size: 7px;
		color: var(--text-muted);
		margin-top: var(--space-xs);
	}

	.history-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
	}

	.history-item {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		padding: var(--space-sm) var(--space-md);
	}

	.history-date {
		font-size: 9px;
		color: var(--text-muted);
		min-width: 60px;
	}

	.history-info {
		flex: 1;
	}

	.history-exercises {
		font-size: 9px;
		color: var(--text-primary);
	}

	.history-xp {
		font-size: 10px;
		color: var(--accent);
	}

	.loading-text, .empty-text {
		font-size: 10px;
		color: var(--text-muted);
		text-align: center;
		padding: var(--space-lg);
	}

	.setting-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.setting-label {
		font-size: 10px;
	}

	.toggle-btn {
		padding: var(--space-sm) var(--space-md);
		background: var(--bg-dark);
		border: 2px solid var(--border);
		color: var(--text-muted);
		font-family: 'Press Start 2P', monospace;
		font-size: 8px;
		cursor: pointer;
	}

	.toggle-btn.active {
		background: var(--secondary);
		border-color: var(--secondary);
		color: var(--bg-dark);
	}
</style>
