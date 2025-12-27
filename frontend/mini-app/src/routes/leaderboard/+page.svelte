<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type LeaderboardEntry } from '$lib/api/client';

	let entries: LeaderboardEntry[] = $state([]);
	let myRank: { rank: number | null; total_users: number } | null = $state(null);
	let isLoading = $state(true);
	let leaderboardType: 'global' | 'friends' = $state('global');

	onMount(async () => {
		await loadLeaderboard();
	});

	async function loadLeaderboard() {
		isLoading = true;
		try {
			[entries, myRank] = await Promise.all([
				api.getLeaderboard(leaderboardType),
				api.getMyRank(),
			]);
		} catch (error) {
			console.error('Failed to load leaderboard:', error);
		} finally {
			isLoading = false;
		}
	}

	function switchType(type: 'global' | 'friends') {
		leaderboardType = type;
		loadLeaderboard();
	}

	function getRankIcon(rank: number): string {
		if (rank === 1) return '🥇';
		if (rank === 2) return '🥈';
		if (rank === 3) return '🥉';
		return `#${rank}`;
	}
</script>

<div class="container">
	<header class="page-header">
		<h1 class="pixel-title">📊 РЕЙТИНГ</h1>
	</header>

	<!-- Type Switcher -->
	<div class="type-switcher">
		<button
			class="type-btn"
			class:active={leaderboardType === 'global'}
			onclick={() => switchType('global')}
		>
			🌍 ГЛОБАЛЬНЫЙ
		</button>
		<button
			class="type-btn"
			class:active={leaderboardType === 'friends'}
			onclick={() => switchType('friends')}
		>
			👥 ДРУЗЬЯ
		</button>
	</div>

	<!-- My Rank -->
	{#if myRank && myRank.rank}
		<div class="my-rank pixel-card">
			<div class="my-rank-label">ТВОЁ МЕСТО:</div>
			<div class="my-rank-value">{myRank.rank}</div>
			<div class="my-rank-total">из {myRank.total_users}</div>
		</div>
	{/if}

	{#if isLoading}
		<div class="loading">
			<div class="loading-icon">📊</div>
			<div class="loading-text">Загрузка рейтинга...</div>
		</div>
	{:else if entries.length === 0}
		<div class="empty-state">
			<div class="empty-icon">🏆</div>
			<div class="empty-text">
				{#if leaderboardType === 'friends'}
					Добавь друзей, чтобы соревноваться!
				{:else}
					Рейтинг пока пуст
				{/if}
			</div>
		</div>
	{:else}
		<div class="leaderboard-list">
			{#each entries as entry, index}
				<div
					class="leaderboard-item"
					class:top-3={entry.rank <= 3}
					class:current-user={entry.is_current_user}
				>
					<div class="rank-col">
						{#if entry.rank <= 3}
							<span class="rank-icon">{getRankIcon(entry.rank)}</span>
						{:else}
							<span class="rank-number">#{entry.rank}</span>
						{/if}
					</div>

					<div class="user-col">
						<div class="user-name">
							{entry.first_name || entry.username || 'Воин'}
							{#if entry.is_current_user}
								<span class="you-badge">ТЫ</span>
							{/if}
						</div>
						<div class="user-stats">
							<span class="level-badge-sm">LVL {entry.level}</span>
							<span class="streak-badge">🔥 {entry.streak_days}</span>
						</div>
					</div>

					<div class="xp-col">
						<div class="xp-value">{entry.experience}</div>
						<div class="xp-label">XP</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.page-header {
		text-align: center;
		margin-bottom: var(--space-md);
	}

	.type-switcher {
		display: flex;
		gap: var(--space-sm);
		margin-bottom: var(--space-md);
	}

	.type-btn {
		flex: 1;
		padding: var(--space-md);
		background: var(--bg-card);
		border: 4px solid var(--border);
		color: var(--text-secondary);
		font-family: 'Press Start 2P', monospace;
		font-size: 8px;
		cursor: pointer;
		transition: all 0.1s;
	}

	.type-btn.active {
		border-color: var(--accent);
		color: var(--accent);
		background: var(--bg-medium);
	}

	.my-rank {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--space-md);
		text-align: center;
		background: linear-gradient(135deg, var(--bg-light) 0%, var(--bg-medium) 100%);
		margin-bottom: var(--space-lg);
	}

	.my-rank-label {
		font-size: 9px;
		color: var(--text-muted);
	}

	.my-rank-value {
		font-size: 24px;
		color: var(--accent);
	}

	.my-rank-total {
		font-size: 9px;
		color: var(--text-muted);
	}

	.loading, .empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 40vh;
		text-align: center;
	}

	.loading-icon, .empty-icon {
		font-size: 48px;
		margin-bottom: var(--space-md);
	}

	.loading-icon {
		animation: bounce 1s infinite;
	}

	.loading-text, .empty-text {
		font-size: 10px;
		color: var(--text-muted);
	}

	.leaderboard-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
	}

	.leaderboard-item {
		display: flex;
		align-items: center;
		gap: var(--space-md);
		padding: var(--space-md);
		background: var(--bg-card);
		border: 4px solid var(--border);
	}

	.leaderboard-item.top-3 {
		border-color: var(--accent);
		background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-light) 100%);
	}

	.leaderboard-item.current-user {
		border-color: var(--secondary);
	}

	.rank-col {
		width: 40px;
		text-align: center;
	}

	.rank-icon {
		font-size: 24px;
	}

	.rank-number {
		font-size: 12px;
		color: var(--text-muted);
	}

	.user-col {
		flex: 1;
	}

	.user-name {
		font-size: 10px;
		color: var(--text-primary);
		display: flex;
		align-items: center;
		gap: var(--space-sm);
	}

	.you-badge {
		font-size: 7px;
		background: var(--secondary);
		color: var(--bg-dark);
		padding: 2px 4px;
	}

	.user-stats {
		display: flex;
		gap: var(--space-sm);
		margin-top: var(--space-xs);
	}

	.level-badge-sm {
		font-size: 7px;
		background: var(--accent);
		color: var(--bg-dark);
		padding: 2px 4px;
	}

	.streak-badge {
		font-size: 7px;
		color: var(--warning);
	}

	.xp-col {
		text-align: right;
	}

	.xp-value {
		font-size: 12px;
		color: var(--accent);
	}

	.xp-label {
		font-size: 7px;
		color: var(--text-muted);
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}
</style>
