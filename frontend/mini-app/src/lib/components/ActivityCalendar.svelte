<script lang="ts">
	import type { DayActivity } from '$lib/types';
	import { telegram } from '$lib/stores/telegram.svelte';

	interface Props {
		activityData: Record<string, DayActivity>;
		year: number;
		onDayClick?: (date: string, activity: DayActivity | null) => void;
		weeks?: number;
	}

	// Matches the designer's Heatmap: a compact, full-width grid of `weeks`
	// Monday-started weeks (default 26), responsive square cells, no labels.
	let { activityData, year, onDayClick, weeks = 26 }: Props = $props();

	const DEFAULT_NORM = 1400;

	// Intensity 0..4 by the day's XP relative to its norm (norm / 4 steps).
	function levelFor(xp: number, norm: number): number {
		if (xp <= 0) return 0;
		const step = Math.max(1, norm || DEFAULT_NORM) / 4;
		if (xp <= step) return 1;
		if (xp <= step * 2) return 2;
		if (xp <= step * 3) return 3;
		return 4;
	}

	function fmt(date: Date): string {
		// Local calendar day (not toISOString/UTC, which shifts the day in UTC+ zones).
		const y = date.getFullYear();
		const m = String(date.getMonth() + 1).padStart(2, '0');
		const d = String(date.getDate()).padStart(2, '0');
		return `${y}-${m}-${d}`;
	}

	function startOfDay(d: Date): Date {
		const x = new Date(d);
		x.setHours(0, 0, 0, 0);
		return x;
	}

	const today = startOfDay(new Date());

	// Build `weeks` columns (each Mon→Sun, top→bottom) ending with the current week.
	const columns = $derived.by(() => {
		const dow = today.getDay() === 0 ? 7 : today.getDay(); // Mon=1..Sun=7
		const sundayThisWeek = new Date(today);
		sundayThisWeek.setDate(today.getDate() + (7 - dow));
		const firstMonday = new Date(sundayThisWeek);
		firstMonday.setDate(sundayThisWeek.getDate() - (weeks * 7 - 1));

		const cols: Date[][] = [];
		const cur = new Date(firstMonday);
		for (let w = 0; w < weeks; w++) {
			const col: Date[] = [];
			for (let d = 0; d < 7; d++) {
				col.push(new Date(cur));
				cur.setDate(cur.getDate() + 1);
			}
			cols.push(col);
		}
		return cols;
	});

	function handleClick(date: Date) {
		if (!onDayClick) return;
		telegram.hapticImpact('light');
		const ds = fmt(date);
		onDayClick(ds, activityData[ds] || null);
	}
</script>

<section class="activity">
	<div class="sec-head">
		<span class="sec-head__t">Активность</span>
		<span class="sec-head__m">{year}</span>
	</div>

	<div class="heatmap">
		{#each columns as col}
			<div class="hm-col">
				{#each col as day}
					{@const ds = fmt(day)}
					{@const act = activityData[ds]}
					{@const xp = act?.total_xp || 0}
					{@const norm = act?.norm || DEFAULT_NORM}
					{#if day.getTime() > today.getTime()}
						<span class="hm-cell" data-lvl="0"></span>
					{:else}
						<button
							class="hm-cell"
							data-lvl={levelFor(xp, norm)}
							title="{ds}: {xp}/{norm} XP, {act?.workouts || 0} тренировок"
							onclick={() => handleClick(day)}
						></button>
					{/if}
				{/each}
			</div>
		{/each}
	</div>

	<div class="activity__legend">
		<span>меньше</span>
		<span class="hm-cell" data-lvl="0"></span>
		<span class="hm-cell" data-lvl="1"></span>
		<span class="hm-cell" data-lvl="2"></span>
		<span class="hm-cell" data-lvl="3"></span>
		<span class="hm-cell" data-lvl="4"></span>
		<span>больше</span>
	</div>
</section>

<style>
	/* Ported 1:1 from the designer's styles.css (.activity / .heatmap / .hm-*). */
	.activity {
		background: var(--card-bg);
		border: var(--bw) solid var(--line);
		border-radius: var(--radius);
		box-shadow: var(--shadow);
		padding: 13px;
	}

	.sec-head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
	}

	.sec-head__t {
		font-family: var(--font-display);
		font-size: var(--font-size-md);
		letter-spacing: 0.5px;
		text-transform: uppercase;
		color: var(--text);
	}

	.sec-head__m {
		font-family: var(--font-data);
		font-size: var(--data-md);
		color: var(--accent);
	}

	.heatmap {
		display: flex;
		gap: 3px;
		margin: 11px 0 9px;
		justify-content: space-between;
	}

	.hm-col {
		display: flex;
		flex-direction: column;
		gap: 3px;
		flex: 1;
		min-width: 0;
	}

	.hm-cell {
		display: block;
		width: 100%;
		aspect-ratio: 1;
		border: none;
		padding: 0;
		border-radius: var(--cell-radius, 0);
		background: var(--hm0);
	}

	button.hm-cell {
		cursor: pointer;
	}

	button.hm-cell:hover {
		outline: 2px solid var(--accent);
		outline-offset: -1px;
	}

	.hm-cell[data-lvl='1'] { background: var(--hm1); }
	.hm-cell[data-lvl='2'] { background: var(--hm2); }
	.hm-cell[data-lvl='3'] { background: var(--hm3); }
	.hm-cell[data-lvl='4'] { background: var(--hm4); }

	.activity__legend {
		display: flex;
		align-items: center;
		gap: 4px;
		justify-content: flex-end;
		font-size: var(--font-size-xs);
		color: var(--muted);
	}

	.activity__legend .hm-cell {
		width: 10px;
		height: 10px;
		flex: 0 0 auto;
		aspect-ratio: auto;
	}
</style>
