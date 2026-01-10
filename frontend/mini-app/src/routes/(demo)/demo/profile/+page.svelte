<script lang="ts">
	import { base } from '$app/paths';
	import { PixelCard, PixelProgress, PixelIcon, PixelAvatar } from '$lib/components/ui';
	import ActivityCalendar from '$lib/components/ActivityCalendar.svelte';
	import type { DayActivity } from '$lib/types';

	// Demo data - impressive stats
	const demoUser = {
		displayName: 'PixelWarrior',
		level: 42,
		xp: 18750,
		coins: 2340,
		streak: 28,
		max_streak: 35,
		avatar_id: 'flame-phoenix'
	};

	// XP calculation for level 42
	const xpForCurrentLevel = 17500;
	const xpForNextLevel = 20000;
	const xpInLevel = demoUser.xp - xpForCurrentLevel;
	const xpNeeded = xpForNextLevel - xpForCurrentLevel;

	// Demo achievements (unlocked)
	const demoAchievements = [
		{ slug: 'first-workout', name_ru: 'Первая тренировка' },
		{ slug: 'streak-7', name_ru: '7 дней подряд' },
		{ slug: 'streak-30', name_ru: '30 дней подряд' },
		{ slug: 'level-10', name_ru: 'Уровень 10' },
		{ slug: 'level-25', name_ru: 'Уровень 25' },
		{ slug: 'pushups-100', name_ru: '100 отжиманий' },
		{ slug: 'pushups-1000', name_ru: '1000 отжиманий' },
		{ slug: 'pullups-master', name_ru: 'Мастер подтягиваний' },
		{ slug: 'early-bird', name_ru: 'Ранняя пташка' },
		{ slug: 'night-owl', name_ru: 'Ночная сова' },
		{ slug: 'workout-10', name_ru: '10 тренировок' },
		{ slug: 'workout-50', name_ru: '50 тренировок' },
		{ slug: 'workout-100', name_ru: '100 тренировок' },
		{ slug: 'xp-1000', name_ru: '1000 XP' },
		{ slug: 'xp-10000', name_ru: '10000 XP' },
		{ slug: 'plank-master', name_ru: 'Мастер планки' }
	];

	const totalAchievements = 24;

	// Generate activity data for the year (realistic pattern)
	function generateActivityData(): Record<string, DayActivity> {
		const days: Record<string, DayActivity> = {};
		const today = new Date();
		const startOfYear = new Date(today.getFullYear(), 0, 1);

		for (let d = new Date(startOfYear); d <= today; d.setDate(d.getDate() + 1)) {
			const dateStr = d.toISOString().split('T')[0];
			const dayOfWeek = d.getDay();
			const random = Math.random();

			// More likely to workout on weekdays, skip some days
			if (dayOfWeek === 0 || dayOfWeek === 6) {
				// Weekend - 60% chance
				if (random < 0.6) {
					days[dateStr] = {
						workouts: Math.floor(Math.random() * 2) + 1,
						total_xp: Math.floor(Math.random() * 150) + 50
					};
				}
			} else {
				// Weekday - 85% chance
				if (random < 0.85) {
					days[dateStr] = {
						workouts: Math.floor(Math.random() * 3) + 1,
						total_xp: Math.floor(Math.random() * 200) + 80
					};
				}
			}
		}

		// Ensure last 28 days have activity (streak)
		for (let i = 0; i < 28; i++) {
			const d = new Date(today);
			d.setDate(d.getDate() - i);
			const dateStr = d.toISOString().split('T')[0];
			if (!days[dateStr]) {
				days[dateStr] = {
					workouts: Math.floor(Math.random() * 2) + 1,
					total_xp: Math.floor(Math.random() * 150) + 50
				};
			}
		}

		return days;
	}

	const activityData = generateActivityData();
</script>

<div class="page container">
	<!-- Profile Header -->
	<header class="profile-header">
		<div class="avatar-wrapper">
			<PixelAvatar
				avatarId={demoUser.avatar_id}
				size="xl"
				borderColor="var(--pixel-accent)"
			/>
		</div>
		<div class="header-info">
			<h1 class="username">{demoUser.displayName}</h1>
			<p class="user-title">Легенда фитнеса</p>
			<div class="level-info">
				<span class="level-badge">Ур.{demoUser.level}</span>
				<div class="xp-mini">
					<PixelProgress value={xpInLevel} max={xpNeeded} variant="xp" size="sm" />
					<span class="xp-text">{xpInLevel}/{xpNeeded} XP</span>
				</div>
			</div>
		</div>
	</header>

	<!-- Activity Calendar -->
	<section class="activity-section">
		<ActivityCalendar
			activityData={activityData}
			year={new Date().getFullYear()}
		/>
	</section>

	<!-- Stats Row -->
	<section class="stats-section">
		<div class="stats-row">
			<div class="stat-item">
				<PixelIcon name="xp" size="md" color="var(--pixel-blue)" />
				<span class="stat-value">{demoUser.xp.toLocaleString()}</span>
			</div>
			<div class="stat-item">
				<PixelIcon name="coin" size="md" color="var(--pixel-orange)" />
				<span class="stat-value">{demoUser.coins.toLocaleString()}</span>
			</div>
			<div class="stat-item">
				<PixelIcon name="streak" size="md" color="var(--pixel-yellow)" />
				<span class="stat-value">{demoUser.streak}</span>
			</div>
			<div class="stat-item">
				<PixelIcon name="trophy" size="md" color="var(--pixel-accent)" />
				<span class="stat-value">{demoAchievements.length}</span>
			</div>
		</div>
	</section>

	<!-- Badges Section -->
	<section class="badges-section">
		<div class="badges-card">
			<div class="badges-header">
				<PixelIcon name="trophy" size="md" color="var(--pixel-accent)" />
				<span class="badges-title">Значки</span>
				<span class="badges-count">{demoAchievements.length}/{totalAchievements}</span>
			</div>
			<div class="badges-grid">
				{#each demoAchievements as achievement}
					<div class="badge-item" title={achievement.name_ru}>
						<img
							src="{base}/sprites/badges/{achievement.slug}.svg"
							alt={achievement.name_ru}
							class="badge-icon"
						/>
					</div>
				{/each}
				<a href="{base}/achievements" class="badge-item badge-more">
					<span>+{totalAchievements - demoAchievements.length}</span>
				</a>
			</div>
		</div>
	</section>

	<!-- Streak Section -->
	<section class="streak-section">
		<div class="streak-card">
			<div class="streak-left">
				<PixelIcon name="streak" size="lg" color="var(--pixel-yellow)" />
				<div class="streak-numbers">
					<span class="streak-current">{demoUser.streak} дней</span>
					<span class="streak-max">Рекорд: {demoUser.max_streak}</span>
				</div>
			</div>
			<div class="streak-visual">
				{#each Array(7) as _, i}
					<div class="streak-day active"></div>
				{/each}
			</div>
		</div>
	</section>

	<!-- Friends Link -->
	<section class="links-section">
		<a href="{base}/friends" class="link-item">
			<PixelCard hoverable>
				<div class="link-content">
					<PixelIcon name="friend" color="var(--pixel-cyan)" />
					<span>Друзья</span>
					<span class="link-count">12</span>
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

	.profile-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		margin-bottom: var(--spacing-md);
	}

	.avatar-wrapper {
		flex-shrink: 0;
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

	.activity-section {
		margin-bottom: var(--spacing-md);
	}

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
</style>
