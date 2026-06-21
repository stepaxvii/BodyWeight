<script lang="ts">
	import { telegram } from '$lib/stores/telegram.svelte';
	import PixelIcon from './PixelIcon.svelte';

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
	<div class="sheet-overlay" onclick={handleBackdropClick}>
		<div class="sheet" role="dialog" aria-modal="true" aria-labelledby="modal-title">
			<span class="sheet__grip"></span>
			{#if title}
				<div class="sheet__head">
					<span class="sheet__title" id="modal-title">{title}</span>
					<button class="sheet__close" onclick={handleClose} aria-label="Закрыть">
						<PixelIcon name="close" size="sm" />
					</button>
				</div>
			{/if}
			{@render children?.()}
		</div>
	</div>
{/if}

<style>
	/* .sheet-overlay / .sheet / .sheet__* are ported from the designer's hud.css.
	   The kit positions the overlay absolute (for the prototype phone frame) at a
	   low z-index; in the real app we need it fixed to the viewport and above the
	   nav / fixed panels. */
	.sheet-overlay {
		position: fixed;
		z-index: 2000;
	}
</style>
