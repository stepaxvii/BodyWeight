<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { PixelNav } from '$lib/components/ui';
	import OnboardingScreen from '$lib/components/OnboardingScreen.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';

	let { children } = $props();

	onMount(async () => {
		// Wait for Telegram WebApp to be ready
		if (telegram.isReady && telegram.initData) {
			await userStore.authenticate(telegram.initData);
		} else {
			// Dev mode - authenticate with mock data
			await userStore.authenticate('');
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
{:else if userStore.isAuthenticated && !userStore.isOnboarded}
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
</style>
