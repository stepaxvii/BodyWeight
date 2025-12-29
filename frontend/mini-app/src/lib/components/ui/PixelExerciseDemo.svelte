<script lang="ts">
	interface Props {
		exercise: string;
		size?: 'sm' | 'md' | 'lg';
		tip?: string;
		autoplay?: boolean; // kept for API compatibility, animation is always on via CSS
	}

	let { exercise, size = 'md', tip = '', autoplay = true }: Props = $props();

	const sizeMap = {
		sm: 64,
		md: 128,
		lg: 192
	};

	const pixelSize = $derived(sizeMap[size]);

	// Alias map for exercises with different slugs than their SVG filenames
	const aliasMap: Record<string, string> = {
		'squat': 'squat-regular',
		'pushup': 'pushup-regular',
		'hyperextension-reverse': 'reverse-hyperextension',
		'plank-leg-lift': 'plank-leg-raise',
		'butterfly-stretch': 'butterfly',
		'arm-circle': 'arm-circles',
		'hollow-hold': 'hollow-body-hold',
		'hang-passive': 'dead-hang'
	};

	// Use alias if exists, otherwise use slug directly (most SVGs match their slug)
	const svgFile = $derived(aliasMap[exercise] || exercise);
	const svgPath = $derived(`/sprites/exercises/${svgFile}.svg`);
</script>

<div class="exercise-animation" style="--size: {pixelSize}px">
	<img src={svgPath} alt={exercise} class="pixel-svg" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
	<div class="fallback" style="display: none;">?</div>

	{#if tip}
		<div class="tips">
			<span class="tip">{tip}</span>
		</div>
	{/if}
</div>

<style>
	.exercise-animation {
		width: var(--size);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.pixel-svg {
		width: var(--size);
		height: var(--size);
		object-fit: contain;
		image-rendering: pixelated;
		image-rendering: crisp-edges;
	}

	.tips {
		text-align: center;
		min-height: 24px;
	}

	.tip {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent, #fcc800);
		text-transform: uppercase;
	}

	.fallback {
		width: var(--size);
		height: var(--size);
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-card, #1a1a2e);
		border: 2px solid var(--border-color, #333);
		font-size: var(--font-size-2xl);
		color: var(--text-muted, #666);
	}
</style>
