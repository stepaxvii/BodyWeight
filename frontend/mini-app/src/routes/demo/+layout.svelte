<script lang="ts">
	import '../../app.css';

	let { children } = $props();
</script>

<svelte:head>
	<title>BodyWeight Demo</title>
</svelte:head>

<div class="demo-app">
	<main class="main-content">
		{@render children()}
	</main>
</div>

<style>
	.demo-app {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background: var(--pixel-bg);
	}

	.main-content {
		flex: 1;
	}
</style>
