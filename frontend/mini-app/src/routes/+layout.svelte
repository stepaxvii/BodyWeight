<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { PixelNav } from '$lib/components/ui';
	import OnboardingScreen from '$lib/components/OnboardingScreen.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';

	let { children } = $props();

	// Handle startParam navigation (deep links from notifications)
	function handleStartParam(param: string | null) {
		if (!param) return;

		// Map startParam values to routes
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
		// Wait for Telegram WebApp to be ready
		if (telegram.isReady && telegram.initData) {
			await userStore.authenticate(telegram.initData);
		} else {
			// Dev mode - authenticate with mock data
			await userStore.authenticate('');
		}

		// Handle deep link navigation after auth
		if (userStore.isAuthenticated && userStore.isOnboarded) {
			handleStartParam(telegram.startParam);
		}
	});
</script>

<svelte:head>
	<title>BodyWeight - Pixel Fitness</title>
	<meta name="description" content="8-bit style bodyweight workout tracker" />
</svelte:head>

{#if userStore.isLoading}
	<div class="loading-screen">
		<div class="loading-spinner"></div>
	</div>
{:else if userStore.error}
	<div class="error-screen">
		<div class="error-content">
			<h2>Ошибка</h2>
			<p>{userStore.error}</p>
		</div>
	</div>
{:else if userStore.isAuthenticated && !userStore.isOnboarded}
	<OnboardingScreen />
{:else if userStore.isAuthenticated}
	<div class="app">
		<main class="main-content">
			{@render children()}
		</main>
		<PixelNav />
	</div>
{:else}
	<div class="error-screen">
		<div class="error-content">
			<h2>Не авторизован</h2>
			<p>Откройте приложение через Telegram</p>
		</div>
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
