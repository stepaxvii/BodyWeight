<script lang="ts">
	import { base } from '$app/paths';
	import type { AvatarId } from '$lib/types';

	interface Props {
		avatarId: AvatarId;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		showBorder?: boolean;
		borderColor?: string;
	}

	let {
		avatarId,
		size = 'md',
		showBorder = true,
		borderColor = 'var(--border-color)'
	}: Props = $props();

	const sizeMap = {
		sm: 24,
		md: 32,
		lg: 48,
		xl: 64
	};

	const pixelSize = $derived(sizeMap[size]);
	const avatarPath = $derived(`${base}/sprites/avatars/${avatarId}.svg`);
</script>

<div
	class="pixel-avatar"
	class:bordered={showBorder}
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
		border: 2px solid var(--border-color);
		box-shadow: 2px 2px 0px var(--pixel-black);
	}

	.pixel-avatar img {
		width: 100%;
		height: 100%;
		image-rendering: pixelated;
		image-rendering: crisp-edges;
		display: block;
	}
</style>
