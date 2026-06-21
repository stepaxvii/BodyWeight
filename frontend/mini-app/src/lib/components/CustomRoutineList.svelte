<script lang="ts">
	import { PixelButton, PixelIcon, PixelTabs, EmptyState } from '$lib/components/ui';
	import type { CustomRoutineListItem } from '$lib/types';

	interface Props {
		routines: CustomRoutineListItem[];
		onplay: (routineId: number) => void;
		onedit: (routineId: number) => void;
		ondelete: (routineId: number, routineName: string) => void;
		oncreate: () => void;
	}

	let { routines, onplay, onedit, ondelete, oncreate }: Props = $props();

	type RoutineCategory = 'workout' | 'morning' | 'stretch' | 'other';
	let activeCategory = $state<RoutineCategory>('workout');

	const categoryTabs = [
		{ id: 'workout' as const, label: 'Тренировка' },
		{ id: 'morning' as const, label: 'Зарядка' },
		{ id: 'stretch' as const, label: 'Растяжка' },
		{ id: 'other' as const, label: 'Другое' }
	];

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
		<EmptyState icon="dumbbell" message="У вас пока нет своих сетов">
			<PixelButton variant="primary" onclick={oncreate}>
				<PixelIcon name="plus" />
				Создать сет
			</PixelButton>
		</EmptyState>
	{:else}
		<div class="create-btn-wrapper">
			<PixelButton variant="secondary" fullWidth onclick={oncreate}>
				<PixelIcon name="plus" />
				Создать сет
			</PixelButton>
		</div>

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
								{routine.duration_minutes}м
							</span>
							<span class="item__tag">
								<PixelIcon name="dumbbell" size="sm" color="var(--muted)" />
								{routine.exercises_count} упр.
							</span>
						</div>
					</div>
					<div class="cust-actions">
						<button
							class="cust-act cust-act--play"
							onclick={() => onplay(routine.id)}
							aria-label="Начать"
							title="Начать"
						>
							<PixelIcon name="play" size="sm" color="var(--on-accent)" />
						</button>
						<button
							class="cust-act"
							onclick={() => onedit(routine.id)}
							aria-label="Редактировать"
							title="Редактировать"
						>
							<PixelIcon name="edit" size="sm" color="var(--muted)" />
						</button>
						<button
							class="cust-act cust-act--del"
							onclick={() => ondelete(routine.id, routine.name)}
							aria-label="Удалить"
							title="Удалить"
						>
							<PixelIcon name="trash" size="sm" color="var(--danger)" />
						</button>
					</div>
				</div>
			{:else}
				<EmptyState icon="dumbbell" message="Нет сетов в этой категории" />
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

	.create-btn-wrapper {
		margin-bottom: var(--spacing-xs);
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
