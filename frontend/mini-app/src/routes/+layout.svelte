<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { token, isAuthenticated, isLoading } from '$lib/stores/auth';
	import { user } from '$lib/stores/user';
	import { api } from '$lib/api/client';
	import '../app.css';

	let { children } = $props();
	let debugInfo = $state('Initializing...');
	let mounted = $state(false);

	// Run immediately when script loads
	if (browser) {
		debugInfo = 'Browser detected';
		console.log('[BodyWeight] Browser detected, waiting for mount...');
	}

	onMount(() => {
		mounted = true;
		console.log('[BodyWeight] Component mounted');
		debugInfo = 'Mounted, checking Telegram...';

		initApp();
	});

	async function initApp() {
		console.log('[BodyWeight] initApp started');

		// Check Telegram WebApp
		const tg = (window as any).Telegram?.WebApp;
		console.log('[BodyWeight] Telegram WebApp:', tg ? 'found' : 'NOT FOUND');

		if (!tg) {
			debugInfo = 'ERROR: Telegram WebApp not found';
			console.error('[BodyWeight] Telegram WebApp not available');
			$isLoading = false;
			return;
		}

		// Initialize Telegram WebApp
		tg.ready();
		tg.expand();

		try {
			tg.setHeaderColor('#1a1a2e');
			tg.setBackgroundColor('#1a1a2e');
		} catch (e) {
			console.warn('[BodyWeight] Could not set colors:', e);
		}

		// Check initData
		const initData = tg.initData;
		console.log('[BodyWeight] initData:', initData ? `${initData.length} chars` : 'EMPTY');

		if (!initData) {
			debugInfo = 'ERROR: No initData from Telegram';
			console.error('[BodyWeight] No initData - app must be opened from Telegram bot');
			$isLoading = false;
			return;
		}

		debugInfo = 'Authenticating...';

		try {
			console.log('[BodyWeight] Calling API auth...');
			const result = await api.authTelegram(initData);
			console.log('[BodyWeight] Auth success:', result);

			$token = result.access_token;
			$isAuthenticated = true;

			debugInfo = 'Loading user data...';

			const userData = await api.getMe();
			console.log('[BodyWeight] User data:', userData);
			$user = userData;

			debugInfo = 'Ready!';
		} catch (error) {
			const message = error instanceof Error ? error.message : String(error);
			debugInfo = `ERROR: ${message}`;
			console.error('[BodyWeight] Auth error:', error);
		} finally {
			$isLoading = false;
		}
	}

	const navItems = [
		{ href: '', icon: '🏠', label: 'Главная' },
		{ href: '/workout', icon: '💪', label: 'Тренировка' },
		{ href: '/achievements', icon: '🏆', label: 'Награды' },
		{ href: '/leaderboard', icon: '📊', label: 'Рейтинг' },
		{ href: '/profile', icon: '⚔️', label: 'Профиль' },
	];

	function isActive(href: string): boolean {
		const currentPath = $page.url.pathname;
		const fullHref = `${base}${href}`;
		if (href === '') {
			return currentPath === base || currentPath === `${base}/`;
		}
		return currentPath.startsWith(fullHref);
	}
</script>

{#if $isLoading}
	<div class="loading-screen">
		<div class="loading-content">
			<div class="loading-icon">💪</div>
			<div class="loading-text">LOADING...</div>
			<div class="loading-bar">
				<div class="loading-fill"></div>
			</div>
			<div class="debug-info">{debugInfo}</div>
		</div>
	</div>
{:else}
	{@render children()}

	<nav class="nav-bottom">
		{#each navItems as item}
			<a
				href="{base}{item.href}"
				class="nav-item"
				class:active={isActive(item.href)}
			>
				<span class="nav-icon">{item.icon}</span>
				<span>{item.label}</span>
			</a>
		{/each}
	</nav>
{/if}

<style>
	.loading-screen {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: var(--bg-dark);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.loading-content {
		text-align: center;
	}

	.loading-icon {
		font-size: 48px;
		animation: bounce 1s infinite;
	}

	.loading-text {
		font-family: 'Press Start 2P', monospace;
		font-size: 12px;
		color: var(--accent);
		margin-top: var(--space-lg);
	}

	.loading-bar {
		width: 200px;
		height: 16px;
		background: var(--bg-medium);
		border: 4px solid var(--border);
		margin-top: var(--space-md);
		overflow: hidden;
	}

	.loading-fill {
		height: 100%;
		background: var(--secondary);
		animation: load 1.5s ease-in-out infinite;
	}

	.debug-info {
		font-size: 10px;
		color: #888;
		margin-top: var(--space-lg);
		word-break: break-all;
		max-width: 280px;
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}

	@keyframes load {
		0% { width: 0%; }
		50% { width: 100%; }
		100% { width: 0%; }
	}
</style>
