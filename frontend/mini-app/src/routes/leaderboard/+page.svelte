<script lang="ts">
	import { onMount } from 'svelte';
	import { PixelCard, PixelIcon, PixelAvatar } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { LeaderboardEntry, LeaderboardType } from '$lib/types';

	let entries = $state<LeaderboardEntry[]>([]);
	let activeTab = $state<LeaderboardType>('global');
	let isLoading = $state(true);
	let error = $state<string | null>(null);

	const tabs: { id: LeaderboardType; label: string }[] = [
		{ id: 'global', label: 'Все' },
		{ id: 'weekly', label: 'Неделя' },
		{ id: 'friends', label: 'Друзья' }
	];

	onMount(async () => {
		await loadLeaderboard();
	});

	async function loadLeaderboard() {
		isLoading = true;
		error = null;
		try {
			entries = await api.getLeaderboard(activeTab);
			console.log(`[Leaderboard] Loaded ${entries.length} entries for tab '${activeTab}'`);
		} catch (err) {
			console.error('Failed to load leaderboard:', err);
			error = err instanceof Error ? err.message : 'Ошибка загрузки рейтинга';
			entries = [];
		} finally {
			isLoading = false;
		}
	}

	async function switchTab(tab: LeaderboardType) {
		if (tab === activeTab) return;
		activeTab = tab;
		telegram.hapticImpact('light');
		await loadLeaderboard();
	}

	function getRankColor(rank: number): string {
		switch (rank) {
			case 1: return 'var(--pixel-yellow)';
			case 2: return 'var(--pixel-light)';
			case 3: return 'var(--pixel-orange)';
			default: return 'var(--text-secondary)';
		}
	}

	function getRankIcon(rank: number): string {
		if (rank <= 3) return 'trophy';
		return '';
	}
</script>

