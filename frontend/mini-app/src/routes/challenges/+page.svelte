<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelIcon, PixelTabs, EmptyState } from '$lib/components/ui';
	import Banner from '$lib/components/ui/Banner.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { ChallengeListItem, ChallengeStatus } from '$lib/types';

	type Tab = 'active' | 'upcoming' | 'finished' | 'mine';
	const tabs = [
		{ id: 'active' as const, label: 'Идут' },
		{ id: 'upcoming' as const, label: 'Скоро' },
		{ id: 'finished' as const, label: 'Завершены' },
		{ id: 'mine' as const, label: 'Мои' }
	];

	function rarOf(s: ChallengeStatus): string {
		return s === 'active' ? 'r2' : s === 'upcoming' ? 'r3' : 'r1';
	}

	let activeTab = $state<Tab>('active');
	let items = $state<ChallengeListItem[]>([]);
	let loading = $state(true);

	async function load() {
		loading = true;
		try {
			if (activeTab === 'mine') {
				items = await api.listChallenges({ mine: true });
			} else {
				items = await api.listChallenges({ status: activeTab as ChallengeStatus });
			}
		} catch (e) {
			console.error('Failed to load challenges:', e);
			items = [];
		} finally {
			loading = false;
		}
	}

	onMount(load);

	$effect(() => {
		// reload when tab changes
		activeTab; // dependency
		load();
	});

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
</style>
