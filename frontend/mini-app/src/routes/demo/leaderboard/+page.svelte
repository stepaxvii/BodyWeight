<script lang="ts">
	import { PixelCard, PixelIcon, PixelTabs, PixelAvatar } from '$lib/components/ui';

	type TabType = 'global' | 'weekly' | 'friends';
	let activeTab = $state<TabType>('global');

	// Demo leaderboard data
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
			{ rank: 5, username: 'PowerAthlete', avatar_id: 'golden-eagle', xp: 1320, level: 48 },
			{ rank: 6, username: 'MuscleHero', avatar_id: 'ocean-whale', xp: 1180, level: 45 },
			{ rank: 7, username: 'StrengthKing', avatar_id: 'frost-bear', xp: 1050, level: 54 },
			{ rank: 8, username: 'FitnessNinja', avatar_id: 'jungle-monkey', xp: 920, level: 42 },
			{ rank: 9, username: 'WorkoutPro', avatar_id: 'desert-fox', xp: 780, level: 39 },
			{ rank: 10, username: 'BodyBuilder', avatar_id: 'night-owl', xp: 650, level: 36 }
		],
		friends: [
			{ rank: 1, username: 'PixelWarrior', avatar_id: 'cyber-dragon', xp: 38920, level: 58, isCurrentUser: true },
			{ rank: 2, username: 'AlexFit', avatar_id: 'flame-phoenix', xp: 28500, level: 44 },
			{ rank: 3, username: 'MaxPower', avatar_id: 'shadow-wolf', xp: 21300, level: 35 },
			{ rank: 4, username: 'AnnaStrong', avatar_id: 'frost-bear', xp: 15800, level: 27 },
			{ rank: 5, username: 'DimaSport', avatar_id: 'thunder-tiger', xp: 12400, level: 22 }
		]
	};

	const tabs = [
		{ id: 'global' as const, label: 'Глобальный' },
		{ id: 'weekly' as const, label: 'Неделя' },
		{ id: 'friends' as const, label: 'Друзья' }
	];

	function switchTab(tab: TabType) {
		activeTab = tab;
	}

	function getRankClass(rank: number): string {
		if (rank === 1) return 'gold';
		if (rank === 2) return 'silver';
		if (rank === 3) return 'bronze';
		return '';
	}

	const entries = $derived(leaderboardData[activeTab]);
</script>

<div class="page container">
	<header class="page-header">
		<h1 class="page-title">Рейтинг</h1>
	</header>

	<PixelTabs {tabs} {activeTab} onTabChange={switchTab} />

	<div class="leaderboard">
		<!-- Top 3 Podium -->
		<div class="podium">
			{#if entries.length >= 2}
				<div class="podium-item second">
					<div class="podium-avatar">
						<PixelAvatar avatarId={entries[1].avatar_id} size="lg" />
					</div>
					<div class="podium-rank silver">2</div>
					<span class="podium-name">{entries[1].username}</span>
					<span class="podium-xp">{entries[1].xp.toLocaleString()} XP</span>
				</div>
			{/if}
			{#if entries.length >= 1}
				<div class="podium-item first">
					<div class="podium-crown">
						<PixelIcon name="trophy" size="md" color="var(--pixel-yellow)" />
					</div>
					<div class="podium-avatar">
						<PixelAvatar avatarId={entries[0].avatar_id} size="xl" />
					</div>
					<div class="podium-rank gold">1</div>
					<span class="podium-name">{entries[0].username}</span>
					<span class="podium-xp">{entries[0].xp.toLocaleString()} XP</span>
				</div>
			{/if}
			{#if entries.length >= 3}
				<div class="podium-item third">
					<div class="podium-avatar">
						<PixelAvatar avatarId={entries[2].avatar_id} size="lg" />
					</div>
					<div class="podium-rank bronze">3</div>
					<span class="podium-name">{entries[2].username}</span>
					<span class="podium-xp">{entries[2].xp.toLocaleString()} XP</span>
				</div>
			{/if}
		</div>

		<!-- Rest of the list -->
		<div class="entries-list">
			{#each entries.slice(3) as entry}
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

		<!-- Current user highlight if not in top 10 -->
		<div class="current-user-card">
			<div class="entry-item current-user highlighted">
				<span class="entry-rank">3</span>
				<div class="entry-avatar">
					<PixelAvatar avatarId="cyber-dragon" size="sm" />
				</div>
				<div class="entry-info">
					<span class="entry-name">PixelWarrior</span>
					<span class="entry-level">Ур.58</span>
				</div>
				<span class="entry-xp">38,920 XP</span>
			</div>
			<span class="your-position">Твоя позиция</span>
		</div>
	</div>
</div>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

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

	/* Podium */
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

	.podium-item.first {
		order: 2;
	}

	.podium-item.second {
		order: 1;
	}

	.podium-item.third {
		order: 3;
	}

	.podium-crown {
		position: absolute;
		top: -24px;
		animation: bounce 1s ease-in-out infinite;
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-4px); }
	}

	.podium-avatar {
		position: relative;
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

	/* Entries list */
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

	.entry-avatar {
		flex-shrink: 0;
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

	/* Current user card */
	.current-user-card {
		margin-top: var(--spacing-lg);
		position: relative;
	}

	.current-user-card .entry-item.highlighted {
		border-width: 3px;
	}

	.your-position {
		position: absolute;
		top: -10px;
		left: 50%;
		transform: translateX(-50%);
		background: var(--pixel-accent);
		padding: 2px 8px;
		font-size: 10px;
		text-transform: uppercase;
	}
</style>
