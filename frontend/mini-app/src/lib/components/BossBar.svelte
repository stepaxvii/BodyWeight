<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import type { Boss } from '$lib/types';

	let boss = $state<Boss | null>(null);
	let loading = $state(true);

	onMount(async () => {
		try {
			boss = await api.getCurrentBoss();
		} catch (e) {
			console.error('Failed to load boss:', e);
		} finally {
			loading = false;
		}
	});

	const hpPercent = $derived.by(() => {
		if (!boss || boss.max_hp <= 0) return 0;
		return Math.max(0, Math.min(100, (boss.current_hp / boss.max_hp) * 100));
	});

	const barColor = $derived.by(() => {
		if (hpPercent > 50) return 'var(--pixel-green, #39d353)';
		if (hpPercent > 25) return 'var(--pixel-orange, #f59e0b)';
		return 'var(--pixel-red, #e02d29)';
	});

	const isDefeated = $derived(boss?.status === 'defeated');
	const isExpired = $derived(boss?.status === 'expired');
</script>

{#if loading}
	<div class="boss-skeleton"></div>
{:else if boss}
	<a href="{base}/boss" class="boss-bar" class:defeated={isDefeated} class:expired={isExpired}>
		<div class="boss-emoji">{boss.image_emoji}</div>
		<div class="boss-content">
			<div class="boss-header">
				<span class="boss-name">{boss.name_ru}</span>
				<span class="boss-status">
					{#if isDefeated}
						ПОВЕРЖЕН
					{:else if isExpired}
						ИСТЁК
					{:else}
						{Math.round(hpPercent)}%
					{/if}
				</span>
			</div>
			<div class="hp-track">
				<div
					class="hp-fill"
					style="width: {hpPercent}%; background: {barColor};"
				></div>
			</div>
			<div class="boss-hp-text">
				{boss.current_hp.toLocaleString('ru-RU')} / {boss.max_hp.toLocaleString('ru-RU')} HP
			</div>
		</div>
	</a>
{/if}

<style>
	.boss-bar {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm) var(--spacing-md);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		text-decoration: none;
		color: var(--text-primary);
		transition: border-color var(--transition-fast);
		cursor: pointer;
	}

	.boss-bar:hover {
		border-color: var(--pixel-accent);
	}

	.boss-bar.defeated {
		border-color: var(--pixel-green, #39d353);
	}

	.boss-bar.expired {
		opacity: 0.7;
	}

	.boss-emoji {
		font-size: 32px;
		line-height: 1;
		flex-shrink: 0;
	}

	.boss-content {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.boss-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.boss-name {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.boss-status {
		font-size: 9px;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 1px;
		flex-shrink: 0;
	}

	.boss-bar.defeated .boss-status {
		color: var(--pixel-green, #39d353);
	}

	.hp-track {
		width: 100%;
		height: 8px;
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
		overflow: hidden;
	}

	.hp-fill {
		height: 100%;
		transition: width 0.4s ease;
	}

	.boss-hp-text {
		font-size: 9px;
		color: var(--text-muted);
	}

	.boss-skeleton {
		height: 56px;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		opacity: 0.4;
	}
</style>
