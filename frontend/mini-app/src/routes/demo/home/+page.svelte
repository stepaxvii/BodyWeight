<script lang="ts">
	import { base } from '$app/paths';
	import { PixelCard, PixelProgress, PixelIcon } from '$lib/components/ui';

	// Demo user data
	const demoUser = {
		displayName: 'PixelWarrior',
		level: 42,
		xp: 18750,
		coins: 2340,
		streak: 28
	};

	// XP calculation
	const xpForCurrentLevel = 17500;
	const xpForNextLevel = 20000;
	const xpInLevel = demoUser.xp - xpForCurrentLevel;
	const xpNeeded = xpForNextLevel - xpForCurrentLevel;

	// Weekly stats
	const weeklyStats = {
		this_week_workouts: 5,
		this_week_xp: 847
	};

	// Recent achievements
	const recentAchievements = [
		{ slug: 'streak-30', name_ru: '30 дней подряд', description_ru: 'Тренируйся 30 дней без перерыва' },
		{ slug: 'pushups-1000', name_ru: '1000 отжиманий', description_ru: 'Выполни 1000 отжиманий всего' },
		{ slug: 'level-40', name_ru: 'Уровень 40', description_ru: 'Достигни 40 уровня' }
	];

	// Time-based greeting
	function getGreeting() {
		const hour = new Date().getHours();
		if (hour < 6) return 'Доброй ночи';
		if (hour < 12) return 'Доброе утро';
		if (hour < 18) return 'Добрый день';
		return 'Добрый вечер';
	}

	const greeting = getGreeting();
</script>

