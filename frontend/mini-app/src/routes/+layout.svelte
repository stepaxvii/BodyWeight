<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { PixelNav } from '$lib/components/ui';
	import OnboardingScreen from '$lib/components/OnboardingScreen.svelte';
	import AuthScreen from '$lib/components/AuthScreen.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';

	let { children } = $props();
	let isTelegramApp = $state(false);
	let initialized = $state(false);

	// Handle startParam navigation (deep links from notifications)
	function handleStartParam(param: string | null) {
		if (!param) return;

		const routes: Record<string, string> = {
			friends_requests: '/friends?tab=requests',
			friends: '/friends',
			workout: '/workout',
		};

		const route = routes[param];
		if (route) {
			goto(route);
		}
	}

	onMount(async () => {
		// Detect if running inside Telegram WebApp
		isTelegramApp = !!(
			typeof window !== 'undefined' &&
			window.Telegram?.WebApp?.initData
		);

		if (isTelegramApp && telegram.isReady && telegram.initData) {
			// Telegram Mini App auth flow
			await userStore.authenticate(telegram.initData);

			if (userStore.isAuthenticated && userStore.isOnboarded) {
				handleStartParam(telegram.startParam);
			}
		} else if (!isTelegramApp) {
			// Browser: try to restore session from stored JWT
			await userStore.tryRestoreSession();
		} else {
			// Dev mode (no Telegram, no stored token)
			await userStore.authenticate('');
		}

		initialized = true;
	});
</script>

<svelte:head>
	<title>PixelFit - Pixel Fitness</title>
	<meta name="description" content="8-bit фитнес трекер с геймификацией" />
</svelte:head>

{#if !initialized || userStore.isLoading}
	<div class="loading-screen">
		<div class="loading-spinner"></div>
	</div>
{:else if userStore.error && userStore.isAuthenticated}
	<div class="error-screen">
		<div class="error-content">
			<h2>Ошибка</h2>
			<p>{userStore.error}</p>
		</div>
	</div>
{:else if !userStore.isAuthenticated}
	{#if isTelegramApp}
		<div class="error-screen">
			<div class="error-content">
				<h2>Не авторизован</h2>
				<p>Откройте приложение через Telegram</p>
			</div>
		</div>
	{:else}
		<AuthScreen />
	{/if}
{:else if !userStore.isOnboarded}
	<OnboardingScreen />
{:else}
	<div class="app">
		<main class="main-content">
			{@render children()}
		</main>
		<PixelNav />
	</div>
{/if}

<style>
	.app {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	.main-content {
		flex: 1;
		padding-bottom: 72px; /* Space for nav */
	}

	.loading-screen {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg);
	}

	.loading-spinner {
		width: 48px;
		height: 48px;
		border: 4px solid var(--border-color);
		border-top-color: var(--pixel-accent);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error-screen {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg);
		padding: 20px;
	}

	.error-content {
		text-align: center;
		color: var(--pixel-text);
	}

	.error-content h2 {
		color: var(--pixel-danger);
		margin-bottom: 8px;
	}
</style>
