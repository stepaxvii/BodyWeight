<script lang="ts">
	import type { DayActivity } from '$lib/types';

	interface Props {
		activityData: Record<string, DayActivity>;
		range: 'week' | '2weeks' | 'month' | '3months';
		onDayClick?: (date: string, activity: DayActivity | null) => void;
	}

	let { activityData, range, onDayClick }: Props = $props();

	const DEFAULT_NORM = 1400;

	const dayCount = $derived(
		range === 'week' ? 7 :
		range === '2weeks' ? 14 :
		range === 'month' ? 30 : 90
	);

	// Local calendar day (NOT toISOString/UTC, which shifts the day in UTC+ zones).
	function toDateStr(date: Date): string {
		const y = date.getFullYear();
		const m = String(date.getMonth() + 1).padStart(2, '0');
		const d = String(date.getDate()).padStart(2, '0');
		return `${y}-${m}-${d}`;
	}

	const todayStr = $derived(toDateStr(new Date()));

	// Даты за выбранный период (от старых к новым)
	const dates = $derived((() => {
		const list: string[] = [];
		const end = new Date();
		for (let i = dayCount - 1; i >= 0; i--) {
			const d = new Date(end);
			d.setDate(d.getDate() - i);
			list.push(toDateStr(d));
		}
		return list;
	})());

	const chartData = $derived(
		dates.map((date) => {
			const day = activityData[date];
			const value = day?.total_xp ?? 0;
			const norm = day?.norm ?? DEFAULT_NORM;
			return { date, value, norm, activity: day ?? null, isToday: date === todayStr };
		})
	);

	const maxValue = $derived(
		chartData.length ? Math.max(...chartData.map((d) => d.value), 1) : 1
	);

	const totalValue = $derived(chartData.reduce((sum, d) => sum + d.value, 0));
	const activeDays = $derived(chartData.filter((d) => d.value > 0).length);

	// 4 уровня заливки по доле дневной нормы — как в ActivityCalendar.
	function getBarColorClass(xp: number, norm: number): string {
		if (xp <= 0) return 'bar-empty';
		const step = Math.max(1, norm || DEFAULT_NORM) / 4;
		if (xp <= step) return 'bar-1';
		if (xp <= step * 2) return 'bar-2';
		if (xp <= step * 3) return 'bar-3';
		return 'bar-4';
	}

	function handleBarClick(date: string, activity: DayActivity | null) {
		onDayClick?.(date, activity);
	}
</script>

<div class="activity-bar-chart">
	<!-- Summary -->
	<div class="chart-summary">
		<div class="summary-item">
			<span class="summary-value">{totalValue}</span>
			<span class="summary-label">XP</span>
		</div>
		<div class="summary-divider"></div>
		<div class="summary-item">
			<span class="summary-value">{activeDays}</span>
			<span class="summary-label">дней</span>
		</div>
		<div class="summary-divider"></div>
		<div class="summary-item">
			<span class="summary-value">{activeDays > 0 ? Math.round(totalValue / activeDays) : 0}</span>
			<span class="summary-label">в среднем</span>
		</div>
	</div>

	<!-- Chart area -->
	<div class="chart-area">
		{#each chartData as { date, value, norm, activity, isToday }, i}
			<button
				class="bar-wrapper"
				class:is-today={isToday}
				onclick={() => handleBarClick(date, activity)}
				type="button"
			>
				{#if value > 0}
					<div
						class="bar {getBarColorClass(value, norm)}"
						style="height: {Math.max((value / maxValue) * 100, 4)}%"
					></div>
				{:else}
					<div class="bar-empty-dot"></div>
				{/if}
				{#if isToday}
					<div class="today-dot"></div>
				{/if}
			</button>
		{/each}
	</div>
</div>

<style>
	.activity-bar-chart {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	/* Summary row */
	.chart-summary {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-md);
	}

	.summary-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
	}

	.summary-value {
		font-size: var(--font-size-md);
		color: var(--text-primary);
	}

	.summary-label {
		font-size: 9px;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	.summary-divider {
		width: 1px;
		height: 24px;
		background: var(--border-color);
	}

	/* Chart area */
	.chart-area {
		display: flex;
		align-items: flex-end;
		gap: 2px;
		height: 120px;
	}

	/* Bar wrapper */
	.bar-wrapper {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		min-width: 0;
		height: 100%;
		justify-content: flex-end;
		position: relative;
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		-webkit-tap-highlight-color: transparent;
	}

	/* Bar — colors match ActivityCalendar */
	.bar {
		width: 100%;
		transition: height 0.3s ease;
	}

	.bar-1 {
		background: var(--hm1);
	}

	.bar-2 {
		background: var(--hm2);
	}

	.bar-3 {
		background: var(--hm3);
	}

	.bar-4 {
		background: var(--hm4);
	}

	.bar-empty-dot {
		width: 3px;
		height: 3px;
		background: var(--border-color);
		border-radius: 50%;
		flex-shrink: 0;
	}

	/* Today indicator */
	.today-dot {
		position: absolute;
		bottom: -4px;
		width: 4px;
		height: 4px;
		background: var(--pixel-accent);
		border-radius: 50%;
	}

	.bar-wrapper.is-today .bar {
		box-shadow: 0 0 4px rgba(57, 211, 83, 0.4);
	}
</style>
