<script lang="ts">
	import { base } from '$app/paths';

	interface Props {
		exercise?: string; // slug (optional if gifUrl provided)
		gifUrl?: string; // direct URL from API
		size?: 'sm' | 'md' | 'lg';
		version?: 'v3' | 'v4'; // v3 = old animation, v4 = new collage
	}

	let { exercise, gifUrl, size = 'md', version = 'v4' }: Props = $props();

	const sizeMap = {
		sm: 64,
		md: 128,
		lg: 192
	};

	const pixelSize = $derived(sizeMap[size]);

	// Alias map for exercises
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

	// Use v4 structure if available
	const svgPath = $derived.by(() => {
		if (gifUrl) return gifUrl;
		if (!exercise) return '';
		const svgFile = aliasMap[exercise] || exercise;

		// Try v4 format first (folder-based with preview.svg)
		if (version === 'v4') {
			return `${base}/sprites/exercises/${svgFile}/preview.svg`;
		}

		// Fallback to v3 format (single animated SVG)
		return `${base}/sprites/exercises/${svgFile}.svg`;
	});
</script>

<div class="exercise-preview" style="--size: {pixelSize}px">
	<img
		src={svgPath}
		alt={exercise}
		class="pixel-svg"
		onerror={(e) => {
			const img = e.currentTarget as HTMLImageElement;
			// If v4 fails, try v3 fallback
			if (version === 'v4' && exercise) {
				const svgFile = aliasMap[exercise] || exercise;
				img.src = `${base}/sprites/exercises/${svgFile}.svg`;
			} else {
				img.style.display = 'none';
				const fallback = img.nextElementSibling as HTMLElement;
				if (fallback) fallback.style.display = 'flex';
			}
		}}
	/>
	<div class="fallback" style="display: none;">
		<svg viewBox="0 0 16 16" fill="currentColor" class="fallback-icon">
			<path d="M2 6h2v4H2V6zm10 0h2v4h-2V6zM4 7h8v2H4V7z"/>
		</svg>
	</div>
</div>

<style>
	.exercise-preview {
		width: var(--size);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.pixel-svg {
		width: 100%;
		height: auto;
		object-fit: contain;
		image-rendering: pixelated;
		image-rendering: crisp-edges;
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
