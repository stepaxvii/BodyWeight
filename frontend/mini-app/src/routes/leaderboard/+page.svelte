<script lang="ts">
	import { onMount } from 'svelte';
	import { PixelCard, PixelIcon, PixelAvatar, EmptyState, PixelTabs, PixelButton } from '$lib/components/ui';
	import UserProfileModal from '$lib/components/UserProfileModal.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import type { LeaderboardEntry, LeaderboardType } from '$lib/types';

	let entries = $state<LeaderboardEntry[]>([]);
	let activeTab = $state<LeaderboardType>('global');
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let selectedUserId = $state<number | null>(null);
	let updatingVisibility = $state(false);

	const leaderboardConsentText = `Показывать твой username (или имя) в общем рейтинге и у друзей?`;

	async function showMeInLeaderboard() {
		if (updatingVisibility || userStore.user?.leaderboard_visible) return;
		updatingVisibility = true;
		try {
				const updated = await api.updateUser({ leaderboard_visible: true });
			if (userStore.user) userStore.user = { ...userStore.user, ...updated };
			telegram.hapticImpact('light');
			await loadLeaderboard();
		} catch (e) {
			console.error('Failed to set leaderboard visible:', e);
		} finally {
			updatingVisibility = false;
		}
	}

	const leaderboardTabs: { id: LeaderboardType; label: string }[] = [
		{ id: 'global', label: 'Все' },
		{ id: 'weekly', label: 'Неделя' },
		{ id: 'friends', label: 'Друзья' }
	];

	onMount(async () => {
		// Рейтинг грузим сразу; пользователя подтягиваем в фоне для карточки «Показывать в рейтинге»
		loadLeaderboard();
		try {
			const u = await api.getCurrentUser();
			if (userStore.user) userStore.user = { ...userStore.user, ...u };
			else userStore.user = u;
		} catch {
			// оставляем данные из auth
		}
	});

	async function loadLeaderboard() {
		isLoading = true;
		error = null;
		try {
			entries = await api.getLeaderboard(activeTab);
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

	function openUserProfile(entry: LeaderboardEntry) {
		if (entry.is_current_user) return; // Don't open own profile
		selectedUserId = entry.user_id;
		telegram.hapticImpact('light');
	}
</script>

<div class="page container">
	<header class="page-header">
		<h1>Рейтинг</h1>
	</header>

	<!-- Tabs -->
	<PixelTabs tabs={leaderboardTabs} activeTab={activeTab} onTabChange={switchTab} />

	<!-- Показать меня в рейтинге (если скрыт или ещё не выбрано) -->
	{#if userStore.user && userStore.user.leaderboard_visible !== true}
		<PixelCard class="leaderboard-consent-card">
			<p class="consent-message">📊 <strong>Рейтинг</strong></p>
			<p class="consent-message">{leaderboardConsentText}</p>
			<p class="consent-hint">Можно изменить позже в настройках приложения.</p>
			<PixelButton
				variant="primary"
				fullWidth
				disabled={updatingVisibility}
				loading={updatingVisibility}
				onclick={showMeInLeaderboard}
			>
				Показывать меня в рейтинге
			</PixelButton>
		</PixelCard>
	{/if}

	<!-- Leaderboard Content -->
	{#if isLoading}
		<div class="loading">
			<div class="pixel-spinner"></div>
			<span>Загрузка...</span>
		</div>
	{:else if error}
		<EmptyState
			icon="trophy"
			message={error}
		/>
	{:else if entries.length === 0}
		<EmptyState
			icon="trophy"
			message="Пока никого нет"
		/>
	{:else}
		<!-- Top 3 Podium -->
		{#if activeTab !== 'friends' && entries.length >= 3}
			<div class="podium">
				<!-- 2nd Place -->
				<button
					class="podium-item second"
					class:clickable={!entries[1].is_current_user}
					onclick={() => openUserProfile(entries[1])}
				>
					<PixelAvatar
						avatarId={entries[1].avatar_id || 'shadow-wolf'}
						size="lg"
						borderColor="var(--pixel-light)"
					/>
					<span class="podium-name">{entries[1].username ? `${entries[1].username}` : entries[1].first_name}</span>
					<span class="podium-xp">{entries[1].total_xp} XP</span>
					<div class="podium-rank">2</div>
				</button>

				<!-- 1st Place -->
				<button
					class="podium-item first"
					class:clickable={!entries[0].is_current_user}
					onclick={() => openUserProfile(entries[0])}
				>
					<div class="podium-crown">
						<PixelIcon name="trophy" color="var(--pixel-yellow)" />
					</div>
					<PixelAvatar
						avatarId={entries[0].avatar_id || 'shadow-wolf'}
						size="xl"
						borderColor="var(--pixel-yellow)"
					/>
					<span class="podium-name">{entries[0].username ? `${entries[0].username}` : entries[0].first_name}</span>
					<span class="podium-xp">{entries[0].total_xp} XP</span>
					<div class="podium-rank">1</div>
				</button>

				<!-- 3rd Place -->
				<button
					class="podium-item third"
					class:clickable={!entries[2].is_current_user}
					onclick={() => openUserProfile(entries[2])}
				>
					<PixelAvatar
						avatarId={entries[2].avatar_id || 'shadow-wolf'}
						size="lg"
						borderColor="var(--pixel-orange)"
					/>
					<span class="podium-name">{entries[2].username ? `${entries[2].username}` : entries[2].first_name}</span>
					<span class="podium-xp">{entries[2].total_xp} XP</span>
					<div class="podium-rank">3</div>
				</button>
			</div>
		{/if}

		<!-- Full List -->
		<div class="leaderboard-list">
			{#each entries as entry, i}
				{@const hasPodium = activeTab !== 'friends' && entries.length >= 3}
				{@const showInList = activeTab === 'friends' || !hasPodium || i >= 3}
				{#if showInList}
					<button
						class="entry-card"
						class:accent={entry.is_current_user}
						class:clickable={!entry.is_current_user}
						onclick={() => openUserProfile(entry)}
					>
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
									{entry.username ? `${entry.username}` : entry.first_name}
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
					</button>
				{/if}
			{/each}
		</div>
	{/if}
</div>

<!-- User Profile Modal -->
<UserProfileModal
	userId={selectedUserId}
	onclose={() => selectedUserId = null}
/>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	.page-header {
		text-align: center;
		margin-bottom: var(--spacing-md);
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
		cursor: pointer;
		font-family: var(--font-pixel);
		color: var(--text-primary);
		transition: transform var(--transition-fast);
	}

	.podium-item.clickable:hover {
		transform: scale(1.05);
	}

	.podium-item.first {
		padding: var(--spacing-md);
		border-color: var(--pixel-yellow);
		margin-bottom: var(--spacing-md);
	}

	.podium-item.second {
		border-color: var(--pixel-light);
		padding-bottom: var(--spacing-md);
	}

	.podium-item.third {
		border-color: var(--pixel-orange);
		padding-bottom: var(--spacing-md);
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
		margin-bottom: 4px;
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

	.entry-card {
		width: 100%;
		padding: var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		font-family: var(--font-pixel);
		color: var(--text-primary);
		cursor: pointer;
		text-align: left;
		transition: border-color var(--transition-fast);
	}

	.entry-card.clickable:hover {
		border-color: var(--pixel-accent);
	}

	.entry-card.accent {
		border-color: var(--pixel-accent);
		background: rgba(233, 69, 96, 0.1);
	}

	.entry {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.entry.current-user {
		background: transparent;
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

	.leaderboard-consent-card {
		margin-bottom: var(--spacing-md);
	}
	.consent-message {
		margin: 0 0 var(--spacing-xs);
		font-size: var(--font-size-sm);
	}
	.consent-hint {
		margin: 0 0 var(--spacing-sm);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}
</style>
