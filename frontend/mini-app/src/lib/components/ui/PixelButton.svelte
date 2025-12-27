<script lang="ts">
	import { telegram } from '$lib/stores/telegram.svelte';

	interface Props {
		variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
		size?: 'sm' | 'md' | 'lg';
		disabled?: boolean;
		loading?: boolean;
		fullWidth?: boolean;
		onclick?: () => void;
		type?: 'button' | 'submit' | 'reset';
	}

	let {
		variant = 'primary',
		size = 'md',
		disabled = false,
		loading = false,
		fullWidth = false,
		onclick,
		type = 'button',
		children
	}: Props & { children?: any } = $props();

	function handleClick() {
		if (!disabled && !loading) {
			telegram.hapticImpact('medium');
			onclick?.();
		}
	}
</script>

<button
	{type}
	class="pixel-button {variant} {size}"
	class:full-width={fullWidth}
	class:loading
	disabled={disabled || loading}
	onclick={handleClick}
>
	{#if loading}
		<span class="spinner"></span>
	{/if}
	<span class="content" class:hidden={loading}>
		{@render children?.()}
	</span>
</button>

<style>
	.pixel-button {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-sm);
		font-family: var(--font-pixel);
		text-transform: uppercase;
		cursor: pointer;
		border: 2px solid;
		background: var(--pixel-card);
		color: var(--text-primary);
		transition: transform var(--transition-fast), box-shadow var(--transition-fast);
		position: relative;
		overflow: hidden;
	}

	/* Sizes */
	.pixel-button.sm {
		padding: var(--spacing-xs) var(--spacing-sm);
		font-size: var(--font-size-xs);
	}

	.pixel-button.md {
		padding: var(--spacing-sm) var(--spacing-md);
		font-size: var(--font-size-sm);
	}

	.pixel-button.lg {
		padding: var(--spacing-md) var(--spacing-lg);
		font-size: var(--font-size-md);
	}

	/* Variants */
	.pixel-button.primary {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent-hover);
		box-shadow: 4px 4px 0px var(--pixel-black);
	}

	.pixel-button.primary:hover:not(:disabled) {
		background: var(--pixel-accent-hover);
	}

	.pixel-button.secondary {
		background: var(--pixel-card);
		border-color: var(--border-light);
		box-shadow: 4px 4px 0px var(--pixel-black);
	}

	.pixel-button.secondary:hover:not(:disabled) {
		background: var(--pixel-card-hover);
		border-color: var(--pixel-accent);
	}

	.pixel-button.success {
		background: var(--pixel-green);
		border-color: var(--pixel-green-light);
		box-shadow: 4px 4px 0px var(--pixel-black);
	}

	.pixel-button.success:hover:not(:disabled) {
		background: var(--pixel-green-light);
	}

	.pixel-button.danger {
		background: var(--pixel-red);
		border-color: var(--pixel-orange);
		box-shadow: 4px 4px 0px var(--pixel-black);
	}

	.pixel-button.danger:hover:not(:disabled) {
		background: var(--pixel-orange);
	}

	.pixel-button.ghost {
		background: transparent;
		border-color: var(--border-color);
		box-shadow: none;
	}

	.pixel-button.ghost:hover:not(:disabled) {
		border-color: var(--pixel-accent);
		color: var(--pixel-accent);
	}

	/* States */
	.pixel-button:active:not(:disabled) {
		transform: translate(2px, 2px);
		box-shadow: 2px 2px 0px var(--pixel-black);
	}

	.pixel-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.pixel-button.full-width {
		width: 100%;
	}

	/* Loading */
	.spinner {
		width: 12px;
		height: 12px;
		border: 2px solid var(--text-primary);
		border-top-color: transparent;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.content.hidden {
		visibility: hidden;
	}

	.pixel-button.loading .spinner {
		position: absolute;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>
