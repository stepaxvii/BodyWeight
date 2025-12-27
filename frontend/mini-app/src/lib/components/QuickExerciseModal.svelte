<script lang="ts">
	import { PixelButton, PixelCard, PixelModal, PixelIcon } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import type { Exercise, EquipmentType } from '$lib/types';
	import { onMount } from 'svelte';

	interface Props {
		open?: boolean;
		onclose?: () => void;
		onsave?: (xp: number, coins: number) => void;
	}

	let { open = false, onclose, onsave }: Props = $props();

	type Step = 'equipment' | 'exercise' | 'input';

	let step = $state<Step>('equipment');
	let selectedEquipment = $state<EquipmentType>('none');
	let exercises = $state<Exercise[]>([]);
	let filteredExercises = $state<Exercise[]>([]);
	let selectedExercise = $state<Exercise | null>(null);
	let reps = $state(10);
	let duration = $state(30);
	let isSubmitting = $state(false);

	const equipmentOptions: { id: EquipmentType; name: string; icon: string }[] = [
		{ id: 'none', name: 'Без оборудования', icon: 'home' },
		{ id: 'pullup-bar', name: 'Турник', icon: 'pullup' },
		{ id: 'dip-bars', name: 'Брусья', icon: 'dip' }
	];

	onMount(async () => {
		exercises = await api.getExercises();
	});

	function selectEquipment(eq: EquipmentType) {
		selectedEquipment = eq;
		filteredExercises = exercises.filter(e => e.equipment === eq);
		step = 'exercise';
		telegram.hapticImpact('light');
	}

	function selectExercise(ex: Exercise) {
		selectedExercise = ex;
		step = 'input';
		telegram.hapticImpact('light');
	}

	function goBack() {
		if (step === 'exercise') {
			step = 'equipment';
		} else if (step === 'input') {
			step = 'exercise';
		}
		telegram.hapticImpact('light');
	}

	function handleClose() {
		step = 'equipment';
		selectedExercise = null;
		reps = 10;
		duration = 30;
		onclose?.();
	}

	// Check if exercise is time-based (planks, stretches, etc)
	function isTimeBased(ex: Exercise): boolean {
		const timeBasedCategories = ['static', 'stretch'];
		return timeBasedCategories.includes(ex.category_slug);
	}

	async function handleSave() {
		if (!selectedExercise || isSubmitting) return;

		isSubmitting = true;
		telegram.hapticNotification('success');

		try {
			// Start a quick workout session
			const session = await api.startWorkout();

			// Add the exercise
			const value = isTimeBased(selectedExercise) ? Math.ceil(duration / 10) : reps;
			const result = await api.addExerciseToWorkout(session.id, selectedExercise.slug, value, 1);

			// Complete the workout
			const completed = await api.completeWorkout(session.id);

			// Update user stats locally
			userStore.addXp(completed.total_xp_earned);
			userStore.addCoins(completed.total_coins_earned);

			onsave?.(completed.total_xp_earned, completed.total_coins_earned);
			handleClose();
		} catch (err) {
			console.error('Failed to save exercise:', err);
			telegram.hapticNotification('error');
		} finally {
			isSubmitting = false;
		}
	}

	function adjustValue(delta: number) {
		if (isTimeBased(selectedExercise!)) {
			duration = Math.max(5, Math.min(300, duration + delta));
		} else {
			reps = Math.max(1, Math.min(999, reps + delta));
		}
		telegram.hapticImpact('light');
	}
</script>

<PixelModal {open} title="Быстрая запись" onclose={handleClose}>
	<div class="quick-modal">
		{#if step === 'equipment'}
			<p class="step-hint">Выбери оборудование:</p>
			<div class="equipment-list">
				{#each equipmentOptions as eq}
					<button
						class="equipment-option"
						onclick={() => selectEquipment(eq.id)}
					>
						<PixelIcon name={eq.icon} size="lg" color="var(--pixel-accent)" />
						<span>{eq.name}</span>
					</button>
				{/each}
			</div>
		{:else if step === 'exercise'}
			<div class="step-header">
				<button class="back-btn" onclick={goBack}>
					<PixelIcon name="arrow-left" size="sm" />
				</button>
				<p class="step-hint">Выбери упражнение:</p>
			</div>
			<div class="exercise-list">
				{#each filteredExercises as ex}
					<button
						class="exercise-option"
						onclick={() => selectExercise(ex)}
					>
						<span class="exercise-name">{ex.name_ru}</span>
						<span class="exercise-xp">+{ex.base_xp} XP</span>
					</button>
				{/each}
				{#if filteredExercises.length === 0}
					<p class="no-exercises">Нет упражнений для выбранного оборудования</p>
				{/if}
			</div>
		{:else if step === 'input' && selectedExercise}
			<div class="step-header">
				<button class="back-btn" onclick={goBack}>
					<PixelIcon name="arrow-left" size="sm" />
				</button>
				<p class="step-hint">{selectedExercise.name_ru}</p>
			</div>
			<div class="input-section">
				{#if isTimeBased(selectedExercise)}
					<p class="input-label">Длительность (секунды):</p>
					<div class="value-input">
						<button class="adjust-btn" onclick={() => adjustValue(-10)}>-10</button>
						<span class="value-display">{duration}</span>
						<button class="adjust-btn" onclick={() => adjustValue(10)}>+10</button>
					</div>
				{:else}
					<p class="input-label">Количество повторений:</p>
					<div class="value-input">
						<button class="adjust-btn" onclick={() => adjustValue(-5)}>-5</button>
						<span class="value-display">{reps}</span>
						<button class="adjust-btn" onclick={() => adjustValue(5)}>+5</button>
					</div>
				{/if}
			</div>
			<div class="save-section">
				<PixelButton
					variant="success"
					size="lg"
					fullWidth
					loading={isSubmitting}
					onclick={handleSave}
				>
					Записать
				</PixelButton>
			</div>
		{/if}
	</div>
</PixelModal>

<style>
	.quick-modal {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		min-height: 200px;
	}

	.step-hint {
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		margin: 0;
	}

	.step-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.back-btn {
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		padding: var(--spacing-xs);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.back-btn:hover {
		border-color: var(--pixel-accent);
	}

	.equipment-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.equipment-option {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.equipment-option:hover {
		border-color: var(--pixel-accent);
		background: var(--pixel-card-hover);
	}

	.equipment-option span {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
	}

	.exercise-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
		max-height: 300px;
		overflow-y: auto;
	}

	.exercise-option {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-sm) var(--spacing-md);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.exercise-option:hover {
		border-color: var(--pixel-accent);
		background: var(--pixel-card-hover);
	}

	.exercise-name {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
	}

	.exercise-xp {
		font-size: var(--font-size-xs);
		color: var(--pixel-green);
	}

	.no-exercises {
		font-size: var(--font-size-sm);
		color: var(--text-muted);
		text-align: center;
		padding: var(--spacing-lg);
	}

	.input-section {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-lg) 0;
	}

	.input-label {
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		margin: 0;
	}

	.value-input {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.adjust-btn {
		padding: var(--spacing-sm) var(--spacing-md);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		font-size: var(--font-size-sm);
		color: var(--text-primary);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.adjust-btn:hover {
		border-color: var(--pixel-accent);
		background: var(--pixel-card-hover);
	}

	.adjust-btn:active {
		transform: scale(0.95);
	}

	.value-display {
		font-size: var(--font-size-xl);
		color: var(--pixel-accent);
		min-width: 80px;
		text-align: center;
	}

	.save-section {
		padding-top: var(--spacing-md);
		border-top: 2px solid var(--border-color);
	}
</style>
