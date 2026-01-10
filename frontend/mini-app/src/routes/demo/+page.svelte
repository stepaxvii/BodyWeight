<script lang="ts">
	import { PixelCard, PixelIcon, PixelButton, PixelTabs, PixelAvatar } from '$lib/components/ui';
	import ActivityCalendar from '$lib/components/ActivityCalendar.svelte';

	type DemoScreen = 'home' | 'profile' | 'leaderboard';
	let currentScreen = $state<DemoScreen>('home');

	const screens: { id: DemoScreen; label: string }[] = [
		{ id: 'home', label: 'Главная' },
		{ id: 'profile', label: 'Профиль' },
		{ id: 'leaderboard', label: 'Рейтинг' }
	];

	function switchScreen(screen: DemoScreen) {
		currentScreen = screen;
	}

	// ===== HOME DATA =====
	function getGreeting(): string {
		const hour = new Date().getHours();
		if (hour < 12) return 'Доброе утро';
		if (hour < 18) return 'Добрый день';
		return 'Добрый вечер';
	}

	const homeUser = {
		username: 'PixelWarrior',
		level: 42,
		currentXp: 2340,
		xpToNextLevel: 3000,
		avatar_id: 'flame-phoenix'
	};

	const weeklyStats = {
		workouts: 5,
		xpEarned: 847
	};

	const recentAchievements = [
		{ id: 'streak_7', name: 'Неделя огня', icon: 'flame', color: '#ff6b35' },
		{ id: 'total_100', name: 'Сотня', icon: 'trophy', color: '#ffd700' },
		{ id: 'early_bird', name: 'Ранняя пташка', icon: 'sun', color: '#ffaa00' }
	];

	// ===== PROFILE DATA =====
	const profileUser = {
		username: 'PixelWarrior',
		title: 'Легенда фитнеса',
		level: 42,
		currentXp: 2750,
		xpToNextLevel: 3000,
		totalXp: 18750,
		avatar_id: 'flame-phoenix',
		coins: 2340,
		streak: 28,
		maxStreak: 45,
		workoutsCompleted: 156,
		totalExercises: 2847,
		joinedAt: '2024-03-15'
	};

	const unlockedBadges = [
		{ id: 'starter', name: 'Новичок', icon: 'star', rarity: 'common' },
		{ id: 'week_warrior', name: 'Воин недели', icon: 'flame', rarity: 'common' },
		{ id: 'century', name: 'Сотня', icon: 'trophy', rarity: 'rare' },
		{ id: 'early_bird', name: 'Ранняя пташка', icon: 'sun', rarity: 'common' },
		{ id: 'night_owl', name: 'Ночная сова', icon: 'moon', rarity: 'common' },
		{ id: 'streak_master', name: 'Мастер серий', icon: 'flame', rarity: 'epic' },
		{ id: 'iron_will', name: 'Железная воля', icon: 'dumbbell', rarity: 'rare' },
		{ id: 'perfectionist', name: 'Перфекционист', icon: 'check', rarity: 'rare' },
		{ id: 'social', name: 'Душа компании', icon: 'users', rarity: 'common' },
		{ id: 'challenger', name: 'Челленджер', icon: 'target', rarity: 'epic' },
		{ id: 'legend', name: 'Легенда', icon: 'crown', rarity: 'legendary' },
		{ id: 'unstoppable', name: 'Неудержимый', icon: 'bolt', rarity: 'epic' },
		{ id: 'mentor', name: 'Наставник', icon: 'heart', rarity: 'rare' },
		{ id: 'explorer', name: 'Исследователь', icon: 'compass', rarity: 'common' },
		{ id: 'dedicated', name: 'Преданный', icon: 'calendar', rarity: 'rare' },
		{ id: 'champion', name: 'Чемпион', icon: 'medal', rarity: 'legendary' }
	];

	// Generate activity data
	function generateActivityData() {
		const data: Record<string, number> = {};
		const today = new Date();
		for (let i = 0; i < 365; i++) {
			const date = new Date(today);
			date.setDate(date.getDate() - i);
			const dateStr = date.toISOString().split('T')[0];
			if (Math.random() > 0.3) {
				data[dateStr] = Math.floor(Math.random() * 4) + 1;
			}
		}
		return data;
	}
	const activityData = generateActivityData();

	// ===== LEADERBOARD DATA =====
	type LeaderboardTab = 'global' | 'weekly' | 'friends';
	let leaderboardTab = $state<LeaderboardTab>('global');

	const leaderboardData = {
		global: [
			{ rank: 1, username: 'FitMaster', avatar_id: 'flame-phoenix', xp: 45230, level: 67 },
			{ rank: 2, username: 'IronWolf', avatar_id: 'shadow-wolf', xp: 42150, level: 64 },
			{ rank: 3, username: 'PixelWarrior', avatar_id: 'cyber-dragon', xp: 38920, level: 58, isCurrentUser: true },
			{ rank: 4, username: 'StrengthKing', avatar_id: 'frost-bear', xp: 35800, level: 54 },
			{ rank: 5, username: 'GymLegend', avatar_id: 'thunder-tiger', xp: 33450, level: 51 },
			{ rank: 6, username: 'PowerAthlete', avatar_id: 'golden-eagle', xp: 31200, level: 48 },
			{ rank: 7, username: 'MuscleHero', avatar_id: 'ocean-whale', xp: 28900, level: 45 },
			{ rank: 8, username: 'FitnessNinja', avatar_id: 'jungle-monkey', xp: 26750, level: 42 },
			{ rank: 9, username: 'WorkoutPro', avatar_id: 'desert-fox', xp: 24500, level: 39 },
			{ rank: 10, username: 'BodyBuilder', avatar_id: 'night-owl', xp: 22300, level: 36 }
		],
		weekly: [
			{ rank: 1, username: 'PixelWarrior', avatar_id: 'cyber-dragon', xp: 1850, level: 58, isCurrentUser: true },
			{ rank: 2, username: 'FitMaster', avatar_id: 'flame-phoenix', xp: 1720, level: 67 },
			{ rank: 3, username: 'GymLegend', avatar_id: 'thunder-tiger', xp: 1580, level: 51 },
			{ rank: 4, username: 'IronWolf', avatar_id: 'shadow-wolf', xp: 1450, level: 64 },
			{ rank: 5, username: 'PowerAthlete', avatar_id: 'golden-eagle', xp: 1320, level: 48 }
		],
		friends: [
			{ rank: 1, username: 'PixelWarrior', avatar_id: 'cyber-dragon', xp: 38920, level: 58, isCurrentUser: true },
			{ rank: 2, username: 'AlexFit', avatar_id: 'flame-phoenix', xp: 28500, level: 44 },
			{ rank: 3, username: 'MaxPower', avatar_id: 'shadow-wolf', xp: 21300, level: 35 },
			{ rank: 4, username: 'AnnaStrong', avatar_id: 'frost-bear', xp: 15800, level: 27 },
			{ rank: 5, username: 'DimaSport', avatar_id: 'thunder-tiger', xp: 12400, level: 22 }
		]
	};

	const leaderboardTabs = [
		{ id: 'global' as const, label: 'Глобальный' },
		{ id: 'weekly' as const, label: 'Неделя' },
		{ id: 'friends' as const, label: 'Друзья' }
	];

	const leaderboardEntries = $derived(leaderboardData[leaderboardTab]);
