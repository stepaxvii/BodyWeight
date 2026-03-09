<script lang="ts">
	import type { DayActivity } from '$lib/types';

	interface Props {
		activityData: Record<string, DayActivity>;
		range: 'week' | '2weeks' | 'month';
		metric?: 'xp' | 'workouts';
	}

	let { activityData, range, metric = 'xp' }: Props = $props();

	const dayCount = $derived(range === 'week' ? 7 : range === '2weeks' ? 14 : 30);

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
			return { date, value, label: formatDayLabel(date) };
		})
	);

	const maxValue = $derived(
		chartData.length ? Math.max(...chartData.map((d) => d.value), 1) : 1
	);

	function formatDayLabel(dateStr: string): string {
		const d = new Date(dateStr + 'T12:00:00');
		const today = new Date();
		const isToday =
			d.getDate() === today.getDate() &&
			d.getMonth() === today.getMonth() &&
			d.getFullYear() === today.getFullYear();
		if (isToday) return 'Сегодня';
		const days = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
		return `${days[d.getDay()]} ${d.getDate()}`;
	}

	const metricLabel = $derived(metric === 'xp' ? 'XP' : 'Тренировок');
</script>

<div class="activity-bar-chart">
	<div class="chart-bars">
		{#each chartData as { date, value, label }}
			<div class="bar-wrapper" title="{date}: {value} {metricLabel}">
				<div
					class="bar"
					style="height: {maxValue > 0 ? (value / maxValue) * 100 : 0}%"
				></div>
				<span class="bar-label">{label}</span>
			</div>
		{/each}
	</div>
	<span class="chart-metric-label">{metricLabel}</span>
</div>

<style>
	.activity-bar-chart {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
		min-height: 140px;
	}

	.chart-bars {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 4px;
		height: 100px;
		padding: 0 var(--spacing-xs);
	}

	.bar-wrapper {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		min-width: 0;
	}

	.bar {
		width: 100%;
		min-height: 2px;
		background: var(--pixel-accent);
		border-radius: 2px 2px 0 0;
		transition: height 0.2s;
	}

	.bar-wrapper:hover .bar {
		background: var(--pixel-green);
	}

	.bar-label {
		font-size: 9px;
		color: var(--text-secondary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 100%;
		text-align: center;
	}

	.chart-metric-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-align: center;
	}
</style>
