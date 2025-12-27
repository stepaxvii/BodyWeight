<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { PixelNav } from '$lib/components/ui';
	import { telegram } from '$lib/stores/telegram';
	import { userStore } from '$lib/stores/user';

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

<div class="app">
	<main class="main-content">
		{@render children()}
	</main>
	<PixelNav />
</div>

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
</style>
