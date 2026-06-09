<script lang="ts">
	import { PixelButton, PixelCard, PixelIcon, EmptyState } from '$lib/components/ui';
	import type { CustomRoutineListItem } from '$lib/types';

	interface Props {
		routines: CustomRoutineListItem[];
		onplay: (routineId: number) => void;
		onedit: (routineId: number) => void;
		ondelete: (routineId: number, routineName: string) => void;
		oncreate: () => void;
	}

	let { routines, onplay, onedit, ondelete, oncreate }: Props = $props();

	function getTypeLabel(type: string): string {
		switch (type) {
			case 'morning': return 'Зарядка';
			case 'workout': return 'Тренировка';
			case 'stretch': return 'Растяжка';
			default: return type;
		}
	}

	function getTypeColor(type: string): string {
		switch (type) {
			case 'morning': return 'var(--pixel-yellow)';
			case 'workout': return 'var(--pixel-accent)';
			case 'stretch': return 'var(--pixel-green)';
			default: return 'var(--text-secondary)';
		}
	}

</script>

<div class="routine-list">
	{#if routines.length === 0}
		<EmptyState
			icon="play"
			message="У вас пока нет своих сетов"
		>
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

		<div class="routines">
			{#each routines as routine (routine.id)}
				<PixelCard padding="md">
					<div class="routine-item">
						<div class="routine-info">
							<div class="routine-header">
								<span class="routine-name" title={routine.name}>{routine.name}</span>
								<span class="routine-type" style="color: {getTypeColor(routine.routine_type)}">
									{getTypeLabel(routine.routine_type)}
								</span>
							</div>
							<div class="routine-stats">
								<span class="stat">
									<PixelIcon name="timer" size="sm" color="var(--text-secondary)" />
									{routine.duration_minutes} мин
								</span>
								<span class="stat">
									<PixelIcon name="play" size="sm" color="var(--text-secondary)" />
									{routine.exercises_count} упр.
								</span>
							</div>
						</div>

						<div class="routine-actions">
							<button
								class="action-btn play"
								onclick={() => onplay(routine.id)}
								title="Начать"
							>
								<PixelIcon name="play" />
							</button>
							<button
								class="action-btn edit"
								onclick={() => onedit(routine.id)}
								title="Редактировать"
							>
								<PixelIcon name="settings" />
							</button>
							<button
								class="action-btn delete"
								onclick={() => ondelete(routine.id, routine.name)}
								title="Удалить"
							>
								<PixelIcon name="close" />
							</button>
						</div>
					</div>
				</PixelCard>
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
		margin-bottom: var(--spacing-sm);
	}

	.routines {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.routine-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.routine-info {
		flex: 1;
		min-width: 0;
	}

	.routine-header {
		display: flex;
		flex-direction: column;
		gap: 2px;
		margin-bottom: var(--spacing-xs);
	}

	.routine-name {
		font-size: var(--font-size-sm);
		font-weight: bold;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		min-width: 0;
	}

	.routine-type {
		font-size: 10px;
		text-transform: uppercase;
		align-self: flex-start;
	}

	.routine-stats {
		display: flex;
		gap: var(--spacing-md);
	}

	.stat {
		display: flex;
		align-items: center;
		gap: 4px;
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.routine-actions {
		display: flex;
		gap: 4px;
	}

	.action-btn {
		width: 36px;
		height: 36px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		cursor: pointer;
	}

	.action-btn.play {
		background: var(--pixel-green);
		border-color: var(--pixel-green);
	}

	.action-btn.edit {
		background: var(--pixel-bg-dark);
	}

	.action-btn.delete {
		background: var(--pixel-bg-dark);
		border-color: var(--pixel-red);
	}
</style>
