<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { token, isAuthenticated, isLoading } from '$lib/stores/auth';
	import { user } from '$lib/stores/user';
	import { api } from '$lib/api/client';
	import '../app.css';

	let { children } = $props();
	let debugInfo = $state('Starting...');

	onMount(async () => {
		if (!browser) return;

		debugInfo = 'onMount started';
		console.log('onMount started');

		const tg = window.Telegram?.WebApp;
		debugInfo = `Telegram WebApp: ${tg ? 'found' : 'NOT FOUND'}`;
		console.log('Telegram WebApp:', tg);

		if (!tg) {
			debugInfo = 'ERROR: Telegram WebApp not available';
			console.error('Telegram WebApp not available');
			$isLoading = false;
			return;
		}

		tg.ready();
		tg.expand();
		tg.setHeaderColor('#1a1a2e');
		tg.setBackgroundColor('#1a1a2e');

		const initData = tg.initData;
		debugInfo = `initData: ${initData ? initData.length + ' chars' : 'EMPTY'}`;
		console.log('initData:', initData ? 'present (' + initData.length + ' chars)' : 'empty');

		if (!initData) {
			debugInfo = 'ERROR: No init data from Telegram';
			console.error('No init data');
			$isLoading = false;
			return;
		}

		try {
			debugInfo = 'Calling API auth...';
			console.log('Calling authTelegram...');
			const result = await api.authTelegram(initData);
			debugInfo = 'Auth OK, getting user...';
			console.log('Auth result:', result);
			$token = result.access_token;
			$isAuthenticated = true;

			const userData = await api.getMe();
			debugInfo = 'User loaded!';
			console.log('User data:', userData);
			$user = userData;
		} catch (error) {
			debugInfo = `ERROR: ${error instanceof Error ? error.message : String(error)}`;
			console.error('Auth error:', error);
		} finally {
			$isLoading = false;
		}
	});

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

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}

	@keyframes load {
		0% { width: 0%; }
		50% { width: 100%; }
		100% { width: 0%; }
	}

	.debug-info {
		font-size: 10px;
		color: #888;
		margin-top: var(--space-lg);
		word-break: break-all;
		max-width: 280px;
	}
</style>
