<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelIcon, PixelTabs, EmptyState } from '$lib/components/ui';
	import Banner from '$lib/components/ui/Banner.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { ChallengeListItem, ChallengeStatus } from '$lib/types';

	type Tab = 'active' | 'upcoming' | 'finished' | 'mine';
	const TAB_DEFS: { id: Tab; label: string }[] = [
		{ id: 'active', label: 'Идут' },
		{ id: 'upcoming', label: 'Скоро' },
		{ id: 'finished', label: 'Завершены' },
		{ id: 'mine', label: 'Мои' }
	];

	function rarOf(s: ChallengeStatus): string {
		return s === 'active' ? 'r2' : s === 'upcoming' ? 'r3' : 'r1';
	}

	let activeTab = $state<Tab>('active');
	let lists = $state<Record<Tab, ChallengeListItem[]>>({
		active: [],
		upcoming: [],
		finished: [],
		mine: []
	});
	let loading = $state(true);

	const items = $derived(lists[activeTab]);
	const counts = $derived<Record<Tab, number>>({
		active: lists.active.length,
		upcoming: lists.upcoming.length,
		finished: lists.finished.length,
		mine: lists.mine.length
	});
	// Tab labels carry a count so the user knows where the action is.
	const tabs = $derived(
		TAB_DEFS.map((t) => ({ id: t.id, label: counts[t.id] > 0 ? `${t.label} ${counts[t.id]}` : t.label }))
	);
	// The active challenge the user is in — pinned at top for quick re-entry.
	const featured = $derived(lists.active.find((c) => c.is_member) ?? null);

	async function loadAll() {
		loading = true;
		try {
			const [active, upcoming, finished, mine] = await Promise.all([
				api.listChallenges({ status: 'active' }),
				api.listChallenges({ status: 'upcoming' }),
				api.listChallenges({ status: 'finished' }),
				api.listChallenges({ mine: true })
			]);
			lists = { active, upcoming, finished, mine };
		} catch (e) {
			console.error('Failed to load challenges:', e);
		} finally {
			loading = false;
		}
	}

	onMount(loadAll);

	function fmtDate(iso: string): string {
		return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
	}

	function statusLabel(s: ChallengeStatus): string {
		if (s === 'upcoming') return 'Скоро';
		if (s === 'active') return 'Идёт';
		return 'Завершён';
	}
</script>

