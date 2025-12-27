<script lang="ts">
	import { user, getLevelProgress, getXPForNextLevel } from '$lib/stores/user';
	import { base } from '$app/paths';

	let levelProgress = $derived($user ? getLevelProgress($user.experience, $user.level) : 0);
	let xpForNext = $derived($user ? getXPForNextLevel($user.level) : 200);
</script>

<div class="container">
	{#if $user}
		<!-- Header -->
		<header class="hero-header">
			<div class="hero-title">
				<span class="hero-icon">⚔️</span>
				<span>BODYWEIGHT</span>
			</div>
			<div class="hero-subtitle">ВОИН {$user.first_name || $user.username || 'НЕИЗВЕСТНЫЙ'}</div>
		</header>

		<!-- Level Card -->
		<div class="pixel-card level-card">
			<div class="level-header">
				<div class="level-badge-large">
					<span class="level-label">LVL</span>
					<span class="level-value">{$user.level}</span>
				</div>
				<div class="xp-info">
					<div class="xp-text">{$user.experience} / {xpForNext} XP</div>
					<div class="pixel-progress">
						<div class="pixel-progress-fill xp" style="width: {levelProgress}%"></div>
					</div>
				</div>
			</div>
		</div>

		<!-- Stats Grid -->
		<div class="stats-grid">
			<div class="stat-box">
				<div class="stat-icon streak-fire">🔥</div>
				<div class="stat-value">{$user.streak_days}</div>
				<div class="stat-label">ДНЕЙ</div>
			</div>
			<div class="stat-box">
				<div class="stat-icon">💪</div>
				<div class="stat-value">{$user.total_workouts}</div>
				<div class="stat-label">ТРЕНИ</div>
			</div>
			<div class="stat-box">
				<div class="stat-icon">🔢</div>
				<div class="stat-value">{$user.total_reps}</div>
				<div class="stat-label">ПОВТОРЫ</div>
			</div>
		</div>

		<!-- Quick Actions -->
		<div class="quick-actions">
			<a href="{base}/workout" class="action-card primary">
				<div class="action-icon">🎮</div>
				<div class="action-text">
					<div class="action-title">НАЧАТЬ ТРЕНИРОВКУ</div>
					<div class="action-desc">Заработай опыт!</div>
				</div>
			</a>

			<a href="{base}/exercises" class="action-card">
				<div class="action-icon">📋</div>
				<div class="action-text">
					<div class="action-title">УПРАЖНЕНИЯ</div>
					<div class="action-desc">Изучи арсенал</div>
				</div>
			</a>

			<a href="{base}/goals" class="action-card">
				<div class="action-icon">🎯</div>
				<div class="action-text">
					<div class="action-title">ЦЕЛИ</div>
					<div class="action-desc">Ставь задачи</div>
				</div>
			</a>

			<a href="{base}/friends" class="action-card">
				<div class="action-icon">👥</div>
				<div class="action-text">
					<div class="action-title">ДРУЗЬЯ</div>
					<div class="action-desc">Соревнуйся</div>
				</div>
			</a>
		</div>

		<!-- Motivation -->
		<div class="motivation-card pixel-card">
			<div class="motivation-icon">⚡</div>
			<div class="motivation-text">
				{#if $user.streak_days > 0}
					Серия {$user.streak_days} дней! Продолжай в том же духе, воин!
				{:else}
					Начни новую серию тренировок сегодня!
				{/if}
			</div>
		</div>
	{:else}
		<div class="no-user">
			<div class="pixel-text">Загрузка данных воина...</div>
		</div>
	{/if}
</div>

<style>
	.hero-header {
		text-align: center;
		padding: var(--space-lg) 0;
	}

	.hero-title {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-sm);
		font-size: 18px;
		color: var(--accent);
		text-shadow: 4px 4px 0 rgba(0,0,0,0.5);
	}

	.hero-icon {
		font-size: 24px;
	}

	.hero-subtitle {
		font-size: 10px;
		color: var(--text-secondary);
		margin-top: var(--space-sm);
	}

	.level-card {
		background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-medium) 100%);
	}

	.level-header {
		display: flex;
		align-items: center;
		gap: var(--space-md);
	}

	.level-badge-large {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 64px;
		height: 64px;
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
		font-size: 20px;
		color: var(--bg-dark);
	}

	.xp-info {
		flex: 1;
	}

	.xp-text {
		font-size: 10px;
		color: var(--accent);
		margin-bottom: var(--space-sm);
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--space-sm);
		margin-top: var(--space-md);
	}

	.stat-box {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: var(--space-md);
		background: var(--bg-card);
		border: 4px solid var(--border);
	}

	.stat-icon {
		font-size: 24px;
		margin-bottom: var(--space-xs);
	}

	.stat-value {
		font-size: 16px;
		color: var(--accent);
	}

	.stat-label {
		font-size: 7px;
		color: var(--text-muted);
		margin-top: var(--space-xs);
	}

	.quick-actions {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--space-sm);
		margin-top: var(--space-lg);
	}

	.action-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: var(--space-md);
		background: var(--bg-card);
		border: 4px solid var(--border);
		text-decoration: none;
		color: var(--text-primary);
		transition: all 0.1s;
	}

	.action-card:hover {
		border-color: var(--accent);
		transform: translateY(-2px);
	}

	.action-card.primary {
		grid-column: span 2;
		flex-direction: row;
		gap: var(--space-md);
		background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
		border-color: var(--primary-dark);
	}

	.action-icon {
		font-size: 28px;
	}

	.action-text {
		text-align: center;
	}

	.action-card.primary .action-text {
		text-align: left;
	}

	.action-title {
		font-size: 10px;
		color: var(--text-primary);
	}

	.action-desc {
		font-size: 7px;
		color: var(--text-secondary);
		margin-top: var(--space-xs);
	}

	.action-card.primary .action-desc {
		color: rgba(255,255,255,0.8);
	}

	.motivation-card {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		margin-top: var(--space-lg);
		background: linear-gradient(135deg, var(--bg-light) 0%, var(--bg-medium) 100%);
	}

	.motivation-icon {
		font-size: 24px;
	}

	.motivation-text {
		font-size: 8px;
		line-height: 1.6;
		color: var(--text-secondary);
	}

	.no-user {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 50vh;
	}
</style>