</script>

<div class="demo-page container">
	<!-- Screen Switcher -->
	<div class="screen-switcher">
		{#each screens as screen}
			<button
				class="screen-btn"
				class:active={currentScreen === screen.id}
				onclick={() => switchScreen(screen.id)}
			>
				{screen.label}
			</button>
		{/each}
	</div>

	<!-- HOME SCREEN -->
	{#if currentScreen === 'home'}
		<div class="screen home-screen">
			<header class="home-header">
				<div class="user-greeting">
					<PixelAvatar avatarId={homeUser.avatar_id} size="lg" />
					<div class="greeting-text">
						<span class="greeting">{getGreeting()},</span>
						<span class="username">{homeUser.username}!</span>
					</div>
				</div>
				<div class="header-actions">
					<button class="notification-btn">
						<PixelIcon name="bell" size="sm" />
						<span class="notification-badge">3</span>
					</button>
				</div>
			</header>

			<PixelCard class="level-card">
				<div class="level-info">
					<div class="level-badge">
						<span class="level-number">{homeUser.level}</span>
						<span class="level-label">УР.</span>
					</div>
					<div class="xp-section">
						<div class="xp-bar">
							<div class="xp-fill" style="width: {(homeUser.currentXp / homeUser.xpToNextLevel) * 100}%"></div>
						</div>
						<span class="xp-text">{homeUser.currentXp} / {homeUser.xpToNextLevel} XP</span>
					</div>
				</div>
			</PixelCard>

			<PixelButton size="lg" variant="primary" class="workout-btn">
				<PixelIcon name="dumbbell" size="md" />
				<span>Начать тренировку</span>
			</PixelButton>

			<div class="stats-row">
				<PixelCard class="stat-card">
					<PixelIcon name="calendar" size="sm" color="var(--pixel-blue)" />
					<span class="stat-value">{weeklyStats.workouts}</span>
					<span class="stat-label">тренировок</span>
				</PixelCard>
				<PixelCard class="stat-card">
					<PixelIcon name="bolt" size="sm" color="var(--pixel-yellow)" />
					<span class="stat-value">{weeklyStats.xpEarned}</span>
					<span class="stat-label">XP за неделю</span>
				</PixelCard>
			</div>

			<section class="achievements-section">
				<h3 class="section-title">Недавние достижения</h3>
				<div class="achievements-row">
					{#each recentAchievements as achievement}
						<div class="achievement-item">
							<div class="achievement-icon" style="background: {achievement.color}20; border-color: {achievement.color}">
								<PixelIcon name={achievement.icon} size="sm" color={achievement.color} />
							</div>
							<span class="achievement-name">{achievement.name}</span>
						</div>
					{/each}
				</div>
			</section>
		</div>

	<!-- PROFILE SCREEN -->
	{:else if currentScreen === 'profile'}
		<div class="screen profile-screen">
			<header class="profile-header">
				<div class="avatar-section">
					<PixelAvatar avatarId={profileUser.avatar_id} size="xl" />
					<div class="user-info">
						<h1 class="username">{profileUser.username}</h1>
						<span class="title">{profileUser.title}</span>
					</div>
				</div>

				<div class="level-section">
					<div class="level-badge large">
						<span class="level-number">{profileUser.level}</span>
						<span class="level-label">УРОВЕНЬ</span>
					</div>
					<div class="xp-info">
						<div class="xp-bar">
							<div class="xp-fill" style="width: {(profileUser.currentXp / profileUser.xpToNextLevel) * 100}%"></div>
						</div>
						<span class="xp-text">{profileUser.currentXp} / {profileUser.xpToNextLevel} XP</span>
					</div>
				</div>
			</header>

			<div class="stats-grid">
				<PixelCard class="stat-card">
					<PixelIcon name="bolt" size="sm" color="var(--pixel-yellow)" />
					<span class="stat-value">{profileUser.totalXp.toLocaleString()}</span>
					<span class="stat-label">Всего XP</span>
				</PixelCard>
				<PixelCard class="stat-card">
					<PixelIcon name="coin" size="sm" color="var(--pixel-yellow)" />
					<span class="stat-value">{profileUser.coins.toLocaleString()}</span>
					<span class="stat-label">Монеты</span>
				</PixelCard>
				<PixelCard class="stat-card">
					<PixelIcon name="flame" size="sm" color="var(--pixel-accent)" />
					<span class="stat-value">{profileUser.streak}</span>
					<span class="stat-label">Дней подряд</span>
				</PixelCard>
				<PixelCard class="stat-card">
					<PixelIcon name="dumbbell" size="sm" color="var(--pixel-blue)" />
					<span class="stat-value">{profileUser.workoutsCompleted}</span>
					<span class="stat-label">Тренировок</span>
				</PixelCard>
			</div>

			<section class="badges-section">
				<div class="section-header">
					<h3 class="section-title">Достижения</h3>
					<span class="badge-count">{unlockedBadges.length} / 24</span>
				</div>
				<div class="badges-grid">
					{#each unlockedBadges as badge}
						<div class="badge-item {badge.rarity}">
							<PixelIcon name={badge.icon} size="sm" />
							<span class="badge-name">{badge.name}</span>
						</div>
					{/each}
				</div>
			</section>

			<section class="activity-section">
				<h3 class="section-title">Активность</h3>
				<ActivityCalendar data={activityData} />
			</section>
		</div>

	<!-- LEADERBOARD SCREEN -->
	{:else if currentScreen === 'leaderboard'}
		<div class="screen leaderboard-screen">
			<header class="page-header">
				<h1 class="page-title">Рейтинг</h1>
			</header>

			<PixelTabs tabs={leaderboardTabs} activeTab={leaderboardTab} onTabChange={(tab) => leaderboardTab = tab} />

			<div class="leaderboard">
				<!-- Top 3 Podium -->
				<div class="podium">
					{#if leaderboardEntries.length >= 2}
						<div class="podium-item second">
							<div class="podium-avatar">
								<PixelAvatar avatarId={leaderboardEntries[1].avatar_id} size="lg" />
							</div>
							<div class="podium-rank silver">2</div>
							<span class="podium-name">{leaderboardEntries[1].username}</span>
							<span class="podium-xp">{leaderboardEntries[1].xp.toLocaleString()} XP</span>
						</div>
					{/if}
					{#if leaderboardEntries.length >= 1}
						<div class="podium-item first">
							<div class="podium-crown">
								<PixelIcon name="trophy" size="md" color="var(--pixel-yellow)" />
							</div>
							<div class="podium-avatar">
								<PixelAvatar avatarId={leaderboardEntries[0].avatar_id} size="xl" />
							</div>
							<div class="podium-rank gold">1</div>
							<span class="podium-name">{leaderboardEntries[0].username}</span>
							<span class="podium-xp">{leaderboardEntries[0].xp.toLocaleString()} XP</span>
						</div>
					{/if}
					{#if leaderboardEntries.length >= 3}
						<div class="podium-item third">
							<div class="podium-avatar">
								<PixelAvatar avatarId={leaderboardEntries[2].avatar_id} size="lg" />
							</div>
							<div class="podium-rank bronze">3</div>
							<span class="podium-name">{leaderboardEntries[2].username}</span>
							<span class="podium-xp">{leaderboardEntries[2].xp.toLocaleString()} XP</span>
						</div>
					{/if}
				</div>

				<!-- Rest of the list -->
				<div class="entries-list">
					{#each leaderboardEntries.slice(3) as entry}
						<div class="entry-item" class:current-user={entry.isCurrentUser}>
							<span class="entry-rank">{entry.rank}</span>
							<div class="entry-avatar">
								<PixelAvatar avatarId={entry.avatar_id} size="sm" />
							</div>
							<div class="entry-info">
								<span class="entry-name">{entry.username}</span>
								<span class="entry-level">Ур.{entry.level}</span>
							</div>
							<span class="entry-xp">{entry.xp.toLocaleString()} XP</span>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.demo-page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	/* Screen Switcher */
	.screen-switcher {
		display: flex;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-lg);
		background: var(--pixel-card);
		padding: var(--spacing-xs);
		border: 2px solid var(--border-color);
	}

	.screen-btn {
		flex: 1;
		padding: var(--spacing-sm) var(--spacing-md);
		background: transparent;
		border: 2px solid transparent;
		color: var(--text-secondary);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		cursor: pointer;
		transition: all 0.2s;
	}

	.screen-btn.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: white;
	}

	.screen {
		animation: fadeIn 0.3s ease;
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(10px); }
		to { opacity: 1; transform: translateY(0); }
	}

	/* ===== HOME STYLES ===== */
	.home-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-lg);
	}

	.user-greeting {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.greeting-text {
		display: flex;
		flex-direction: column;
	}

	.greeting {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.home-header .username {
		font-size: var(--font-size-md);
		color: var(--text-primary);
	}

	.notification-btn {
		position: relative;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-sm);
		cursor: pointer;
	}

	.notification-badge {
		position: absolute;
		top: -4px;
		right: -4px;
		background: var(--pixel-accent);
		color: white;
		font-size: 10px;
		width: 16px;
		height: 16px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	:global(.level-card) {
		margin-bottom: var(--spacing-md);
	}

	.level-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.level-badge {
		display: flex;
		flex-direction: column;
		align-items: center;
		background: linear-gradient(135deg, var(--pixel-accent), #ff0066);
		padding: var(--spacing-sm) var(--spacing-md);
		min-width: 60px;
	}

	.level-number {
		font-size: var(--font-size-lg);
		font-weight: bold;
		color: white;
	}

	.level-label {
		font-size: 10px;
		color: rgba(255,255,255,0.8);
	}

	.xp-section {
		flex: 1;
	}

	.xp-bar {
		height: 12px;
		background: var(--border-color);
		border: 2px solid var(--border-color);
		margin-bottom: 4px;
	}

	.xp-fill {
		height: 100%;
		background: linear-gradient(90deg, var(--pixel-blue), var(--pixel-accent));
		transition: width 0.3s;
	}

	.xp-text {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	:global(.workout-btn) {
		width: 100%;
		margin-bottom: var(--spacing-lg);
	}

	.stats-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-lg);
	}

	:global(.stat-card) {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-md) !important;
	}

	.stat-value {
		font-size: var(--font-size-lg);
		color: var(--text-primary);
	}

	.stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-align: center;
	}

	.section-title {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin-bottom: var(--spacing-sm);
		color: var(--text-primary);
	}

	.achievements-row {
		display: flex;
		gap: var(--spacing-sm);
	}

	.achievement-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.achievement-icon {
		width: 48px;
		height: 48px;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 2px solid;
	}

	.achievement-name {
		font-size: 10px;
		color: var(--text-secondary);
		text-align: center;
	}

	/* ===== PROFILE STYLES ===== */
	.profile-header {
		margin-bottom: var(--spacing-lg);
	}

	.avatar-section {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		margin-bottom: var(--spacing-md);
	}

	.user-info {
		display: flex;
		flex-direction: column;
	}

	.profile-screen .username {
		font-size: var(--font-size-lg);
		margin: 0;
	}

	.title {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
	}

	.level-section {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.level-badge.large {
		min-width: 80px;
		padding: var(--spacing-md);
	}

	.level-badge.large .level-number {
		font-size: var(--font-size-xl);
	}

	.xp-info {
		flex: 1;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-lg);
	}

	.badges-section,
	.activity-section {
		margin-bottom: var(--spacing-lg);
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-sm);
	}

	.badge-count {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.badges-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--spacing-sm);
	}

	.badge-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
	}

	.badge-item.common { border-color: #888; }
	.badge-item.rare { border-color: #4a9eff; }
	.badge-item.epic { border-color: #a855f7; }
	.badge-item.legendary { border-color: #ffd700; }

	.badge-name {
		font-size: 9px;
		color: var(--text-secondary);
		text-align: center;
		line-height: 1.2;
	}

	/* ===== LEADERBOARD STYLES ===== */
	.page-header {
		margin-bottom: var(--spacing-md);
	}

	.page-title {
		font-size: var(--font-size-lg);
		text-transform: uppercase;
		margin: 0;
	}

	.leaderboard {
		margin-top: var(--spacing-md);
	}

	.podium {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-lg);
		padding: var(--spacing-md) 0;
	}

	.podium-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
		position: relative;
	}

	.podium-item.first { order: 2; }
	.podium-item.second { order: 1; }
	.podium-item.third { order: 3; }

	.podium-crown {
		position: absolute;
		top: -24px;
		animation: bounce 1s ease-in-out infinite;
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-4px); }
	}

	.podium-rank {
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: var(--font-size-sm);
		font-weight: bold;
		margin-top: -8px;
	}

	.podium-rank.gold {
		background: linear-gradient(135deg, #ffd700, #ffaa00);
		color: #000;
	}

	.podium-rank.silver {
		background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
		color: #000;
	}

	.podium-rank.bronze {
		background: linear-gradient(135deg, #cd7f32, #a0522d);
		color: #fff;
	}

	.podium-name {
		font-size: var(--font-size-xs);
		color: var(--text-primary);
		max-width: 80px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		text-align: center;
	}

	.podium-xp {
		font-size: 10px;
		color: var(--pixel-blue);
	}

	.entries-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.entry-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.entry-item.current-user {
		border-color: var(--pixel-accent);
		background: rgba(255, 0, 100, 0.1);
	}

	.entry-rank {
		width: 24px;
		text-align: center;
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
	}

	.entry-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}

	.entry-name {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.entry-level {
		font-size: 10px;
		color: var(--text-secondary);
	}

	.entry-xp {
		font-size: var(--font-size-xs);
		color: var(--pixel-blue);
		white-space: nowrap;
	}
</style>
