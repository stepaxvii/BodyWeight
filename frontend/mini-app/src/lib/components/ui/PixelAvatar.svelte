<script lang="ts">
	import { base } from '$app/paths';
	import type { AvatarId } from '$lib/types';

	interface Props {
		avatarId: AvatarId;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		showBorder?: boolean;
		borderColor?: string;
		idle?: boolean; // gentle idle motion (off under prefers-reduced-motion)
		ring?: boolean; // pulsing gold ring for premium avatars
	}

	let {
		avatarId,
		size = 'md',
		showBorder = true,
		borderColor = 'var(--border-color)',
		idle = true,
		ring = false
	}: Props = $props();

	const sizeMap = {
		sm: 24,
		md: 32,
		lg: 48,
		xl: 64
	};

	// Pick an idle variant deterministically from the id so a grid of avatars
	// "breathes" out of sync rather than in lockstep.
	const IDLE_VARIANTS = ['idle-bob', 'idle-breathe', 'idle-sway', 'idle-hop'];
	const pixelSize = $derived(sizeMap[size]);
	const avatarPath = $derived(`${base}/sprites/avatars/${avatarId}.svg`);
	const idleClass = $derived(
		idle
			? IDLE_VARIANTS[
					[...avatarId].reduce((sum, ch) => sum + ch.charCodeAt(0), 0) % IDLE_VARIANTS.length
				]
			: ''
	);
</script>

<div
	class="pixel-avatar {idleClass}"
	class:bordered={showBorder}
	class:anim-ring={ring}
	style="
		--size: {pixelSize}px;
		--border-color: {borderColor};
	"
>
	<img
		src={avatarPath}
		alt="Avatar"
		width={pixelSize}
		height={pixelSize}
	/>
</div>

<style>
	.pixel-avatar {
		width: var(--size);
		height: var(--size);
		overflow: hidden;
		flex-shrink: 0;
	}

	.pixel-avatar.bordered {
		border: var(--border-width) solid var(--border-color);
		box-shadow: var(--shadow-sm);
	}

	.pixel-avatar img {
		width: 100%;
		height: 100%;
		image-rendering: pixelated;
		image-rendering: crisp-edges;
		display: block;
	}
</style>
