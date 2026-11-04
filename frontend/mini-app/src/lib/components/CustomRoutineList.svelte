<script lang="ts">
	import { PixelIcon, PixelTabs, EmptyState } from '$lib/components/ui';
	import { t } from '$lib/i18n/index.svelte';
	import type { CustomRoutineListItem } from '$lib/types';

	interface Props {
		routines: CustomRoutineListItem[];
		onplay: (routineId: number) => void;
		onedit: (routineId: number) => void;
		ondelete: (routineId: number, routineName: string) => void;
	}

	let { routines, onplay, onedit, ondelete }: Props = $props();

	type RoutineCategory = 'workout' | 'morning' | 'stretch' | 'other';
	let activeCategory = $state<RoutineCategory>('workout');

	const categoryTabs = $derived([
		{ id: 'workout' as const, label: t('routines.list.typeWorkout') },
		{ id: 'morning' as const, label: t('routines.list.typeMorning') },
		{ id: 'stretch' as const, label: t('routines.list.typeStretch') },
		{ id: 'other' as const, label: t('routines.list.typeOther') }
	]);

	const filteredRoutines = $derived(
		routines.filter(r => {
			const type = r.routine_type || 'workout';
			if (activeCategory === 'other') {
				return type !== 'workout' && type !== 'morning' && type !== 'stretch';
			}
			return type === activeCategory;
		})
	);
</script>

<div class="routine-list">
	{#if routines.length === 0}
		<EmptyState icon="dumbbell" message={t('routines.list.empty')} />
	{:else}
		<PixelTabs tabs={categoryTabs} activeTab={activeCategory} onTabChange={(id) => activeCategory = id} />

		<div class="cust-rows">
			{#each filteredRoutines as routine (routine.id)}
				<div class="item cust-item">
					<span class="item__edge"></span>
					<span class="slot slot--md">
						<PixelIcon name="dumbbell" size="md" color="var(--accent)" />
					</span>
					<div class="item__body">
						<span class="item__name" title={routine.name}>{routine.name}</span>
						<div class="item__sub">
							<span class="item__tag">
								<PixelIcon name="timer" size="sm" color="var(--muted)" />
								{t('routines.list.durationMin', { minutes: routine.duration_minutes })}
							</span>
							<span class="item__tag">
								<PixelIcon name="dumbbell" size="sm" color="var(--muted)" />
								{t('routines.list.exercisesCount', { count: routine.exercises_count })}
							</span>
						</div>
					</div>
					<div class="cust-actions">
						<button
							class="cust-act cust-act--play"
							onclick={() => onplay(routine.id)}
							aria-label={t('routines.list.start')}
							title={t('routines.list.start')}
						>
							<PixelIcon name="play" size="sm" color="var(--on-accent)" />
						</button>
						<button
							class="cust-act"
							onclick={() => onedit(routine.id)}
							aria-label={t('routines.list.edit')}
							title={t('routines.list.edit')}
						>
							<PixelIcon name="edit" size="sm" color="var(--muted)" />
						</button>
						<button
							class="cust-act cust-act--del"
							onclick={() => ondelete(routine.id, routine.name)}
							aria-label={t('routines.list.delete')}
							title={t('routines.list.delete')}
						>
							<PixelIcon name="trash" size="sm" color="var(--danger)" />
						</button>
					</div>
				</div>
			{:else}
				<EmptyState icon="dumbbell" message={t('routines.list.emptyCategory')} />
			{/each}
		</div>
	{/if}
</div>

<style>
	.routine-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.cust-rows {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	/* compact, non-clickable-as-a-whole override of the global .item kit */
	.cust-item {
		cursor: default;
		gap: 10px;
		padding: 9px 11px;
	}
	.cust-item:active {
		transform: none;
		box-shadow: var(--shadow);
	}

	.cust-actions {
		flex: 0 0 auto;
		display: flex;
		gap: 5px;
	}

	.cust-act {
		width: 32px;
		height: 32px;
		display: grid;
		place-items: center;
		background: var(--bg3);
		border: 2px solid var(--line);
		cursor: pointer;
	}
	.cust-act:active {
		transform: translate(1px, 1px);
	}
	.cust-act--play {
		background: var(--green);
		border-color: var(--line);
	}
	.cust-act--del {
		border-color: var(--danger);
	}
</style>
