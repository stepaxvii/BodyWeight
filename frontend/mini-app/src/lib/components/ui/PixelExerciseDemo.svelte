<script lang="ts">
	import { base } from '$app/paths';

	interface Props {
		exercise?: string; // slug (optional if gifUrl provided)
		gifUrl?: string; // direct URL from API
		size?: 'sm' | 'md' | 'lg';
		tip?: string;
		autoplay?: boolean; // kept for API compatibility, animation is always on via CSS
	}

	let { exercise, gifUrl, size = 'md', tip = '', autoplay = true }: Props = $props();

	const sizeMap = {
		sm: 64,
		md: 128,
		lg: 192
	};

	const pixelSize = $derived(sizeMap[size]);

	// Alias map for exercises with different slugs than their SVG filenames (legacy fallback)
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

	// Use gifUrl from API if provided, otherwise fallback to slug-based path
	const svgPath = $derived.by(() => {
		if (gifUrl) return gifUrl;
		if (!exercise) return '';
		const svgFile = aliasMap[exercise] || exercise;
		return `${base}/sprites/exercises/${svgFile}.svg`;
	});
</script>

<div class="exercise-animation" style="--size: {pixelSize}px">
	<img
		src={svgPath}
		alt={exercise}
		class="pixel-svg"
		onerror={(e) => {
			const img = e.currentTarget as HTMLImageElement;
			img.style.display = 'none';
			const fallback = img.nextElementSibling as HTMLElement;
			if (fallback) fallback.style.display = 'flex';
		}}
	/>
	<div class="fallback" style="display: none;">
		<svg viewBox="0 0 16 16" fill="currentColor" class="fallback-icon">
			<path d="M2 6h2v4H2V6zm10 0h2v4h-2V6zM4 7h8v2H4V7z"/>
		</svg>
	</div>

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
		color: var(--text-muted, #666);
	}

	.fallback-icon {
		width: 50%;
		height: 50%;
	}
</style>
