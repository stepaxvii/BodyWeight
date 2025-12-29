<script lang="ts">
	import { PixelButton, PixelCard, PixelIcon } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { CustomRoutineListItem, CustomRoutine } from '$lib/types';

	interface Props {
		routines: CustomRoutineListItem[];
		onplay: (routineId: number) => void;
		onedit: (routineId: number) => void;
		ondelete: (routineId: number) => void;
		oncreate: () => void;
	}

	let { routines, onplay, onedit, ondelete, oncreate }: Props = $props();

	let deletingId = $state<number | null>(null);

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

	async function confirmDelete(id: number) {
		if (deletingId === id) {
			// Second tap - actually delete
			try {
				await api.deleteCustomRoutine(id);
				ondelete(id);
				telegram.hapticNotification('success');
			} catch (err) {
				console.error('Failed to delete routine:', err);
				telegram.hapticNotification('error');
			}
			deletingId = null;
		} else {
			// First tap - show confirmation
			deletingId = id;
			telegram.hapticImpact('medium');
			// Auto-reset after 3 seconds
			setTimeout(() => {
				deletingId = null;
			}, 3000);
		}
	}
</script>

<div class="routine-list">
	{#if routines.length === 0}
		<div class="empty-state">
			<PixelIcon name="play" size="xl" color="var(--text-muted)" />
			<p>У вас пока нет своих комплексов</p>
			<PixelButton variant="primary" onclick={oncreate}>
				<PixelIcon name="plus" />
				Создать комплекс
			</PixelButton>
		</div>
	{:else}
		<div class="create-btn-wrapper">
			<PixelButton variant="secondary" fullWidth onclick={oncreate}>
				<PixelIcon name="plus" />
				Создать комплекс
			</PixelButton>
		</div>

		<div class="routines">
			{#each routines as routine (routine.id)}
				<PixelCard padding="md">
					<div class="routine-item">
						<div class="routine-info">
							<div class="routine-header">
								<span class="routine-name">{routine.name}</span>
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
								class:confirming={deletingId === routine.id}
								onclick={() => confirmDelete(routine.id)}
								title={deletingId === routine.id ? 'Нажмите ещё раз для удаления' : 'Удалить'}
							>
								{#if deletingId === routine.id}
									<PixelIcon name="check" />
								{:else}
									<PixelIcon name="close" />
								{/if}
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

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-muted);
		text-align: center;
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
		align-items: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-xs);
	}

	.routine-name {
		font-size: var(--font-size-sm);
		font-weight: bold;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.routine-type {
		font-size: 10px;
		text-transform: uppercase;
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
		border: 2px solid var(--border-color);
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

	.action-btn.delete.confirming {
		background: var(--pixel-red);
		animation: pulse 0.5s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}
</style>
