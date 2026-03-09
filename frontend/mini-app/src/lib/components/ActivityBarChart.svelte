<script lang="ts">
	import type { DayActivity } from '$lib/types';

	interface Props {
		activityData: Record<string, DayActivity>;
		range: 'week' | '2weeks' | 'month';
		metric?: 'xp' | 'workouts';
	}

	let { activityData, range, metric = 'xp' }: Props = $props();

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
			const value = metric === 'xp' ? (day?.total_xp ?? 0) : (day?.workouts ?? 0);
			return { date, value, isToday: date === todayStr };
		})
	);

	const maxValue = $derived(
		chartData.length ? Math.max(...chartData.map((d) => d.value), 1) : 1
	);

	const totalValue = $derived(chartData.reduce((sum, d) => sum + d.value, 0));
	const activeDays = $derived(chartData.filter((d) => d.value > 0).length);

	// Y-axis grid lines (3 lines: 25%, 50%, 75%)
	const gridLines = $derived([
		{ percent: 75, value: Math.round(maxValue * 0.75) },
		{ percent: 50, value: Math.round(maxValue * 0.5) },
		{ percent: 25, value: Math.round(maxValue * 0.25) },
	]);

	// Bar opacity based on value relative to max (0.3 – 1.0)
	function barOpacity(value: number): number {
		if (value === 0) return 0;
		return 0.35 + (value / maxValue) * 0.65;
	}

	let selectedIndex = $state<number | null>(null);

	function handleBarClick(index: number) {
		selectedIndex = selectedIndex === index ? null : index;
	}

	function formatDayLabel(dateStr: string): string {
		const d = new Date(dateStr + 'T12:00:00');
		if (range === 'month') {
			return `${d.getDate()}`;
		}
		const days = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
		if (range === '2weeks') {
			return `${d.getDate()}`;
		}
		return days[d.getDay()];
	}

	const metricLabel = $derived(metric === 'xp' ? 'XP' : 'тренировок');
	const metricUnit = $derived(metric === 'xp' ? 'XP' : '');
</script>

<div class="activity-bar-chart">
	<!-- Summary -->
	<div class="chart-summary">
		<div class="summary-item">
			<span class="summary-value">{totalValue}</span>
			<span class="summary-label">{metricLabel}</span>
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

	<!-- Selected bar tooltip -->
	{#if selectedIndex !== null}
		{@const item = chartData[selectedIndex]}
		<div class="tooltip">
			<span class="tooltip-date">
				{new Date(item.date + 'T12:00:00').toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', weekday: 'short' })}
			</span>
			<span class="tooltip-value">{item.value} {metricUnit}</span>
		</div>
	{/if}

	<!-- Chart area -->
	<div class="chart-area">
		<!-- Y-axis labels -->
		<div class="y-axis">
			<span class="y-label">{maxValue}</span>
			{#each gridLines as line}
				<span class="y-label" style="bottom: {line.percent}%">{line.value}</span>
			{/each}
			<span class="y-label y-zero">0</span>
		</div>

		<!-- Bars -->
		<div class="chart-bars">
			<!-- Grid lines -->
			{#each gridLines as line}
				<div class="grid-line" style="bottom: {line.percent}%"></div>
			{/each}

			{#each chartData as { date, value, isToday }, i}
				<button
					class="bar-wrapper"
					class:is-today={isToday}
					class:selected={selectedIndex === i}
					onclick={() => handleBarClick(i)}
					type="button"
				>
					{#if value > 0 && range === 'week'}
						<span class="bar-value">{value}</span>
					{/if}
					<div
						class="bar"
						class:empty={value === 0}
						style="height: {value > 0 ? Math.max((value / maxValue) * 100, 3) : 0}%; opacity: {barOpacity(value)}"
					></div>
					{#if value === 0}
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

	/* Tooltip */
	.tooltip {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: var(--spacing-sm);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		min-height: 20px;
	}

	.tooltip-value {
		color: var(--pixel-accent);
		font-weight: bold;
	}

	/* Chart area */
	.chart-area {
		display: flex;
		gap: var(--spacing-xs);
		height: 120px;
	}

	/* Y-axis */
	.y-axis {
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		position: relative;
		width: 28px;
		flex-shrink: 0;
		padding-bottom: 22px; /* space for bar labels */
	}

	.y-label {
		font-size: 8px;
		color: var(--text-muted);
		text-align: right;
		line-height: 1;
	}

	.y-zero {
		margin-top: auto;
	}

	/* Bars container */
	.chart-bars {
		flex: 1;
		display: flex;
		align-items: flex-end;
		gap: 2px;
		position: relative;
		padding-bottom: 22px; /* space for labels */
	}

	/* Grid lines */
	.grid-line {
		position: absolute;
		left: 0;
		right: 0;
		height: 1px;
		background: var(--border-color);
		opacity: 0.3;
		pointer-events: none;
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

	.bar-wrapper.selected .bar {
		opacity: 1 !important;
		box-shadow: 0 0 6px var(--pixel-accent);
	}

	/* Bar */
	.bar {
		width: 100%;
		background: var(--pixel-accent);
		transition: height 0.3s ease, opacity 0.3s ease;
	}

	.bar.empty {
		display: none;
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
		background: var(--pixel-green);
	}
</style>
