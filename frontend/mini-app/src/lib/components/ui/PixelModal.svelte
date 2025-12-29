<script lang="ts">
	import { telegram } from '$lib/stores/telegram.svelte';
	import PixelButton from './PixelButton.svelte';

	interface Props {
		open?: boolean;
		title?: string;
		onclose?: () => void;
	}

	let {
		open = false,
		title = '',
		onclose,
		children
	}: Props & { children?: any } = $props();

	function handleClose() {
		telegram.hapticImpact('light');
		onclose?.();
	}

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			handleClose();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			handleClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="modal-backdrop" onclick={handleBackdropClick}>
		<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
			{#if title}
				<div class="modal-header">
					<h3 id="modal-title">{title}</h3>
					<button class="close-btn" onclick={handleClose} aria-label="Close">
						<svg viewBox="0 0 16 16" fill="currentColor">
							<path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="2"/>
						</svg>
					</button>
				</div>
			{/if}
			<div class="modal-content">
				{@render children?.()}
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-md);
		z-index: 2000;
		animation: fade-in 0.15s ease-out;
	}

	.modal {
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		box-shadow: var(--shadow-lg);
		width: 100%;
		max-width: 360px;
		max-height: 80vh;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		animation: slide-up 0.2s ease-out;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-md);
		border-bottom: 2px solid var(--border-color);
		background: var(--pixel-bg-dark);
	}

	.modal-header h3 {
		font-size: var(--font-size-sm);
		margin: 0;
	}

	.close-btn {
		width: 24px;
		height: 24px;
		padding: 0;
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.close-btn:hover {
		color: var(--pixel-accent);
	}

	.close-btn svg {
		width: 12px;
		height: 12px;
	}

	.modal-content {
		padding: var(--spacing-md);
		overflow-y: auto;
	}

	@keyframes fade-in {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	@keyframes slide-up {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
