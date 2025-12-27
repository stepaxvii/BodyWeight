<script lang="ts">
	import { telegram } from '$lib/stores/telegram';

	interface Props {
		variant?: 'default' | 'accent' | 'success' | 'warning';
		hoverable?: boolean;
		onclick?: () => void;
		padding?: 'none' | 'sm' | 'md' | 'lg';
	}

	let {
		variant = 'default',
		hoverable = false,
		onclick,
		padding = 'md',
		children
	}: Props & { children?: any } = $props();

	function handleClick() {
		if (onclick) {
			telegram.hapticImpact('light');
			onclick();
		}
	}
</script>

<div
	class="pixel-card {variant} padding-{padding}"
	class:hoverable
	class:clickable={!!onclick}
	role={onclick ? 'button' : undefined}
	tabindex={onclick ? 0 : undefined}
	onclick={handleClick}
	onkeydown={(e) => e.key === 'Enter' && handleClick()}
>
	{@render children?.()}
</div>

<style>
	.pixel-card {
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		box-shadow: var(--shadow-sm);
		position: relative;
	}

	/* Padding variants */
	.pixel-card.padding-none { padding: 0; }
	.pixel-card.padding-sm { padding: var(--spacing-sm); }
	.pixel-card.padding-md { padding: var(--spacing-md); }
	.pixel-card.padding-lg { padding: var(--spacing-lg); }

	/* Color variants */
	.pixel-card.accent {
		border-color: var(--pixel-accent);
	}

	.pixel-card.success {
		border-color: var(--pixel-green);
	}

	.pixel-card.warning {
		border-color: var(--pixel-yellow);
	}

	/* Hoverable state */
	.pixel-card.hoverable {
		transition: transform var(--transition-fast),
					box-shadow var(--transition-fast),
					border-color var(--transition-fast);
	}

	.pixel-card.hoverable:hover {
		transform: translate(-2px, -2px);
		box-shadow: var(--shadow-md);
		border-color: var(--pixel-accent);
	}

	/* Clickable state */
	.pixel-card.clickable {
		cursor: pointer;
	}

	.pixel-card.clickable:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}
</style>