<div class="page container">
	<!-- Header -->
	<header class="page-header">
		<div class="header-left">
			<span class="greeting-text">{greeting}, {demoUser.displayName}!</span>
			<div class="level-badge">
				<PixelIcon name="level" size="sm" color="var(--pixel-accent)" />
				<span>Ур.{demoUser.level}</span>
			</div>
		</div>
		<div class="notification-wrapper">
			<button type="button" class="notification-badge has-notifications">
				<PixelIcon name="bell" size="md" />
				<span class="badge-count">3</span>
			</button>
		</div>
	</header>

	<!-- Main Workout Button -->
	<section class="main-action">
		<a href="{base}/workout" class="workout-card">
			<div class="workout-card-content">
				<div class="workout-icon">
					<PixelIcon name="workout" size="xl" color="var(--pixel-accent)" />
				</div>
				<div class="workout-text">
					<span class="workout-title">Начать тренировку</span>
					<span class="workout-subtitle">Выбери программу или упражнения</span>
				</div>
				<div class="workout-arrow">
					<PixelIcon name="play" size="lg" />
				</div>
			</div>
		</a>
		<button class="quick-record-btn">
			<PixelIcon name="plus" size="sm" />
			<span>Быстрая запись</span>
		</button>
	</section>

	<!-- Progress Card -->
	<section class="progress-section">
		<div class="progress-card">
			<div class="progress-header">
				<div class="progress-level">
					<span class="level-number">{demoUser.level}</span>
					<span class="level-label">Уровень</span>
				</div>
				<div class="progress-xp">
					<PixelProgress value={xpInLevel} max={xpNeeded} variant="xp" size="md" />
					<span class="xp-label">{xpInLevel}/{xpNeeded} XP до следующего</span>
				</div>
			</div>
		</div>
	</section>

	<!-- Stats Row -->
	<section class="stats-section">
		<div class="stats-row">
			<div class="stat-item">
				<PixelIcon name="xp" size="md" color="var(--pixel-blue)" />
				<div class="stat-info">
					<span class="stat-value">{demoUser.xp.toLocaleString()}</span>
					<span class="stat-label">XP</span>
				</div>
			</div>
			<div class="stat-divider"></div>
			<div class="stat-item">
				<PixelIcon name="streak" size="md" color="var(--pixel-yellow)" />
				<div class="stat-info">
					<span class="stat-value">{demoUser.streak}</span>
					<span class="stat-label">Серия</span>
				</div>
			</div>
			<div class="stat-divider"></div>
			<div class="stat-item">
				<PixelIcon name="coin" size="md" color="var(--pixel-orange)" />
				<div class="stat-info">
					<span class="stat-value">{demoUser.coins.toLocaleString()}</span>
					<span class="stat-label">Монеты</span>
				</div>
			</div>
		</div>
	</section>

	<!-- Weekly Stats -->
	<section class="weekly-section">
		<h3 class="section-title">Эта неделя</h3>
		<div class="weekly-row">
			<div class="weekly-stat">
				<PixelIcon name="workout" size="md" color="var(--pixel-green)" />
				<span class="weekly-value">{weeklyStats.this_week_workouts}</span>
				<span class="weekly-label">тренировок</span>
			</div>
			<div class="weekly-stat">
				<PixelIcon name="xp" size="md" color="var(--pixel-blue)" />
				<span class="weekly-value">{weeklyStats.this_week_xp}</span>
				<span class="weekly-label">XP</span>
			</div>
		</div>
	</section>

	<!-- Recent Achievements -->
	<section class="achievements-section">
		<div class="section-header">
			<h3 class="section-title">Новые достижения</h3>
			<a href="{base}/achievements" class="section-link">Все</a>
		</div>
		<div class="achievements-list">
			{#each recentAchievements as achievement}
				<div class="achievement-item">
					<div class="achievement-icon">
						<img
							src="{base}/sprites/badges/{achievement.slug}.svg"
							alt={achievement.name_ru}
							class="achievement-badge"
						/>
					</div>
					<div class="achievement-info">
						<span class="achievement-name">{achievement.name_ru}</span>
						<span class="achievement-desc">{achievement.description_ru}</span>
					</div>
				</div>
			{/each}
		</div>
	</section>
</div>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-md);
	}

	.header-left {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.greeting-text {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
	}

	.level-badge {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		background: var(--pixel-bg-dark);
		padding: 2px 8px;
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
		width: fit-content;
	}

	.notification-wrapper {
		position: relative;
	}

	.notification-badge {
		position: relative;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-xs);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.notification-badge.has-notifications {
		border-color: var(--pixel-accent);
	}

	.badge-count {
		position: absolute;
		top: -4px;
		right: -4px;
		background: var(--pixel-red);
		color: white;
		font-size: 10px;
		min-width: 16px;
		height: 16px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 4px;
	}

	.main-action {
		margin-bottom: var(--spacing-md);
	}

	.workout-card {
		display: block;
		text-decoration: none;
		background: var(--pixel-card);
		border: 2px solid var(--pixel-accent);
		padding: var(--spacing-md);
	}

	.workout-card-content {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.workout-icon {
		flex-shrink: 0;
	}

	.workout-text {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.workout-title {
		font-size: var(--font-size-md);
		color: var(--pixel-accent);
		text-transform: uppercase;
	}

	.workout-subtitle {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.workout-arrow {
		color: var(--pixel-accent);
		opacity: 0.7;
	}

	.quick-record-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-xs);
		width: 100%;
		margin-top: var(--spacing-sm);
		padding: var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
		cursor: pointer;
	}

	.progress-section {
		margin-bottom: var(--spacing-md);
	}

	.progress-card {
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-md);
	}

	.progress-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.progress-level {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding-right: var(--spacing-md);
		border-right: 2px solid var(--border-color);
	}

	.level-number {
		font-size: var(--font-size-xl);
		color: var(--pixel-accent);
		line-height: 1;
	}

	.level-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.progress-xp {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.xp-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.stats-section {
		margin-bottom: var(--spacing-md);
	}

	.stats-row {
		display: flex;
		align-items: center;
		justify-content: space-around;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.stat-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.stat-info {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.stat-value {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
		line-height: 1.2;
	}

	.stat-label {
		font-size: 10px;
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.stat-divider {
		width: 2px;
		height: 24px;
		background: var(--border-color);
	}

	.weekly-section {
		margin-bottom: var(--spacing-md);
	}

	.section-title {
		font-size: var(--font-size-sm);
		margin-bottom: var(--spacing-sm);
		text-transform: uppercase;
	}

	.weekly-row {
		display: flex;
		gap: var(--spacing-sm);
	}

	.weekly-stat {
		flex: 1;
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.weekly-value {
		font-size: var(--font-size-lg);
		color: var(--text-primary);
	}

	.weekly-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.achievements-section {
		margin-bottom: var(--spacing-lg);
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-sm);
	}

	.section-link {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
		text-decoration: none;
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
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.achievement-icon {
		width: 40px;
		height: 40px;
		flex-shrink: 0;
	}

	.achievement-badge {
		width: 100%;
		height: 100%;
		image-rendering: pixelated;
	}

	.achievement-info {
		flex: 1;
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
