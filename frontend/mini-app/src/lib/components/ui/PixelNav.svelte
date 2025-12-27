<script lang="ts">
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { NavItem } from '$lib/types';

	interface NavItemConfig {
		id: NavItem;
		label: string;
		href: string;
		icon: string;
	}

	const navItems: NavItemConfig[] = [
		{ id: 'home', label: 'Home', href: `${base}/`, icon: 'home' },
		{ id: 'workout', label: 'Workout', href: `${base}/workout`, icon: 'workout' },
		{ id: 'profile', label: 'Profile', href: `${base}/profile`, icon: 'profile' },
		{ id: 'leaderboard', label: 'Board', href: `${base}/leaderboard`, icon: 'trophy' }
	];

	function isActive(href: string, pathname: string): boolean {
		if (href === `${base}/`) {
			return pathname === `${base}/` || pathname === base;
		}
		return pathname.startsWith(href);
	}

	function handleNavClick() {
		telegram.hapticImpact('light');
	}
</script>

<nav class="pixel-nav">
	<div class="nav-container">
		{#each navItems as item}
			{@const active = isActive(item.href, $page.url.pathname)}
			<a
				href={item.href}
				class="nav-item"
				class:active
				onclick={handleNavClick}
				aria-current={active ? 'page' : undefined}
			>
				<div class="icon-wrapper">
					<svg class="icon" viewBox="0 0 16 16" fill="currentColor">
						{#if item.icon === 'home'}
							<path d="M8 1L1 7h2v7h4v-4h2v4h4V7h2L8 1zm0 2.5L12 7v6h-2v-4H6v4H4V7l4-3.5z"/>
						{:else if item.icon === 'workout'}
							<path d="M2 7h2v2H2V7zm10 0h2v2h-2V7zM5 6h6v4H5V6zm0 5h6v1H5v-1zm0-7h6v1H5V4z"/>
						{:else if item.icon === 'profile'}
							<path d="M8 2a3 3 0 100 6 3 3 0 000-6zM4 10c0-1 1-2 4-2s4 1 4 2v3H4v-3z"/>
						{:else if item.icon === 'trophy'}
							<path d="M4 2h8v2h2v3c0 1-1 2-2 2h-1c0 2-1 3-3 3s-3-1-3-3H4c-1 0-2-1-2-2V4h2V2zm1 2v2h1c0 1 1 2 2 2s2-1 2-2h1V4H5zm1 8h4v2H6v-2z"/>
						{/if}
					</svg>
				</div>
				<span class="label">{item.label}</span>
				{#if active}
					<div class="active-indicator"></div>
				{/if}
			</a>
		{/each}
	</div>
</nav>

<style>
	.pixel-nav {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		background: var(--pixel-bg-dark);
		border-top: 2px solid var(--border-color);
		z-index: 100;
		padding-bottom: env(safe-area-inset-bottom, 0);
	}

	.nav-container {
		display: flex;
		justify-content: space-around;
		align-items: center;
		max-width: 480px;
		margin: 0 auto;
		padding: var(--spacing-sm) 0;
	}

	.nav-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-xs) var(--spacing-md);
		color: var(--text-secondary);
		text-decoration: none;
		position: relative;
		transition: color var(--transition-fast);
	}

	.nav-item:hover {
		color: var(--text-primary);
	}

	.nav-item.active {
		color: var(--pixel-accent);
	}

	.icon-wrapper {
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.icon {
		width: 16px;
		height: 16px;
		image-rendering: pixelated;
	}

	.label {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
	}

	.active-indicator {
		position: absolute;
		top: -2px;
		left: 50%;
		transform: translateX(-50%);
		width: 4px;
		height: 4px;
		background: var(--pixel-accent);
	}
</style>
