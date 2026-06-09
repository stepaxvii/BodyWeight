<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon, PixelTabs, EmptyState } from '$lib/components/ui';
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
	<header class="page-header">
		<a href="{base}/" class="back-link">
			<PixelIcon name="arrow-left" size="sm" />
		</a>
		<h1>Челленджи</h1>
		<a href="{base}/challenges/new" class="new-btn">
			<PixelIcon name="plus" size="sm" />
			<span>Создать</span>
		</a>
	</header>

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
				<a href="{base}/challenges/{item.id}" class="challenge-card-link">
					<PixelCard padding="md">
						<div class="card-header">
							<div class="card-title">{item.title}</div>
							<div class="status-pill status-{item.status}">{statusLabel(item.status)}</div>
						</div>
						<div class="card-meta">
							<span>{fmtDate(item.start_date)} — {fmtDate(item.end_date)}</span>
						</div>
						<div class="card-stats">
							<div class="stat">
								<span class="stat-val">{item.participants_count}</span>
								<span class="stat-lbl">участников</span>
							</div>
							<div class="stat">
								<span class="stat-val">{item.exercises_count}</span>
								<span class="stat-lbl">упражнений</span>
							</div>
							{#if item.creator_name}
								<div class="creator">от @{item.creator_name}</div>
							{/if}
						</div>
						{#if item.is_member}
							<div class="member-badge">Ты участвуешь</div>
						{/if}
					</PixelCard>
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

	.page-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.page-header h1 {
		font-size: var(--font-size-md);
		color: var(--text-primary);
		margin: 0;
		flex: 1;
	}

	.back-link, .new-btn {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		padding: var(--spacing-xs) var(--spacing-sm);
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-xs);
		text-decoration: none;
		color: var(--text-primary);
		font-size: var(--font-size-xs);
	}

	.new-btn {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
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

	.challenge-card-link {
		text-decoration: none;
		color: inherit;
	}

	.card-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-xs);
	}

	.card-title {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
		flex: 1;
	}

	.status-pill {
		font-size: 9px;
		padding: 2px 6px;
		border: 1px solid var(--border-color);
		text-transform: uppercase;
		letter-spacing: 1px;
		flex-shrink: 0;
	}

	.status-upcoming {
		color: var(--pixel-accent);
		border-color: var(--pixel-accent);
	}
	.status-active {
		color: var(--pixel-green);
		border-color: var(--pixel-green);
	}
	.status-finished {
		color: var(--text-muted);
	}

	.card-meta {
		font-size: 11px;
		color: var(--text-muted);
		margin-bottom: var(--spacing-xs);
	}

	.card-stats {
		display: flex;
		align-items: baseline;
		gap: var(--spacing-md);
	}

	.stat {
		display: flex;
		gap: 4px;
		align-items: baseline;
	}

	.stat-val {
		font-size: var(--font-size-sm);
		color: var(--pixel-accent);
	}

	.stat-lbl {
		font-size: 9px;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	.creator {
		margin-left: auto;
		font-size: 10px;
		color: var(--text-muted);
	}

	.member-badge {
		margin-top: var(--spacing-xs);
		font-size: 10px;
		color: #fff;
		background: var(--pixel-green);
		border: var(--border-width) solid var(--pixel-green);
		padding: 2px 6px;
		display: inline-block;
		text-transform: uppercase;
		letter-spacing: 1px;
	}
</style>
