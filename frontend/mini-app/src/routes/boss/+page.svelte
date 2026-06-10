<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon, PixelAvatar, PixelTabs, EmptyState, CountUp } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import type { Boss, BossLeaderboard, BossMyContribution, BossHistory, BossHistoryItem } from '$lib/types';

	let boss = $state<Boss | null>(null);
	let leaderboard = $state<BossLeaderboard | null>(null);
	let me = $state<BossMyContribution | null>(null);
	let history = $state<BossHistory | null>(null);

	let loading = $state(true);
	let claiming = $state(false);
	let claimMessage = $state<string | null>(null);
	let activeTab = $state<'current' | 'history'>('current');

	const tabs = [
		{ id: 'current' as const, label: 'Текущий' },
		{ id: 'history' as const, label: 'История' }
	];

	async function loadAll() {
		loading = true;
		try {
			const [b, lb, m, h] = await Promise.all([
				api.getCurrentBoss(),
				api.getBossLeaderboard(),
				api.getMyBossContribution(),
				api.getBossHistory()
			]);
			boss = b;
			leaderboard = lb;
			me = m;
			history = h;
		} catch (e) {
			console.error('Failed to load boss data:', e);
		} finally {
			loading = false;
		}
	}

	onMount(loadAll);

	async function handleClaim() {
		if (!boss || !me?.reward_claimable || claiming) return;
		claiming = true;
		try {
			const result = await api.claimBossReward(boss.id);
			claimMessage = `Получено: +${result.coins_awarded} монет!`;
			telegram.hapticNotification('success');
			await userStore.loadStats();
			await loadAll();
		} catch (e) {
			console.error('Claim failed:', e);
			telegram.hapticNotification('error');
			claimMessage = 'Не удалось забрать награду';
		} finally {
			claiming = false;
		}
	}

	const hpPercent = $derived.by(() => {
		if (!boss || boss.max_hp <= 0) return 0;
		return Math.max(0, Math.min(100, (boss.current_hp / boss.max_hp) * 100));
	});

	const barColor = $derived.by(() => {
		if (hpPercent > 50) return 'var(--pixel-green, #39d353)';
		if (hpPercent > 25) return 'var(--pixel-orange, #f59e0b)';
		return 'var(--pixel-red, #e02d29)';
	});

	function formatNum(n: number): string {
		return n.toLocaleString('ru-RU');
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
	}

	function statusLabel(status: string): string {
		if (status === 'defeated') return 'Повержен';
		if (status === 'expired') return 'Не побеждён';
		return 'В битве';
	}
</script>

