<script lang="ts">
	import type { DayActivity } from '$lib/types';

	interface Props {
		activityData: Record<string, DayActivity>;
		range: 'week' | '2weeks' | 'month';
		onDayClick?: (date: string, activity: DayActivity | null) => void;
	}

	let { activityData, range, onDayClick }: Props = $props();

	const dayCount = $derived(range === 'week' ? 7 : range === '2weeks' ? 14 : 30);

	const todayStr = $derived(new Date().toISOString().split('T')[0]);

	// Даты за выбранный период (от старых к новым)
	const dates = $derived((() => {
		const list: string[] = [];
		const end = new Date();
		for (let i = dayCount - 1; i >= 0; i--) {
			const d = new Date(end);
			d.setDate(d.getDate() - i);
			list.push(d.toISOString().split('T')[0]);
		}
		return list;
	})());

	const chartData = $derived(
		dates.map((date) => {
			const day = activityData[date];
			const value = day?.total_xp ?? 0;
			return { date, value, activity: day ?? null, isToday: date === todayStr };
		})
	);

	const maxValue = $derived(
		chartData.length ? Math.max(...chartData.map((d) => d.value), 1) : 1
	);

	const totalValue = $derived(chartData.reduce((sum, d) => sum + d.value, 0));
	const activeDays = $derived(chartData.filter((d) => d.value > 0).length);

	// Color classes matching ActivityCalendar thresholds
	function getBarColorClass(xp: number): string {
		if (xp === 0) return 'bar-empty';
		if (xp <= 200) return 'bar-light';
		if (xp <= 400) return 'bar-medium';
		if (xp <= 600) return 'bar-intense';
		if (xp < 1000) return 'bar-strong';
		return 'bar-very-intense';
	}

	function handleBarClick(date: string, activity: DayActivity | null) {
		onDayClick?.(date, activity);
	}

	function formatDayLabel(dateStr: string): string {
		const d = new Date(dateStr + 'T12:00:00');
		if (range === 'month' || range === '2weeks') {
			return `${d.getDate()}`;
		}
		const days = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
		return days[d.getDay()];
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
		{#each chartData as { date, value, activity, isToday }, i}
			<button
				class="bar-wrapper"
				class:is-today={isToday}
				onclick={() => handleBarClick(date, activity)}
				type="button"
			>
				{#if value > 0 && range === 'week'}
					<span class="bar-value">{value}</span>
				{/if}
				{#if value > 0}
					<div
						class="bar {getBarColorClass(value)}"
						style="height: {Math.max((value / maxValue) * 100, 4)}%"
					></div>
				{:else}
					<div class="bar-empty-dot"></div>
				{/if}
				<span class="bar-label" class:today-label={isToday}>
					{#if isToday}
						·
					{:else}
						{formatDayLabel(date)}
					{/if}
				</span>
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
		padding-bottom: 22px; /* space for labels */
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

	.bar-light {
		background: #0e4429;
	}

	.bar-medium {
		background: #006d32;
	}

	.bar-intense {
		background: #1a7f37;
	}

	.bar-strong {
		background: #26a641;
	}

	.bar-very-intense {
		background: #39d353;
	}

	.bar-empty-dot {
		width: 3px;
		height: 3px;
		background: var(--border-color);
		border-radius: 50%;
		flex-shrink: 0;
	}

	/* Value above bar (week only) */
	.bar-value {
		font-size: 8px;
		color: var(--text-secondary);
		line-height: 1;
		white-space: nowrap;
	}

	/* Labels */
	.bar-label {
		font-size: 8px;
		color: var(--text-muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 100%;
		text-align: center;
		position: absolute;
		bottom: 0;
		line-height: 18px;
	}

	.today-label {
		font-size: 14px;
		color: var(--pixel-accent);
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
