<script lang="ts" generics="T extends string">
	import type { Snippet } from 'svelte';
	import { telegram } from '$lib/stores/telegram.svelte';

	interface Tab<T> {
		id: T;
		label: string;
		badge?: number;
		icon?: Snippet;
	}

	interface Props<T extends string> {
		tabs: Tab<T>[];
		activeTab: T;
		onTabChange: (tabId: T) => void;
	}

	let { tabs, activeTab, onTabChange }: Props<T> = $props();

	function handleTabClick(tabId: T) {
		onTabChange(tabId);
		telegram.hapticImpact('light');
	}
</script>

<div class="tabs">
	{#each tabs as tab}
		<button
			class="tab"
			class:active={activeTab === tab.id}
			onclick={() => handleTabClick(tab.id)}
		>
			{#if tab.icon}
				{@render tab.icon()}
			{/if}
			{tab.label}
			{#if tab.badge !== undefined && tab.badge > 0}
				<span class="badge">{tab.badge}</span>
			{/if}
		</button>
	{/each}
</div>

<style>
	.tabs {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-lg);
	}

	.tab {
		flex: 1 1 auto;
		min-width: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		border-radius: var(--radius-sm);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all var(--transition-fast);
		position: relative;
	}

	.tab:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent-hover);
		color: var(--pixel-bg);
	}

	.badge {
		position: absolute;
		top: -4px;
		right: -4px;
		min-width: 16px;
		height: 16px;
		padding: 0 4px;
		font-size: 8px;
		background: var(--pixel-red);
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
	}
</style>