<div class="challenges-page">
	<Banner icon="calendar" title="Челленджи" sub="Соревнуйся и забирай награды" deco="trophy">
		{#snippet action()}
			<a href="{base}/challenges/new" class="banner-new" aria-label="Создать челлендж">
				<PixelIcon name="plus" size="md" color="currentColor" />
			</a>
		{/snippet}
	</Banner>

	{#if featured}
		<a href="{base}/challenges/{featured.id}" class="chal-hero">
			<div class="chal-hero__top">
				<span class="chal-hero__label"><PixelIcon name="trophy" size="sm" color="var(--gold)" /> Твой активный челлендж</span>
				<span class="chal-hero__pct">{featured.completion_percent ?? 0}%</span>
			</div>
			<span class="chal-hero__title">{featured.title}</span>
			<div class="chal-hero__bar"><div class="chal-hero__fill" style="width: {featured.completion_percent ?? 0}%"></div></div>
			<span class="chal-hero__go"><PixelIcon name="play" size="sm" color="var(--on-accent)" /> Продолжить</span>
		</a>
	{/if}

	<PixelTabs
		tabs={tabs}
		activeTab={activeTab}
		onTabChange={(id) => (activeTab = id)}
	/>

	{#if loading}
		<div class="loading">Загрузка...</div>
	{:else if items.length === 0}
		<EmptyState
			title="Пусто"
			message={activeTab === 'mine' ? 'Ты ещё не создал и не присоединился ни к одному челленджу' : 'Нет челленджей'}
			buttonText="Создать челлендж"
			onButtonClick={() => (window.location.href = `${base}/challenges/new`)}
		/>
	{:else}
		<div class="challenge-list anim-rows">
			{#each items as item (item.id)}
				<a href="{base}/challenges/{item.id}" class="item chal-item {rarOf(item.status)}">
					<span class="item__edge"></span>
					<div class="chal-top">
						<span class="item__name">{item.title}</span>
						<span class="status status--{item.status}">{statusLabel(item.status)}</span>
					</div>
					<div class="chal-meta">
						<span><PixelIcon name="calendar" size="sm" color="var(--muted)" /> {fmtDate(item.start_date)} — {fmtDate(item.end_date)}</span>
						{#if item.creator_name}<span>от @{item.creator_name}</span>{/if}
					</div>
					<div class="chal-meta">
						<span class="item__tag"><PixelIcon name="users" size="sm" color="var(--muted)" /> {item.participants_count}</span>
						<span class="item__tag"><PixelIcon name="dumbbell" size="sm" color="var(--muted)" /> {item.exercises_count} упр.</span>
						{#if item.is_member}<span class="chal-mem"><PixelIcon name="check" size="sm" color="#fff" /> участвуешь</span>{/if}
					</div>
					{#if item.is_member && item.status === 'active' && item.completion_percent !== null}
						<div class="chal-prog">
							<div class="chal-prog__bar"><div class="chal-prog__fill" style="width: {item.completion_percent}%"></div></div>
							<span class="chal-prog__pct">{item.completion_percent}%{#if item.completed_days !== null} · {item.completed_days}/{item.total_days} дн.{/if}</span>
						</div>
					{/if}
					{#if item.reward_claimable}
						<div class="chal-claim"><PixelIcon name="coin" size="sm" color="var(--gold)" /> Забери награду: +{item.reward_coins}</div>
					{/if}
				</a>
			{/each}
		</div>
	{/if}
</div>

<style>
	.challenges-page {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
	}

	.banner-new {
		flex: 0 0 auto;
		display: grid;
		place-items: center;
		width: 36px;
		height: 36px;
		background: rgba(0, 0, 0, 0.2);
		border: 2px solid rgba(0, 0, 0, 0.3);
		color: var(--hero-text);
		text-decoration: none;
	}

	.loading {
		text-align: center;
		color: var(--text-muted);
		padding: var(--spacing-lg);
	}

	.challenge-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	/* challenge cards use the global .item kit, overridden to a column layout */
	.chal-item {
		flex-direction: column;
		align-items: stretch;
		gap: 9px;
		padding: 12px;
		text-decoration: none;
	}

	.chal-top {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 10px;
	}

	.chal-top .item__name {
		white-space: normal;
		overflow: visible;
		line-height: 1.35;
	}

	.chal-meta {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 7px;
		font-size: var(--font-size-xs);
		color: var(--muted);
	}

	.chal-meta span {
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}

	.status {
		flex-shrink: 0;
		font-family: var(--font-display);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		padding: 3px 7px;
		border: 2px solid currentColor;
		white-space: nowrap;
	}
	.status--active {
		color: var(--green);
	}
	.status--upcoming {
		color: var(--accent);
	}
	.status--finished {
		color: var(--muted);
	}

	/* Pinned hero — the user's active challenge */
	.chal-hero {
		display: flex;
		flex-direction: column;
		gap: 7px;
		padding: 12px;
		background: var(--hero-bg);
		border: var(--bw) solid var(--hero-edge);
		box-shadow: var(--shadow);
		color: var(--hero-text);
		text-decoration: none;
	}
	.chal-hero__top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}
	.chal-hero__label {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-size: 11px;
		opacity: 0.9;
	}
	.chal-hero__pct {
		font-family: var(--font-data);
		font-size: 16px;
		color: var(--hero-num);
	}
	.chal-hero__title {
		font-family: var(--font-display);
		font-size: 15px;
		line-height: 1.3;
	}
	.chal-hero__bar {
		height: 8px;
		background: rgba(0, 0, 0, 0.25);
		border: 2px solid var(--hero-edge);
	}
	.chal-hero__fill {
		height: 100%;
		background: var(--gold);
		transition: width 0.4s ease;
	}
	.chal-hero__go {
		align-self: flex-start;
		display: inline-flex;
		align-items: center;
		gap: 5px;
		margin-top: 2px;
		padding: 5px 12px;
		background: var(--accent);
		color: var(--on-accent);
		font-family: var(--font-display);
		font-size: 12px;
	}

	/* Personal progress on a card (active member) */
	.chal-prog {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.chal-prog__bar {
		flex: 1;
		height: 7px;
		background: var(--bg3);
		border: 2px solid var(--line);
		overflow: hidden;
	}
	.chal-prog__fill {
		height: 100%;
		background: var(--green);
		transition: width 0.4s ease;
	}
	.chal-prog__pct {
		flex: 0 0 auto;
		font-family: var(--font-data);
		font-size: 11px;
		color: var(--muted);
	}

	/* Claimable reward signal on a finished card */
	.chal-claim {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		align-self: flex-start;
		padding: 4px 9px;
		background: var(--gold);
		color: var(--ink);
		font-family: var(--font-display);
		font-size: 11px;
	}
</style>
