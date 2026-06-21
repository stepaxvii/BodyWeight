<script lang="ts">
	// Difficulty pips (designer's <Diff/>): `n` filled of `max`. Ported 1:1 from
	// the designer app.css (.diff / .diff__d).
	interface Props {
		n: number;
		max?: number;
	}
	let { n, max = 5 }: Props = $props();
</script>

<span class="diff" title="Сложность {n}/{max}">
	{#each Array(max) as _, i}
		<span class="diff__d" class:on={i < n}></span>
	{/each}
</span>

<style>
	.diff {
		display: inline-flex;
		gap: 3px;
	}
	.diff__d {
		width: 7px;
		height: 7px;
		background: var(--line2);
	}
	.diff__d.on {
		background: var(--accent);
	}
</style>
