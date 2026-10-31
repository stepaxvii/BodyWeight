<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { PixelIcon, PixelAvatar, EmptyState, PixelButton, CountUp } from '$lib/components/ui';
	import UserProfileModal from '$lib/components/UserProfileModal.svelte';
	import Banner from '$lib/components/ui/Banner.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import type { LeaderboardEntry } from '$lib/types';

	let entries = $state<LeaderboardEntry[]>([]);
	let isLoading = $state(true);
	let error = $state<string | null>(null);
	let selectedUserId = $state<number | null>(null);
	let updatingVisibility = $state(false);

	// Есть ли вообще соперники (кроме самого пользователя)
	const hasRivals = $derived(entries.some((e) => !e.is_current_user));
	const showPodium = $derived(entries.length >= 3);

	async function showMeInLeaderboard() {
		if (updatingVisibility || userStore.user?.leaderboard_visible) return;
		updatingVisibility = true;
		try {
			await userStore.setLeaderboardVisible(true);
			telegram.hapticImpact('light');
			await loadLeaderboard();
		} catch (e) {
			console.error('Failed to set leaderboard visible:', e);
		} finally {
			updatingVisibility = false;
		}
	}

	onMount(async () => {
		// Рейтинг и пользователь параллельно
		const [, u] = await Promise.all([
			loadLeaderboard(),
			api.getCurrentUser().catch(() => null),
		]);
		if (u) {
			userStore.user = userStore.user ? { ...userStore.user, ...u } : u;
		}
	});

	async function loadLeaderboard() {
		isLoading = true;
		error = null;
		try {
			const list = await api.getLeaderboard();
			entries = Array.isArray(list) ? list : [];
		} catch (err) {
			console.error('Failed to load leaderboard:', err);
			error = err instanceof Error ? err.message : 'Ошибка загрузки рейтинга';
			entries = [];
		} finally {
			isLoading = false;
		}
	}

	function getRankColor(rank: number): string {
		switch (rank) {
			case 1: return 'var(--gold)';
			case 2: return 'var(--dim)';
			case 3: return 'var(--podium3)';
			default: return 'var(--muted)';
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

	function goInviteFriend() {
		telegram.hapticImpact('light');
		goto(`${base}/friends`);
	}
</script>

<div class="page container">
	<div class="banner-wrap">
		<Banner icon="trophy" title="Рейтинг" sub="Неделя среди друзей" deco="crown" />
	</div>

	<p class="lb-note">
		<PixelIcon name="clock" size="sm" color="var(--muted)" />
		<span>Очки сбрасываются каждый понедельник</span>
	</p>

	<!-- Скрыт из рейтинга — панель с предложением показать себя друзьям -->
	{#if userStore.isAuthenticated && (userStore.user == null || userStore.user.leaderboard_visible !== true)}
		<div class="lb-hidden">
			<div class="lb-hidden__head">
				<span class="slot slot--md"><PixelIcon name="lock" size="md" color="var(--muted)" /></span>
				<div class="lb-hidden__txt">
					<span class="lb-hidden__t">Ты скрыт из рейтинга</span>
					<span class="lb-hidden__s">Друзья не видят тебя в недельном рейтинге.</span>
				</div>
			</div>
			<PixelButton
				variant="primary"
				fullWidth
				disabled={updatingVisibility}
				loading={updatingVisibility}
				onclick={showMeInLeaderboard}
			>
				Показывать меня друзьям
			</PixelButton>
		</div>
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
	{:else if !hasRivals}
		<!-- Пусто: кроме тебя соревноваться некому -->
		<div class="lb-empty anim-pop">
			<span class="slot slot--lg"><PixelIcon name="friends" size="lg" color="var(--muted)" /></span>
			<p class="lb-empty__t">Пока соревноваться не с кем</p>
			<p class="lb-empty__s">Добавь друзей — и недельная гонка за XP начнётся.</p>
			<PixelButton variant="primary" fullWidth onclick={goInviteFriend}>
				Пригласить друга
			</PixelButton>
		</div>
	{:else}
		<!-- Top 3 Podium (недельные XP) -->
		{#if showPodium}
			<div class="podium">
				<!-- 2nd Place -->
				<button
					class="podium-item second anim-pop"
					class:clickable={!entries[1].is_current_user}
					onclick={() => openUserProfile(entries[1])}
				>
					<PixelAvatar
						avatarId={entries[1].avatar_id || 'shadow-wolf'}
						size="lg"
						borderColor="var(--line)"
					/>
					<span class="podium-name">{entries[1].username ? `${entries[1].username}` : entries[1].first_name}</span>
					<span class="podium-xp"><CountUp value={entries[1].total_xp} /> XP</span>
					<div class="podium-rank">2</div>
				</button>

				<!-- 1st Place -->
				<button
					class="podium-item first anim-pop"
					class:clickable={!entries[0].is_current_user}
					onclick={() => openUserProfile(entries[0])}
				>
					<div class="podium-crown">
						<PixelIcon name="crown" color="var(--ink)" />
					</div>
					<PixelAvatar
						avatarId={entries[0].avatar_id || 'shadow-wolf'}
						size="xl"
						borderColor="var(--line)"
					/>
					<span class="podium-name">{entries[0].username ? `${entries[0].username}` : entries[0].first_name}</span>
					<span class="podium-xp"><CountUp value={entries[0].total_xp} /> XP</span>
					<div class="podium-rank">1</div>
				</button>

				<!-- 3rd Place -->
				<button
					class="podium-item third anim-pop"
					class:clickable={!entries[2].is_current_user}
					onclick={() => openUserProfile(entries[2])}
				>
					<PixelAvatar
						avatarId={entries[2].avatar_id || 'shadow-wolf'}
						size="lg"
						borderColor="var(--line)"
					/>
					<span class="podium-name">{entries[2].username ? `${entries[2].username}` : entries[2].first_name}</span>
					<span class="podium-xp"><CountUp value={entries[2].total_xp} /> XP</span>
					<div class="podium-rank">3</div>
				</button>
			</div>
		{/if}

		<!-- Остальные места -->
		<div class="leaderboard-list anim-rows">
			{#each entries as entry, i}
				{#if !showPodium || i >= 3}
					<button
						class="entry-card"
						class:accent={entry.is_current_user}
						class:clickable={!entry.is_current_user}
						onclick={() => openUserProfile(entry)}
					>
						<div class="entry" class:current-user={entry.is_current_user}>
							<div class="entry-rank" style="color: {entry.is_current_user ? 'var(--on-accent)' : getRankColor(entry.rank)}">
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
								<span class="entry-level">Ур.{entry.level}{#if entry.equipped_title} · {entry.equipped_title}{/if}</span>
							</div>

							<div class="entry-stats">
								<span class="entry-xp"><CountUp value={entry.total_xp} /></span>
								<span class="entry-xp-label">XP</span>
							</div>

							<div class="entry-streak">
								<PixelIcon name="streak" size="sm" color="var(--gold)" />
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

	.banner-wrap {
		margin-bottom: var(--spacing-sm);
	}

	/* Caption: weekly reset rule */
	.lb-note {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		margin: 0 0 var(--spacing-md);
		font-size: 10px;
		color: var(--muted);
	}

	/* Loading */
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--muted);
		font-size: var(--font-size-sm);
	}

	/* "Hidden from leaderboard" panel */
	.lb-hidden {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm) var(--spacing-md) var(--spacing-md);
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		margin-bottom: var(--spacing-md);
	}
	.lb-hidden__head {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}
	.lb-hidden__txt {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}
	.lb-hidden__t {
		font-family: var(--font-display);
		font-size: var(--font-size-sm);
		color: var(--text);
	}
	.lb-hidden__s {
		font-size: 11px;
		color: var(--muted);
		line-height: 1.4;
	}

	/* Empty: nobody to compete with yet */
	.lb-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-lg) var(--spacing-md);
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		text-align: center;
	}
	.lb-empty__t {
		margin: var(--spacing-xs) 0 0;
		font-family: var(--font-display);
		font-size: var(--font-size-sm);
		color: var(--text);
	}
	.lb-empty__s {
		margin: 0 0 var(--spacing-sm);
		font-size: 11px;
		color: var(--muted);
		line-height: 1.5;
	}

	/* Podium */
	.podium {
		display: flex;
		justify-content: center;
		align-items: flex-end;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-lg);
		padding: var(--spacing-md) var(--spacing-md) var(--spacing-sm);
	}

	.podium-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm);
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		position: relative;
		cursor: pointer;
		font-family: var(--font-display);
		color: var(--text);
		transition: transform var(--transition-fast);
	}

	.podium-item.clickable:active {
		transform: translate(2px, 2px);
		box-shadow: var(--bevel);
	}

	.podium-item.first {
		padding: var(--spacing-md);
		background: var(--gold);
		margin-bottom: var(--spacing-md);
		color: var(--ink);
	}

	.podium-item.second {
		background: var(--podium2);
		padding-bottom: var(--spacing-md);
		color: var(--ink);
	}

	.podium-item.third {
		background: var(--podium3);
		padding-bottom: var(--spacing-md);
		color: var(--ink);
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
		font-family: var(--font-data);
		font-size: var(--font-size-xs);
		color: var(--ink);
		margin-bottom: 4px;
	}

	.podium-rank {
		position: absolute;
		bottom: -12px;
		width: 24px;
		height: 24px;
		background: var(--bg3);
		border: var(--bw) solid var(--line);
		color: var(--text);
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-data);
		font-size: var(--font-size-xs);
	}

	/* Leaderboard List */
	.leaderboard-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.entry-card {
		width: 100%;
		padding: var(--spacing-sm);
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		font-family: var(--font-ui);
		color: var(--text);
		cursor: pointer;
		text-align: left;
		transition: transform 0.08s;
	}

	.entry-card.clickable:active {
		transform: translate(2px, 2px);
		box-shadow: var(--bevel);
	}

	/* Current-user row sits on the cobalt accent block */
	.entry-card.accent {
		background: var(--accent);
		color: var(--on-accent);
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
		font-family: var(--font-data);
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
		background: var(--gold);
		color: var(--ink);
	}

	.entry-level {
		font-size: 8px;
		color: var(--muted);
	}

	.entry-card.accent .entry-level,
	.entry-card.accent .entry-xp,
	.entry-card.accent .entry-xp-label,
	.entry-card.accent .entry-streak {
		color: var(--on-accent);
	}

	.entry-stats {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}

	.entry-xp {
		font-family: var(--font-data);
		font-size: var(--font-size-sm);
		color: var(--gold);
	}

	.entry-xp-label {
		font-size: 10px;
		color: var(--muted);
	}

	.entry-streak {
		display: flex;
		align-items: center;
		gap: 2px;
		font-family: var(--font-data);
		font-size: var(--font-size-xs);
		color: var(--gold);
		min-width: 32px;
	}

	@keyframes pixel-bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-4px); }
	}
</style>