<div class="page container">
	<header class="page-header">
		<h1>Рейтинг</h1>
	</header>

	<!-- Tabs -->
	<div class="tabs">
		{#each tabs as tab}
			<button
				class="tab"
				class:active={activeTab === tab.id}
				onclick={() => switchTab(tab.id)}
			>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- Leaderboard Content -->
	{#if isLoading}
		<div class="loading">
			<div class="pixel-spinner"></div>
			<span>Загрузка...</span>
		</div>
	{:else if error}
		<div class="empty-state">
			<PixelIcon name="trophy" size="xl" color="var(--pixel-red)" />
			<p>{error}</p>
		</div>
	{:else if entries.length === 0}
		<div class="empty-state">
			<PixelIcon name="trophy" size="xl" color="var(--text-muted)" />
			<p>Пока никого нет</p>
		</div>
	{:else}
		<!-- Top 3 Podium -->
		{#if activeTab !== 'friends' && entries.length >= 3}
			<div class="podium">
				<!-- 2nd Place -->
				<div class="podium-item second">
					<PixelAvatar
						avatarId={entries[1].avatar_id || 'shadow-wolf'}
						size="lg"
						borderColor="var(--pixel-light)"
					/>
					<span class="podium-name">{entries[1].username ? `@${entries[1].username}` : entries[1].first_name}</span>
					<span class="podium-xp">{entries[1].total_xp} XP</span>
					<div class="podium-rank">2</div>
				</div>

				<!-- 1st Place -->
				<div class="podium-item first">
					<div class="podium-crown">
						<PixelIcon name="trophy" color="var(--pixel-yellow)" />
					</div>
					<PixelAvatar
						avatarId={entries[0].avatar_id || 'shadow-wolf'}
						size="xl"
						borderColor="var(--pixel-yellow)"
					/>
					<span class="podium-name">{entries[0].username ? `@${entries[0].username}` : entries[0].first_name}</span>
					<span class="podium-xp">{entries[0].total_xp} XP</span>
					<div class="podium-rank">1</div>
				</div>

				<!-- 3rd Place -->
				<div class="podium-item third">
					<PixelAvatar
						avatarId={entries[2].avatar_id || 'shadow-wolf'}
						size="lg"
						borderColor="var(--pixel-orange)"
					/>
					<span class="podium-name">{entries[2].username ? `@${entries[2].username}` : entries[2].first_name}</span>
					<span class="podium-xp">{entries[2].total_xp} XP</span>
					<div class="podium-rank">3</div>
				</div>
			</div>
		{/if}

		<!-- Full List -->
		<div class="leaderboard-list">
			{#each entries as entry, i}
				{@const hasPodium = activeTab !== 'friends' && entries.length >= 3}
				{@const showInList = activeTab === 'friends' || !hasPodium || i >= 3}
				{#if showInList}
					<PixelCard variant={entry.is_current_user ? 'accent' : 'default'} padding="sm">
						<div class="entry" class:current-user={entry.is_current_user}>
							<div class="entry-rank" style="color: {getRankColor(entry.rank)}">
								{#if getRankIcon(entry.rank)}
									<PixelIcon name={getRankIcon(entry.rank)} size="sm" color={getRankColor(entry.rank)} />
								{/if}
								<span>#{entry.rank}</span>
							</div>

							<PixelAvatar
								avatarId={entry.avatar_id || 'shadow-wolf'}
								size="sm"
								showBorder={false}
							/>

							<div class="entry-info">
								<span class="entry-name">
									{entry.username ? `@${entry.username}` : entry.first_name}
									{#if entry.is_current_user}
										<span class="you-badge">ВЫ</span>
									{/if}
								</span>
								<span class="entry-level">Ур.{entry.level}</span>
							</div>

							<div class="entry-stats">
								<span class="entry-xp">{entry.total_xp}</span>
								<span class="entry-xp-label">XP</span>
							</div>

							<div class="entry-streak">
								<PixelIcon name="streak" size="sm" color="var(--pixel-yellow)" />
								<span>{entry.current_streak}</span>
							</div>
						</div>
					</PixelCard>
				{/if}
			{/each}
		</div>
	{/if}
</div>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	.page-header {
		text-align: center;
		margin-bottom: var(--spacing-md);
	}

	/* Tabs */
	.tabs {
		display: flex;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-lg);
	}

	.tab {
		flex: 1;
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.tab:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent-hover);
		color: var(--text-primary);
	}

	/* Loading */
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-secondary);
		font-size: var(--font-size-sm);
		text-transform: uppercase;
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-muted);
		font-size: var(--font-size-sm);
	}

	/* Podium */
	.podium {
		display: flex;
		justify-content: center;
		align-items: flex-end;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-lg);
		padding: var(--spacing-md);
	}

	.podium-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		position: relative;
	}

	.podium-item.first {
		padding: var(--spacing-md);
		border-color: var(--pixel-yellow);
		margin-bottom: var(--spacing-md);
	}

	.podium-item.second {
		border-color: var(--pixel-light);
	}

	.podium-item.third {
		border-color: var(--pixel-orange);
	}

	.podium-crown {
		position: absolute;
		top: -20px;
		animation: pixel-bounce 1s ease-in-out infinite;
	}

	.podium-name {
		font-size: var(--font-size-xs);
		max-width: 60px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.podium-xp {
		font-size: var(--font-size-xs);
		color: var(--pixel-green);
	}

	.podium-rank {
		position: absolute;
		bottom: -12px;
		width: 24px;
		height: 24px;
		background: var(--pixel-bg-dark);
		border: 2px solid currentColor;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: var(--font-size-xs);
	}

	.podium-item.first .podium-rank { color: var(--pixel-yellow); }
	.podium-item.second .podium-rank { color: var(--pixel-light); }
	.podium-item.third .podium-rank { color: var(--pixel-orange); }

	/* Leaderboard List */
	.leaderboard-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.entry {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.entry.current-user {
		background: rgba(233, 69, 96, 0.1);
	}

	.entry-rank {
		display: flex;
		align-items: center;
		gap: 2px;
		min-width: 40px;
		font-size: var(--font-size-xs);
	}

	.entry-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}

	.entry-name {
		font-size: var(--font-size-xs);
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.you-badge {
		font-size: 6px;
		padding: 1px 4px;
		background: var(--pixel-accent);
		color: var(--text-primary);
	}

	.entry-level {
		font-size: 8px;
		color: var(--text-secondary);
	}

	.entry-stats {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}

	.entry-xp {
		font-size: var(--font-size-sm);
		color: var(--pixel-green);
	}

	.entry-xp-label {
		font-size: 6px;
		color: var(--text-muted);
	}

	.entry-streak {
		display: flex;
		align-items: center;
		gap: 2px;
		font-size: var(--font-size-xs);
		color: var(--pixel-yellow);
		min-width: 32px;
	}

	@keyframes pixel-bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-4px); }
	}
</style>