<div class="boss-page">
	<header class="page-header">
		<a href="{base}/" class="back-link">
			<PixelIcon name="arrow-left" size="sm" />
		</a>
		<h1>Босс месяца</h1>
	</header>

	<PixelTabs
		tabs={tabs}
		activeTab={activeTab}
		onTabChange={(id) => (activeTab = id)}
	/>

	{#if loading}
		<div class="loading">Загрузка...</div>
	{:else if activeTab === 'current'}
		{#if boss}
			<PixelCard padding="md">
				<div class="boss-hero">
					<img src="{base}{boss.image_url}" alt={boss.name_ru} class="boss-img-large anim-floaty" />
					<div class="boss-hero__top">
						<span class="boss-title">{boss.name_ru}</span>
						<span class="status-pill status-{boss.status}">{statusLabel(boss.status)}</span>
					</div>
					<p class="boss-period">{formatDate(boss.start_date)} — {formatDate(boss.end_date)}</p>

					<div class="hp-section">
						<div class="hp-track-large">
							<div class="hp-fill-large anim-bar-grow" style="width: {hpPercent}%; background: {barColor};"></div>
						</div>
						<div class="hp-numbers">
							<span>{formatNum(boss.current_hp)} HP</span>
							<span class="hp-max">/ {formatNum(boss.max_hp)}</span>
						</div>
					</div>

					<p class="boss-legend">{boss.legend_ru}</p>
				</div>
			</PixelCard>

			<PixelCard padding="md">
				<h3 class="section-title">Твой вклад</h3>
				{#if me && me.total_damage > 0}
					<div class="me-stats">
						<div class="me-stat">
							<span class="me-value"><CountUp value={me.total_damage} /></span>
							<span class="me-label">урон</span>
						</div>
						<div class="me-stat">
							<span class="me-value">{me.rank ? `#${me.rank}` : '—'}</span>
							<span class="me-label">место</span>
						</div>
						<div class="me-stat">
							<span class="me-value">{me.attacks_count}</span>
							<span class="me-label">ударов</span>
						</div>
					</div>

					{#if me.reward_claimable}
						<div class="claim-card">
							<div class="claim-info">
								<span class="claim-coins">+<CountUp value={me.reward_coins} /></span>
								<span class="claim-text">монет ждут тебя</span>
								{#if me.is_top10}
									<span class="claim-top10">🏆 Топ-10</span>
								{/if}
							</div>
							<PixelButton
								variant="success"
								size="md"
								loading={claiming}
								onclick={handleClaim}
							>
								Забрать
							</PixelButton>
						</div>
					{:else if me.reward_claimed_at}
						<div class="claimed-msg">Награда уже получена ({formatNum(me.reward_coins)} монет)</div>
					{/if}

					{#if claimMessage}
						<div class="claim-toast">{claimMessage}</div>
					{/if}
				{:else}
					<p class="me-empty">Ты ещё не нанёс ни одного удара. Сделай тренировку — XP станет уроном по боссу.</p>
				{/if}
			</PixelCard>

			<PixelCard padding="md">
				<h3 class="section-title">Топ-10 по урону</h3>
				{#if leaderboard && leaderboard.entries.length > 0}
					<div class="leaderboard anim-rows">
						{#each leaderboard.entries as entry}
							<div class="lb-row" class:lb-me={me?.rank === entry.rank}>
								<span class="lb-rank">#{entry.rank}</span>
								<PixelAvatar avatarId={entry.avatar_id || 'shadow-wolf'} size="sm" />
								<span class="lb-name">
									{entry.username || entry.first_name || 'Игрок'}
								</span>
								<span class="lb-damage">{formatNum(entry.total_damage)}</span>
							</div>
						{/each}
					</div>
					{#if me && me.rank && me.rank > 10}
						<div class="lb-row lb-me lb-self-row">
							<span class="lb-rank">#{me.rank}</span>
							<span class="lb-name">Ты</span>
							<span class="lb-damage">{formatNum(me.total_damage)}</span>
						</div>
					{/if}
				{:else}
					<EmptyState
						title="Никто ещё не атаковал"
						message="Стань первым, кто ударит босса"
					/>
				{/if}
			</PixelCard>
		{/if}
	{:else if activeTab === 'history'}
		{#if history && history.bosses.length > 0}
			<div class="history-list anim-rows">
				{#each history.bosses as h (h.id)}
					<PixelCard padding="md">
						<div class="hist-row">
							<img src="{base}{h.image_url}" alt={h.name_ru} class="hist-img" />
							<div class="hist-info">
								<div class="hist-name">{h.name_ru}</div>
								<div class="hist-period">{formatDate(h.start_date)} — {formatDate(h.end_date)}</div>
								<div class="hist-status status-{h.status}">{statusLabel(h.status)}</div>
							</div>
							<div class="hist-stats">
								{#if h.my_total_damage > 0}
									<div class="hist-stat">
										<span class="hist-stat-val">{formatNum(h.my_total_damage)}</span>
										<span class="hist-stat-lbl">урон</span>
									</div>
									{#if h.my_rank}
										<div class="hist-stat">
											<span class="hist-stat-val">#{h.my_rank}</span>
											<span class="hist-stat-lbl">место</span>
										</div>
									{/if}
									{#if h.my_reward_coins > 0}
										<div class="hist-reward" class:hist-claimed={h.my_reward_claimed}>
											{h.my_reward_claimed ? '✓' : '+'}{h.my_reward_coins} м
										</div>
									{/if}
								{:else}
									<div class="hist-empty">Не участвовал</div>
								{/if}
							</div>
						</div>
					</PixelCard>
				{/each}
			</div>
		{:else}
			<EmptyState title="История пуста" message="Здесь будут появляться прошлые боссы" />
		{/if}
	{/if}
</div>

<style>
	.boss-page {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
	}

	.page-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.page-header h1 {
		font-size: var(--font-size-md);
		color: var(--text-primary);
		margin: 0;
	}

	.back-link {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		padding: var(--spacing-xs);
		display: flex;
		align-items: center;
		justify-content: center;
		text-decoration: none;
		color: var(--text-primary);
	}

	.loading {
		text-align: center;
		color: var(--text-muted);
		padding: var(--spacing-lg);
	}

	.boss-hero {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		text-align: center;
	}

	.boss-img-large {
		width: 120px;
		height: 120px;
		image-rendering: pixelated;
		flex-shrink: 0;
	}

	.boss-hero__top {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-sm);
		flex-wrap: wrap;
	}

	.boss-title {
		font-family: var(--font-display);
		font-size: var(--font-size-lg);
		margin: 0;
		color: var(--text-primary);
	}

	.boss-period {
		font-family: var(--font-data);
		font-size: var(--font-size-xs);
		color: var(--text-muted);
		margin: 0;
	}

	.status-pill {
		display: inline-block;
		font-size: 9px;
		padding: 2px 6px;
		border: 1px solid var(--border-color);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.status-active {
		color: var(--pixel-orange);
		border-color: var(--pixel-orange);
	}
	.status-defeated {
		color: var(--pixel-green);
		border-color: var(--pixel-green);
	}
	.status-expired {
		color: var(--text-muted);
	}

	.hp-section {
		display: flex;
		flex-direction: column;
		gap: 4px;
		width: 100%;
	}

	.hp-track-large {
		width: 100%;
		height: 14px;
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--border-color);
		overflow: hidden;
	}

	.hp-fill-large {
		height: 100%;
		transition: width 0.4s ease;
	}

	.hp-numbers {
		display: flex;
		gap: 4px;
		align-items: baseline;
		justify-content: center;
		font-family: var(--font-data);
		font-size: var(--font-size-xs);
		color: var(--text-primary);
	}

	.hp-max {
		color: var(--text-muted);
	}

	.boss-legend {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		line-height: 1.6;
		margin: 0;
	}

	.section-title {
		font-size: var(--font-size-sm);
		margin: 0 0 var(--spacing-sm) 0;
		color: var(--text-primary);
	}

	.me-stats {
		display: flex;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-md);
	}

	.me-stat {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		padding: var(--spacing-sm) var(--spacing-xs);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
	}

	.me-value {
		font-size: var(--font-size-md);
		color: var(--text-primary);
		font-family: var(--font-data);
	}

	.me-label {
		font-size: 9px;
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.me-empty {
		font-size: var(--font-size-xs);
		color: var(--text-muted);
		margin: 0;
		line-height: 1.5;
	}

	.claim-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm);
		background: var(--pixel-yellow);
		border: var(--border-width) solid var(--pixel-black);
	}

	.claim-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.claim-coins {
		font-size: var(--font-size-md);
		color: var(--ink);
		font-family: var(--font-data);
	}

	.claim-text {
		font-size: 9px;
		color: var(--ink);
		text-transform: uppercase;
	}

	.claim-top10 {
		font-size: 10px;
		color: var(--ink);
	}

	.claimed-msg {
		font-size: var(--font-size-xs);
		color: var(--text-muted);
		text-align: center;
	}

	.claim-toast {
		margin-top: var(--spacing-sm);
		text-align: center;
		font-size: var(--font-size-xs);
		color: var(--pixel-green);
	}

	.leaderboard {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.lb-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
	}

	.lb-self-row {
		margin-top: var(--spacing-sm);
	}

	.lb-me {
		border-color: var(--pixel-accent);
	}

	.lb-rank {
		font-size: var(--font-size-xs);
		color: var(--text-muted);
		min-width: 28px;
	}

	.lb-name {
		flex: 1;
		font-size: var(--font-size-xs);
		color: var(--text-primary);
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.lb-damage {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
	}

	.history-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.hist-row {
		display: flex;
		gap: var(--spacing-sm);
		align-items: flex-start;
	}

	.hist-img {
		width: 48px;
		height: 48px;
		image-rendering: pixelated;
		flex-shrink: 0;
	}

	.hist-info {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.hist-name {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
	}

	.hist-period {
		font-size: 9px;
		color: var(--text-muted);
	}

	.hist-status {
		font-size: 9px;
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.hist-stats {
		display: flex;
		flex-direction: column;
		gap: 4px;
		align-items: flex-end;
	}

	.hist-stat {
		display: flex;
		gap: 4px;
		align-items: baseline;
	}

	.hist-stat-val {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
	}

	.hist-stat-lbl {
		font-size: 9px;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	.hist-reward {
		font-size: var(--font-size-xs);
		color: var(--pixel-yellow);
	}

	.hist-claimed {
		color: var(--pixel-green);
	}

	.hist-empty {
		font-size: var(--font-size-xs);
		color: var(--text-muted);
	}
</style>
