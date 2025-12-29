<script lang="ts">
	interface Props {
		name: string;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		color?: string;
	}

	let {
		name,
		size = 'md',
		color = 'currentColor'
	}: Props = $props();

	const sizeMap = {
		sm: 12,
		md: 16,
		lg: 24,
		xl: 32
	};

	const iconSize = $derived(sizeMap[size]);
</script>

<svg
	class="pixel-icon"
	width={iconSize}
	height={iconSize}
	viewBox="0 0 16 16"
	fill={color}
>
	{#if name === 'xp'}
		<path d="M2 4h12v2H2V4zm2 3h8v2H4V7zm2 3h4v2H6v-2z"/>
	{:else if name === 'coin'}
		<circle cx="8" cy="8" r="6" fill="none" stroke={color} stroke-width="2"/>
		<path d="M6 6h4v1H6V6zm0 3h4v1H6V9z"/>
	{:else if name === 'streak'}
		<path d="M8 1l2 4 4 1-3 3 1 4-4-2-4 2 1-4-3-3 4-1 2-4z"/>
	{:else if name === 'level'}
		<path d="M8 2L2 8l6 6 6-6-6-6zm0 3l3 3-3 3-3-3 3-3z"/>
	{:else if name === 'timer'}
		<circle cx="8" cy="8" r="6" fill="none" stroke={color} stroke-width="2"/>
		<path d="M8 4v4l3 2"/>
	{:else if name === 'reps'}
		<path d="M3 6h2v8H3V6zm4-2h2v10H7V4zm4 4h2v6h-2v-6z"/>
	{:else if name === 'check'}
		<path d="M3 8l3 3 7-7-2-2-5 5-1-1-2 2z"/>
	{:else if name === 'lock'}
		<path d="M5 7V5a3 3 0 016 0v2h1v7H4V7h1zm2-2v2h2V5a1 1 0 00-2 0z"/>
	{:else if name === 'star'}
		<path d="M8 1l2 4 4 1-3 3 1 4-4-2-4 2 1-4-3-3 4-1 2-4z"/>
	{:else if name === 'star-empty'}
		<path d="M8 1l2 4 4 1-3 3 1 4-4-2-4 2 1-4-3-3 4-1 2-4z" fill="none" stroke={color} stroke-width="1"/>
	{:else if name === 'friend'}
		<path d="M6 4a2 2 0 100 4 2 2 0 000-4zM3 10c0-1 1-2 3-2s3 1 3 2v1H3v-1zm7-5a2 2 0 110 4 2 2 0 010-4zm-1 7v-1c0-1-.5-1.5-1-2 .5-.5 2-.5 3 0s1.5 1 1.5 2v1h-3.5z"/>
	{:else if name === 'settings'}
		<path d="M6 2h4v2l1 1h2v4h-2l-1 1v2H6v-2l-1-1H3V5h2l1-1V2zm2 4a2 2 0 100 4 2 2 0 000-4z"/>
	{:else if name === 'back'}
		<path d="M10 3L5 8l5 5V3z"/>
	{:else if name === 'plus'}
		<path d="M7 3v4H3v2h4v4h2V9h4V7H9V3H7z"/>
	{:else if name === 'minus'}
		<path d="M3 7h10v2H3V7z"/>
	{:else if name === 'play'}
		<path d="M5 3v10l8-5-8-5z"/>
	{:else if name === 'pause'}
		<path d="M4 3h3v10H4V3zm5 0h3v10H9V3z"/>
	{:else if name === 'stop'}
		<path d="M3 3h10v10H3V3z"/>
	{:else if name === 'trophy'}
		<path d="M4 2h8v2h2v3c0 1-1 2-2 2h-1c0 2-1 3-3 3s-3-1-3-3H4c-1 0-2-1-2-2V4h2V2zm1 2v2h1c0 1 1 2 2 2s2-1 2-2h1V4H5zm1 8h4v2H6v-2z"/>
	{:else if name === 'arrow-up'}
		<path d="M8 3l5 6H3l5-6z"/>
	{:else if name === 'arrow-down'}
		<path d="M8 13l-5-6h10l-5 6z"/>
	{:else if name === 'heart'}
		<path d="M8 4C6 2 2 2 2 6s6 8 6 8 6-4 6-8-4-4-6-2z"/>
	{:else if name === 'heart-empty'}
		<path d="M8 4C6 2 2 2 2 6s6 8 6 8 6-4 6-8-4-4-6-2z" fill="none" stroke={color} stroke-width="1"/>
	{:else if name === 'friends'}
		<path d="M5 4a2 2 0 100 4 2 2 0 000-4zM2 10c0-1 1-2 3-2s3 1 3 2v1H2v-1zm9-6a2 2 0 110 4 2 2 0 010-4zm0 6c2 0 3 1 3 2v1H9v-1c0-1 1-2 2-2z"/>
	{:else if name === 'search'}
		<path d="M6 2a4 4 0 103 6.5l3.5 3.5 1.5-1.5L10.5 7A4 4 0 006 2zm0 2a2 2 0 110 4 2 2 0 010-4z"/>
	{:else if name === 'mail'}
		<path d="M2 4h12v8H2V4zm2 2l4 3 4-3v1l-4 3-4-3V6z"/>
	{:else if name === 'close'}
		<path d="M4 4l8 8M12 4l-8 8" fill="none" stroke={color} stroke-width="2"/>
	{:else if name === 'warning'}
		<path d="M8 1L1 14h14L8 1zm0 4v5h0V5zm0 7a1 1 0 110 2 1 1 0 010-2z"/>
	{:else if name === 'home'}
		<path d="M8 2L2 7v7h4V10h4v4h4V7L8 2z"/>
	{:else if name === 'pullup'}
		<path d="M2 3h12v2H2V3zm5 3h2v8H7V6zm-4 0h2v4H3v-4zm8 0h2v4h-2v-4z"/>
	{:else if name === 'dip'}
		<path d="M2 4h3v2H2V4zm9 0h3v2h-3V4zM7 2h2v12H7V2zm-4 8h3v2H3v-2zm8 0h3v2h-3v-2z"/>
	{:else if name === 'arrow-left'}
		<path d="M10 3L5 8l5 5V3z"/>
	{:else if name === 'arrow-right'}
		<path d="M6 3l5 5-5 5V3z"/>
	{:else if name === 'bell'}
		<path d="M8 2a1 1 0 011 1v1c2 .5 3 2 3 4v2l1 1v1H3v-1l1-1V8c0-2 1-3.5 3-4V3a1 1 0 011-1zm-1 12h2a1 1 0 01-2 0z"/>
	{:else}
		<!-- Default: question mark -->
		<path d="M6 4h4v1H8v2h2v2H8v2H6V9h2V7H6V4zm0 7h2v2H6v-2z"/>
	{/if}
</svg>

<style>
	.pixel-icon {
		image-rendering: pixelated;
		flex-shrink: 0;
	}
</style>
