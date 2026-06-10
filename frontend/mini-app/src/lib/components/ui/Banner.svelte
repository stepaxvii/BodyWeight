<script lang="ts">
	import PixelIcon from './PixelIcon.svelte';
	import type { Snippet } from 'svelte';

	// Neo screen header (mocha colour-block): icon slot + title + context, with an
	// optional right-side action and a faint corner deco. Styles live in hud.css
	// (.banner / .banner__*); this only tweaks the slot tint for the mocha bg.
	interface Props {
		icon?: string;
		title: string;
		sub?: string;
		deco?: string;
		action?: Snippet;
	}
	let { icon, title, sub, deco, action }: Props = $props();
</script>

<header class="banner">
	{#if icon}
		<span class="banner__slot slot slot--md">
			<PixelIcon name={icon} size="md" color="currentColor" />
		</span>
	{/if}
	<div class="banner__txt">
		<span class="banner__t">{title}</span>
		{#if sub}<span class="banner__s">{sub}</span>{/if}
	</div>
	{#if action}{@render action()}{/if}
	{#if deco}
		<span class="banner__deco"><PixelIcon name={deco} size="xl" color="currentColor" /></span>
	{/if}
</header>

<style>
	/* The slot sits on the mocha hero — darken it; the bevel comes from .slot. */
	.banner__slot {
		background: rgba(0, 0, 0, 0.18);
	}
</style>
