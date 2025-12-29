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

	// Map exercise slugs to SVG filenames
	const exerciseMap: Record<string, string> = {
		'squat': 'squat-regular',
		'squat-regular': 'squat-regular',
		'pushup': 'pushup-regular',
		'pushup-regular': 'pushup-regular',
		'pushup-knee': 'pushup-knee',
		'pushup-diamond': 'pushup-diamond',
		'superman': 'superman',
		'superman-twist': 'superman-twist',
		'squat-sumo': 'squat-sumo',
		'lunge-stationary': 'lunge-stationary',
		'plank': 'plank',
		'plank-side': 'plank-side',
		'bird-dog': 'bird-dog',
		'child-pose': 'child-pose',
		'reverse-hyperextension': 'reverse-hyperextension',
		'hyperextension-reverse': 'reverse-hyperextension',
		'plank-leg-raise': 'plank-leg-raise',
		'plank-leg-lift': 'plank-leg-raise',
		'butterfly': 'butterfly',
		'butterfly-stretch': 'butterfly',
		'arm-circles': 'arm-circles',
		'arm-circle': 'arm-circles'
	};

	const svgFile = $derived(exerciseMap[exercise] || null);
	const svgPath = $derived(svgFile ? `/sprites/exercises/${svgFile}.svg` : null);
</script>

<div class="exercise-animation" style="--size: {pixelSize}px">
	{#if svgPath}
		<object type="image/svg+xml" data={svgPath} class="pixel-svg" aria-label={exercise}>
			<span class="fallback">?</span>
		</object>
	{:else}
		<div class="placeholder">
			<span>?</span>
		</div>
	{/if}

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
		width: 100%;
		height: auto;
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

	.placeholder,
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
