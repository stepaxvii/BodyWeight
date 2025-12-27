<script lang="ts">
	interface Props {
		value: number;
		max?: number;
		variant?: 'hp' | 'xp' | 'default';
		showLabel?: boolean;
		size?: 'sm' | 'md' | 'lg';
		animated?: boolean;
	}

	let {
		value,
		max = 100,
		variant = 'default',
		showLabel = false,
		size = 'md',
		animated = false
	}: Props = $props();

	const percentage = $derived(Math.min(100, Math.max(0, (value / max) * 100)));

	// HP-bar color changes based on percentage
	const hpColor = $derived(() => {
		if (variant !== 'hp') return '';
		if (percentage > 60) return 'green';
		if (percentage > 30) return 'yellow';
		return 'red';
	});
</script>

<div class="pixel-progress {variant} {size}" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
	<div class="track">
		<div
			class="bar {variant === 'hp' ? hpColor() : ''}"
			class:animated
			style="width: {percentage}%"
		>
			{#if variant === 'hp'}
				<!-- HP bar segments -->
				<div class="segments">
					{#each Array(10) as _, i}
						<div class="segment" class:filled={percentage > i * 10}></div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
	{#if showLabel}
		<div class="label">
			<span class="current">{value}</span>
			<span class="separator">/</span>
			<span class="max">{max}</span>
		</div>
	{/if}
</div>

<style>
	.pixel-progress {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
		width: 100%;
	}

	.track {
		width: 100%;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		overflow: hidden;
	}

	/* Sizes */
	.pixel-progress.sm .track { height: 8px; }
	.pixel-progress.md .track { height: 12px; }
	.pixel-progress.lg .track { height: 16px; }

	.bar {
		height: 100%;
		background: var(--pixel-accent);
		transition: width 0.3s ease-out;
		position: relative;
	}

	.bar.animated {
		animation: progress-pulse 2s ease-in-out infinite;
	}

	/* XP variant - blue/purple gradient feel */
	.pixel-progress.xp .bar {
		background: var(--pixel-blue);
	}

	/* HP variant - color changes based on health */
	.pixel-progress.hp .bar {
		background: var(--pixel-green);
	}

	.pixel-progress.hp .bar.yellow {
		background: var(--pixel-yellow);
	}

	.pixel-progress.hp .bar.red {
		background: var(--pixel-red);
		animation: low-hp 0.5s ease-in-out infinite;
	}

	/* HP segments overlay */
	.segments {
		display: flex;
		height: 100%;
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
	}

	.segment {
		flex: 1;
		border-right: 1px solid rgba(0, 0, 0, 0.3);
	}

	.segment:last-child {
		border-right: none;
	}

	/* Label */
	.label {
		display: flex;
		justify-content: flex-end;
		font-size: var(--font-size-xs);
		font-family: var(--font-pixel);
	}

	.current {
		color: var(--text-primary);
	}

	.separator {
		color: var(--text-muted);
		margin: 0 2px;
	}

	.max {
		color: var(--text-secondary);
	}

	@keyframes progress-pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.8; }
	}

	@keyframes low-hp {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}
</style>
