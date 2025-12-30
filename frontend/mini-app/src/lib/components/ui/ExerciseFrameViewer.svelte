<script lang="ts">
	import { base } from '$app/paths';
	import { telegram } from '$lib/stores/telegram.svelte';

	interface Props {
		exercise: string; // slug
		currentFrame?: number;
		onFrameChange?: (frame: number) => void;
	}

	let { exercise, currentFrame = 1, onFrameChange }: Props = $props();

	// Alias map
	const aliasMap: Record<string, string> = {
		'squat': 'squat-regular',
		'pushup': 'pushup-regular'
	};

	const svgFile = $derived(aliasMap[exercise] || exercise);

	// Detect available frames (try up to 4)
	let availableFrames = $state<number[]>([]);
	let activeFrame = $state(currentFrame);

	// Check which frames exist
	$effect(() => {
		const frames: number[] = [];
		for (let i = 1; i <= 4; i++) {
			const img = new Image();
			img.src = `${base}/sprites/exercises/${svgFile}/frame-${i}.svg`;
			img.onload = () => {
				if (!frames.includes(i)) {
					frames.push(i);
					availableFrames = [...frames].sort();
				}
			};
		}
	});

	function selectFrame(frame: number) {
		activeFrame = frame;
		telegram.hapticImpact('light');
		onFrameChange?.(frame);
	}

	function nextFrame() {
		const currentIndex = availableFrames.indexOf(activeFrame);
		const nextIndex = (currentIndex + 1) % availableFrames.length;
		selectFrame(availableFrames[nextIndex]);
	}

	function prevFrame() {
		const currentIndex = availableFrames.indexOf(activeFrame);
		const prevIndex = (currentIndex - 1 + availableFrames.length) % availableFrames.length;
		selectFrame(availableFrames[prevIndex]);
	}

	const framePath = $derived(`${base}/sprites/exercises/${svgFile}/frame-${activeFrame}.svg`);
</script>

<div class="frame-viewer">
	<!-- Main frame display -->
	<div class="frame-display">
		<img
			src={framePath}
			alt="{exercise} - frame {activeFrame}"
			class="frame-img"
		/>
	</div>

	<!-- Navigation controls -->
	{#if availableFrames.length > 1}
		<div class="controls">
			<button class="nav-btn" onclick={prevFrame} aria-label="Previous frame">
				<svg viewBox="0 0 24 24" fill="currentColor">
					<path d="M15 18l-6-6 6-6v12z"/>
				</svg>
			</button>

			<div class="frame-dots">
				{#each availableFrames as frame}
					<button
						class="dot"
						class:active={frame === activeFrame}
						onclick={() => selectFrame(frame)}
						aria-label="Frame {frame}"
					/>
				{/each}
			</div>

			<button class="nav-btn" onclick={nextFrame} aria-label="Next frame">
				<svg viewBox="0 0 24 24" fill="currentColor">
					<path d="M9 6l6 6-6 6V6z"/>
				</svg>
			</button>
		</div>

		<!-- Frame labels -->
		<div class="frame-label">
			{#if activeFrame === 1}
				<span>Начальная позиция</span>
			{:else if activeFrame === availableFrames.length}
				<span>Конечная позиция</span>
			{:else}
				<span>Фаза {activeFrame}</span>
			{/if}
		</div>
	{/if}
</div>

<style>
	.frame-viewer {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		width: 100%;
	}

	.frame-display {
		display: flex;
		justify-content: center;
		align-items: center;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		padding: var(--spacing-md);
		min-height: 200px;
	}

	.frame-img {
		max-width: 100%;
		height: auto;
		image-rendering: pixelated;
		image-rendering: crisp-edges;
	}

	.controls {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-md);
	}

	.nav-btn {
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		cursor: pointer;
		color: var(--text-primary);
		transition: all var(--transition-fast);
	}

	.nav-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--pixel-accent);
	}

	.nav-btn:active {
		transform: scale(0.95);
	}

	.nav-btn svg {
		width: 20px;
		height: 20px;
	}

	.frame-dots {
		display: flex;
		gap: var(--spacing-sm);
	}

	.dot {
		width: 12px;
		height: 12px;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		cursor: pointer;
		padding: 0;
		transition: all var(--transition-fast);
	}

	.dot:hover {
		border-color: var(--pixel-accent);
	}

	.dot.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
	}

	.frame-label {
		text-align: center;
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}
</style>
