<script lang="ts">
	import type { DayActivity } from '$lib/types';
	import { telegram } from '$lib/stores/telegram.svelte';

	interface Props {
		activityData: Record<string, DayActivity>;
		year: number;
		onDayClick?: (date: string, activity: DayActivity | null) => void;
	}

	let { activityData, year, onDayClick }: Props = $props();

	// Color thresholds based on XP (excluding achievement XP)
	const XP_THRESHOLDS = {
		LIGHT: 1,      // 1-100 XP: light green
		MEDIUM: 101,   // 101-300 XP: green
		INTENSE: 301,  // 301-500 XP: bright green
		VERY_INTENSE: 501 // 500+ XP: red/dark green
	};

	function getColorClass(xp: number): string {
		if (xp === 0) return 'color-empty';
		if (xp < XP_THRESHOLDS.MEDIUM) return 'color-light';
		if (xp < XP_THRESHOLDS.INTENSE) return 'color-medium';
		if (xp < XP_THRESHOLDS.VERY_INTENSE) return 'color-intense';
		return 'color-very-intense';
	}

	// Generate all days for the year
	function generateYearGrid(year: number): Date[] {
		const days: Date[] = [];
		const start = new Date(year, 0, 1); // January 1st
		const end = new Date(year, 11, 31); // December 31st

		for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
			days.push(new Date(d));
		}
		return days;
	}

	// Group days by week (starting Monday)
	function groupByWeeks(days: Date[]): Date[][] {
		const weeks: Date[][] = [];
		let currentWeek: Date[] = [];

		// Fill first week with empty slots if it doesn't start on Monday
		const firstDay = days[0];
		let firstDayOfWeek = firstDay.getDay(); // 0 = Sunday, 1 = Monday, etc.
		// Convert Sunday (0) to 7 for easier Monday-based calculation
		if (firstDayOfWeek === 0) firstDayOfWeek = 7;
		const daysToFill = firstDayOfWeek - 1; // Monday = 1, so Monday needs 0 empty slots

		for (let i = 0; i < daysToFill; i++) {
			currentWeek.push(null as any); // Empty slot
		}

		for (const day of days) {
			currentWeek.push(day);

			// Check if week is complete (7 days total)
			if (currentWeek.length === 7) {
				weeks.push([...currentWeek]);
				currentWeek = [];
			}
		}

		// Fill last week with empty slots if needed
		if (currentWeek.length > 0) {
			while (currentWeek.length < 7) {
				currentWeek.push(null as any);
			}
			weeks.push(currentWeek);
		}

		return weeks;
	}

	const yearDays = $derived(generateYearGrid(year));
	const weeks = $derived(groupByWeeks(yearDays));

	function formatDate(date: Date): string {
		return date.toISOString().split('T')[0];
	}

	function handleDayClick(date: Date | null) {
		if (!date || !onDayClick) return;

		telegram.hapticImpact('light');
		const dateStr = formatDate(date);
		const activity = activityData[dateStr] || null;
		onDayClick(dateStr, activity);
	}

	// Month labels
	const monthNames = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];

	// Get month label positions (first week of each month)
	function getMonthLabels(): Array<{ month: string; weekIndex: number }> {
		const labels: Array<{ month: string; weekIndex: number }> = [];
		let lastMonth = -1;

		weeks.forEach((week, weekIndex) => {
			const firstDayInWeek = week.find(d => d !== null);
			if (firstDayInWeek) {
				const month = firstDayInWeek.getMonth();
				if (month !== lastMonth) {
					labels.push({ month: monthNames[month], weekIndex });
					lastMonth = month;
				}
			}
		});

		return labels;
	}

	const monthLabels = $derived(getMonthLabels());

	// Weekday labels (showing only Mon, Wed, Fri)
	const weekdayLabels = ['Пн', '', 'Ср', '', 'Пт', '', ''];
</script>

<div class="activity-calendar">
	<div class="calendar-header">
		<h3 class="calendar-title">Активность в {year}</h3>
		<div class="calendar-legend">
			<span class="legend-label">Меньше</span>
			<div class="legend-box color-empty"></div>
			<div class="legend-box color-light"></div>
			<div class="legend-box color-medium"></div>
			<div class="legend-box color-intense"></div>
			<div class="legend-box color-very-intense"></div>
			<span class="legend-label">Больше</span>
		</div>
	</div>

	<div class="calendar-grid-wrapper">
		<!-- Month labels -->
		<div class="month-labels">
			{#each monthLabels as { month, weekIndex }}
				<span class="month-label" style="left: {weekIndex * 12}px">{month}</span>
			{/each}
		</div>

		<!-- Calendar grid -->
		<div class="calendar-grid">
			{#each weeks as week}
				<div class="calendar-column">
					{#each week as day}
						{#if day === null}
							<div class="calendar-day empty"></div>
						{:else}
							{@const dateStr = formatDate(day)}
							{@const activity = activityData[dateStr]}
							{@const xp = activity?.total_xp || 0}
							<button
								class="calendar-day {getColorClass(xp)}"
								title="{dateStr}: {xp} XP, {activity?.workouts || 0} тренировок"
								onclick={() => handleDayClick(day)}
							></button>
						{/if}
					{/each}
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.activity-calendar {
		width: 100%;
		padding: var(--spacing-md);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
	}

	.calendar-header {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-md);
	}

	.calendar-title {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin: 0;
	}

	.calendar-legend {
		display: flex;
		align-items: center;
		gap: 3px;
		font-size: var(--font-size-xs);
	}

	.legend-label {
		color: var(--text-secondary);
		margin: 0 4px;
	}

	.legend-box {
		width: 10px;
		height: 10px;
		border: 1px solid var(--border-color);
	}

	.calendar-grid-wrapper {
		position: relative;
		overflow: hidden;
	}

	.month-labels {
		position: relative;
		height: 14px;
		margin-bottom: 2px;
		min-width: fit-content;
	}

	.month-label {
		position: absolute;
		font-size: 9px;
		color: var(--text-secondary);
		text-transform: uppercase;
		white-space: nowrap;
	}

	.calendar-grid {
		display: flex;
		gap: 2px;
		min-width: fit-content;
		padding-bottom: var(--spacing-xs);
	}

	.calendar-column {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.calendar-day {
		width: 10px;
		height: 10px;
		border: 1px solid var(--border-color);
		cursor: pointer;
		padding: 0;
		transition: all 0.1s;
	}

	.calendar-day:not(.empty):hover {
		transform: scale(1.3);
		box-shadow: 0 0 0 2px var(--pixel-accent);
		z-index: 1;
	}

	.calendar-day.empty {
		background: transparent;
		border-color: transparent;
		cursor: default;
	}

	/* Color scheme based on XP */
	.color-empty {
		background: var(--pixel-bg-dark);
	}

	.color-light {
		background: #0e4429; /* Dark green - light workout */
	}

	.color-medium {
		background: #006d32; /* Green - medium workout */
	}

	.color-intense {
		background: #26a641; /* Bright green - intense workout */
	}

	.color-very-intense {
		background: #39d353; /* Very bright green - very intense workout */
	}

	/* Scrollbar styling */
	.calendar-grid::-webkit-scrollbar {
		height: 6px;
	}

	.calendar-grid::-webkit-scrollbar-track {
		background: var(--pixel-bg-dark);
	}

	.calendar-grid::-webkit-scrollbar-thumb {
		background: var(--border-color);
	}

	.calendar-grid::-webkit-scrollbar-thumb:hover {
		background: var(--pixel-accent);
	}
</style>
