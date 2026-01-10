<script lang="ts">
	import { PixelIcon, PixelButton } from '$lib/components/ui';
	import type { IconName } from './PixelIcon.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		icon?: IconName;
		title?: string;
		message: string;
		hint?: string;
		buttonText?: string;
		onButtonClick?: () => void;
		children?: Snippet;
	}

	let { icon, title, message, hint, buttonText, onButtonClick, children }: Props = $props();
</script>

<div class="empty-state">
	{#if icon}
		<PixelIcon name={icon} size="lg" color="var(--text-secondary)" />
	{/if}
	{#if title}
		<h3 class="empty-title">{title}</h3>
	{/if}
	<p class="empty-message">{message}</p>
	{#if hint}
		<p class="empty-hint">{hint}</p>
	{/if}
	{#if children}
		{@render children()}
	{/if}
	{#if buttonText && onButtonClick}
		<PixelButton variant="ghost" onclick={onButtonClick}>
			{buttonText}
		</PixelButton>
	{/if}
</div>

<style>
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-xl);
		text-align: center;
		color: var(--text-secondary);
	}

	.empty-title {
		margin: 0;
		font-size: var(--font-size-md);
		color: var(--text-primary);
	}

	.empty-message {
		margin: 0;
		font-size: var(--font-size-sm);
	}

	.empty-hint {
		margin: 0;
		font-size: var(--font-size-xs);
		color: var(--text-muted);
	}
</style>
