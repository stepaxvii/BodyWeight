<script lang="ts">
	import { PixelButton, PixelCard, PixelIcon } from '$lib/components/ui';
	import ExerciseInfoModal from '$lib/components/ExerciseInfoModal.svelte';
	import FilterModal from '$lib/components/FilterModal.svelte';
	import type { FilterState } from '$lib/components/FilterModal.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Exercise, CustomRoutine, CustomRoutineType, CustomRoutineCreate, ExerciseCategory } from '$lib/types';

	interface RoutineExerciseItem {
		exercise: Exercise;
		target_reps?: number;
		target_duration?: number;
		rest_seconds: number;
	}

	interface Props {
		exercises: Exercise[];
		categories?: ExerciseCategory[];
		editingRoutine?: CustomRoutine | null;
		onclose: () => void;
		onsave: (routine: CustomRoutine) => void;
	}

	let { exercises, categories = [], editingRoutine = null, onclose, onsave }: Props = $props();

	// Form state
	let name = $state(editingRoutine?.name || '');
	let description = $state(editingRoutine?.description || '');
	let routineType = $state<CustomRoutineType>(editingRoutine?.routine_type || 'workout');
	let selectedExercises = $state<RoutineExerciseItem[]>([]);
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);

	// View state
	let currentView = $state<'info' | 'exercises' | 'settings'>('info');
	let showExercisePicker = $state(false);
	let searchQuery = $state('');
	let editingExerciseIndex = $state<number | null>(null);
	let showInfoExercise = $state<Exercise | null>(null);

	// Picker filter state
	let pickerActiveCategory = $state<string | null>(null);
	let showPickerFilterModal = $state(false);
	let pickerSelectedEquipment = $state<string[]>([]);
	let pickerSelectedDifficulties = $state<number[]>([]);
	let pickerSelectedTags = $state<string[]>([]);

	// Category colors (by load type)
	const categoryColors: Record<string, string> = {
		strength: '#d82800',
		cardio: '#ff6b35',
		static: '#0058f8',
		'dynamic-stretch': '#00a800',
		'static-stretch': '#00a8a8'
	};

	// Active filter count for picker
	const pickerActiveFilterCount = $derived(
		pickerSelectedEquipment.length + pickerSelectedDifficulties.length + pickerSelectedTags.length
	);

	// Initialize from editing routine
	$effect(() => {
		if (editingRoutine) {
			selectedExercises = editingRoutine.exercises.map(ex => {
				const fullExercise = exercises.find(e => e.id === ex.exercise_id);
				return {
					exercise: fullExercise!,
					target_reps: ex.target_reps || undefined,
					target_duration: ex.target_duration || undefined,
					rest_seconds: ex.rest_seconds
				};
			});
		}
	});

	// Filter exercises for picker
	const filteredExercises = $derived.by(() => {
		let result = exercises;

		// Search query filter
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			result = result.filter(e =>
				e.name_ru.toLowerCase().includes(query) ||
				e.name.toLowerCase().includes(query)
			);
		}

		// Category filter
		if (pickerActiveCategory) {
			result = result.filter(e => e.category_slug === pickerActiveCategory);
		}

		// Equipment filter
		if (pickerSelectedEquipment.length > 0) {
			result = result.filter(e => pickerSelectedEquipment.includes(e.equipment));
		}

		// Difficulty filter
		if (pickerSelectedDifficulties.length > 0) {
			result = result.filter(e => pickerSelectedDifficulties.includes(e.difficulty));
		}

		// Tags filter (OR logic)
		if (pickerSelectedTags.length > 0) {
			result = result.filter(e => e.tags.some(t => pickerSelectedTags.includes(t)));
		}

		return result;
	});

	// Estimate duration
	const estimatedDuration = $derived.by(() => {
		let totalSeconds = 0;
		for (const item of selectedExercises) {
			// Time per exercise (either duration or ~30 sec for reps)
			totalSeconds += item.target_duration || 30;
			// Rest time
			totalSeconds += item.rest_seconds;
		}
		return Math.max(1, Math.round(totalSeconds / 60));
	});

	const routineTypes: { id: CustomRoutineType; label: string }[] = [
		{ id: 'morning', label: 'Зарядка' },
		{ id: 'workout', label: 'Тренировка' },
		{ id: 'stretch', label: 'Растяжка' }
	];

	function addExercise(exercise: Exercise) {
		// Check if already added
		if (selectedExercises.some(e => e.exercise.id === exercise.id)) {
			telegram.hapticNotification('warning');
			return;
		}

		selectedExercises = [...selectedExercises, {
			exercise,
			target_reps: exercise.is_timed ? undefined : 10,
			target_duration: exercise.is_timed ? 30 : undefined,
			rest_seconds: 30
		}];
		telegram.hapticImpact('light');
	}

	function selectPickerCategory(slug: string) {
		pickerActiveCategory = pickerActiveCategory === slug ? null : slug;
		telegram.hapticImpact('light');
	}

	function handlePickerFilterApply(filters: FilterState) {
		pickerSelectedEquipment = filters.equipment;
		pickerSelectedDifficulties = filters.difficulties;
		pickerSelectedTags = filters.tags;
	}

	function clearPickerFilters() {
		pickerSelectedEquipment = [];
		pickerSelectedDifficulties = [];
		pickerSelectedTags = [];
		pickerActiveCategory = null;
		searchQuery = '';
		telegram.hapticImpact('light');
	}

	function removeExercise(index: number) {
		selectedExercises = selectedExercises.filter((_, i) => i !== index);
		telegram.hapticImpact('light');
	}

	function moveExercise(index: number, direction: 'up' | 'down') {
		const newIndex = direction === 'up' ? index - 1 : index + 1;
		if (newIndex < 0 || newIndex >= selectedExercises.length) return;

		const newList = [...selectedExercises];
		[newList[index], newList[newIndex]] = [newList[newIndex], newList[index]];
		selectedExercises = newList;
		telegram.hapticImpact('light');
	}

	function updateExerciseSettings(index: number, updates: Partial<RoutineExerciseItem>) {
		selectedExercises = selectedExercises.map((item, i) =>
			i === index ? { ...item, ...updates } : item
		);
	}

	async function handleSubmit() {
		// Validation
		if (!name.trim()) {
			error = 'Введите название комплекса';
			return;
		}
		if (selectedExercises.length === 0) {
			error = 'Добавьте хотя бы одно упражнение';
			return;
		}

		isSubmitting = true;
		error = null;

		try {
			const data: CustomRoutineCreate = {
				name: name.trim(),
				description: description.trim() || undefined,
				routine_type: routineType,
				exercises: selectedExercises.map(item => ({
					exercise_id: item.exercise.id,
					target_reps: item.target_reps,
					target_duration: item.target_duration,
					rest_seconds: item.rest_seconds
				}))
			};

			let result: CustomRoutine;
			if (editingRoutine) {
				result = await api.updateCustomRoutine(editingRoutine.id, data);
			} else {
				result = await api.createCustomRoutine(data);
			}

			telegram.hapticNotification('success');
			onsave(result);
		} catch (err) {
			console.error('Failed to save routine:', err);
			error = err instanceof Error ? err.message : 'Ошибка сохранения';
			telegram.hapticNotification('error');
		} finally {
			isSubmitting = false;
		}
	}
</script>

<div class="editor-overlay">
	<div class="editor-container">
		<!-- Header -->
		<div class="editor-header">
			<button class="back-btn" onclick={onclose}>
				<PixelIcon name="close" />
			</button>
			<h2 class="editor-title">{editingRoutine ? 'Редактировать' : 'Новый комплекс'}</h2>
			<button
				class="save-btn"
				onclick={handleSubmit}
				disabled={isSubmitting}
			>
				{#if isSubmitting}
					<span class="spinner"></span>
				{:else}
					<PixelIcon name="check" />
				{/if}
			</button>
		</div>

		{#if error}
			<div class="error-banner">{error}</div>
		{/if}

		<!-- Navigation tabs -->
		<div class="editor-tabs">
			<button class="tab" class:active={currentView === 'info'} onclick={() => currentView = 'info'}>
				Инфо
			</button>
			<button class="tab" class:active={currentView === 'exercises'} onclick={() => currentView = 'exercises'}>
				Упражнения
				{#if selectedExercises.length > 0}
					<span class="tab-badge">{selectedExercises.length}</span>
				{/if}
			</button>
		</div>

		<!-- Content -->
		<div class="editor-content">
			{#if currentView === 'info'}
				<!-- Basic info form -->
				<div class="form-section">
					<label class="form-label">Название</label>
					<input
						type="text"
						class="form-input"
						placeholder="Мой комплекс"
						bind:value={name}
						maxlength="50"
					/>
				</div>

				<div class="form-section">
					<label class="form-label">Описание (опционально)</label>
					<textarea
						class="form-textarea"
						placeholder="Описание комплекса..."
						bind:value={description}
						maxlength="200"
						rows="3"
					></textarea>
				</div>

				<div class="form-section">
					<label class="form-label">Тип</label>
					<div class="type-selector">
						{#each routineTypes as type}
							<button
								class="type-btn"
								class:active={routineType === type.id}
								onclick={() => { routineType = type.id; telegram.hapticImpact('light'); }}
							>
								{type.label}
							</button>
						{/each}
					</div>
				</div>

				<div class="summary-card">
					<div class="summary-item">
						<PixelIcon name="timer" color="var(--text-secondary)" />
						<span>~{estimatedDuration} мин</span>
					</div>
					<div class="summary-item">
						<PixelIcon name="play" color="var(--text-secondary)" />
						<span>{selectedExercises.length} упр.</span>
					</div>
				</div>

			{:else if currentView === 'exercises'}
				<!-- Exercise list -->
				{#if selectedExercises.length === 0}
					<div class="empty-exercises">
						<PixelIcon name="play" size="xl" color="var(--text-muted)" />
						<p>Нет упражнений</p>
						<PixelButton variant="primary" onclick={() => showExercisePicker = true}>
							Добавить упражнение
						</PixelButton>
					</div>
				{:else}
					<div class="exercise-list">
						{#each selectedExercises as item, index (item.exercise.id)}
							<div class="exercise-item">
								<div class="exercise-order">
									<button
										class="order-btn"
										disabled={index === 0}
										onclick={() => moveExercise(index, 'up')}
									>▲</button>
									<span class="order-num">{index + 1}</span>
									<button
										class="order-btn"
										disabled={index === selectedExercises.length - 1}
										onclick={() => moveExercise(index, 'down')}
									>▼</button>
								</div>

								<div class="exercise-info">
									<span class="exercise-name">{item.exercise.name_ru}</span>
									<div class="exercise-params">
										{#if item.target_duration}
											<span class="param">{item.target_duration} сек</span>
										{:else if item.target_reps}
											<span class="param">{item.target_reps} повт</span>
										{/if}
										<span class="param rest">отдых {item.rest_seconds}с</span>
									</div>
								</div>

								<div class="exercise-actions">
									<button class="action-btn" onclick={() => editingExerciseIndex = index}>
										<PixelIcon name="settings" size="sm" />
									</button>
									<button class="action-btn delete" onclick={() => removeExercise(index)}>
										<PixelIcon name="close" size="sm" />
									</button>
								</div>
							</div>
						{/each}
					</div>

					<div class="add-exercise-btn">
						<PixelButton variant="secondary" fullWidth onclick={() => showExercisePicker = true}>
							<PixelIcon name="plus" />
							Добавить упражнение
						</PixelButton>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>

<!-- Exercise Picker Modal -->
{#if showExercisePicker}
	<div class="picker-overlay" onclick={() => showExercisePicker = false}>
		<div class="picker-container" onclick={(e) => e.stopPropagation()}>
			<div class="picker-header">
				<h3>Выберите упражнение</h3>
				<button class="close-btn" onclick={() => showExercisePicker = false}>
					<PixelIcon name="close" />
				</button>
			</div>

			<div class="search-box">
				<input
					type="text"
					class="search-input"
					placeholder="Поиск..."
					bind:value={searchQuery}
				/>
			</div>

			<!-- Filter header -->
			<div class="picker-filter-header">
				<span class="picker-filter-label">
					{filteredExercises.length} упражнений
				</span>
				<div class="picker-filter-actions">
					{#if pickerActiveFilterCount > 0 || pickerActiveCategory || searchQuery}
						<button class="picker-clear-btn" onclick={clearPickerFilters}>
							Сбросить
						</button>
					{/if}
					<button class="picker-filter-btn" onclick={() => showPickerFilterModal = true}>
						<PixelIcon name="settings" size="sm" />
						Фильтр
						{#if pickerActiveFilterCount > 0}
							<span class="picker-filter-badge">{pickerActiveFilterCount}</span>
						{/if}
					</button>
				</div>
			</div>

			<!-- Category tabs -->
			{#if categories.length > 0}
				<div class="picker-category-tabs">
					{#each categories as category}
						<button
							class="picker-category-tab"
							class:active={pickerActiveCategory === category.slug}
							style="--cat-color: {categoryColors[category.slug]}"
							onclick={() => selectPickerCategory(category.slug)}
						>
							{category.name_ru}
						</button>
					{/each}
				</div>
			{/if}

			<div class="picker-list">
				{#each filteredExercises as exercise (exercise.id)}
					{@const isAdded = selectedExercises.some(e => e.exercise.id === exercise.id)}
					<div class="picker-item" class:added={isAdded}>
						<button
							class="picker-item-main"
							onclick={() => { addExercise(exercise); showExercisePicker = false; }}
							disabled={isAdded}
						>
							<div class="picker-item-info">
								<span class="picker-item-name">{exercise.name_ru}</span>
								<span class="picker-item-type">
									{exercise.is_timed ? 'На время' : 'Повторения'}
								</span>
							</div>
						</button>
						<button
							class="picker-item-action info"
							onclick={() => { showInfoExercise = exercise; }}
							title="Подробнее"
						>
							?
						</button>
						<button
							class="picker-item-action add"
							onclick={() => { addExercise(exercise); showExercisePicker = false; }}
							disabled={isAdded}
						>
							{#if isAdded}
								<PixelIcon name="check" size="sm" color="var(--pixel-green)" />
							{:else}
								<PixelIcon name="plus" size="sm" color="var(--pixel-accent)" />
							{/if}
						</button>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}

<!-- Exercise Settings Modal -->
{#if editingExerciseIndex !== null}
	{@const item = selectedExercises[editingExerciseIndex]}
	<div class="settings-overlay" onclick={() => editingExerciseIndex = null}>
		<div class="settings-container" onclick={(e) => e.stopPropagation()}>
			<div class="settings-header">
				<h3>{item.exercise.name_ru}</h3>
				<button class="close-btn" onclick={() => editingExerciseIndex = null}>
					<PixelIcon name="close" />
				</button>
			</div>

			<div class="settings-content">
				{#if item.exercise.is_timed}
					<div class="form-section">
						<label class="form-label">Время (секунд)</label>
						<div class="number-input">
							<button onclick={() => updateExerciseSettings(editingExerciseIndex, { target_duration: Math.max(5, (item.target_duration || 30) - 5) })}>-</button>
							<input
								type="number"
								value={item.target_duration || 30}
								min="5"
								max="300"
								onchange={(e) => updateExerciseSettings(editingExerciseIndex, { target_duration: parseInt(e.currentTarget.value) || 30 })}
							/>
							<button onclick={() => updateExerciseSettings(editingExerciseIndex, { target_duration: Math.min(300, (item.target_duration || 30) + 5) })}>+</button>
						</div>
					</div>
				{:else}
					<div class="form-section">
						<label class="form-label">Повторения</label>
						<div class="number-input">
							<button onclick={() => updateExerciseSettings(editingExerciseIndex, { target_reps: Math.max(1, (item.target_reps || 10) - 1) })}>-</button>
							<input
								type="number"
								value={item.target_reps || 10}
								min="1"
								max="100"
								onchange={(e) => updateExerciseSettings(editingExerciseIndex, { target_reps: parseInt(e.currentTarget.value) || 10 })}
							/>
							<button onclick={() => updateExerciseSettings(editingExerciseIndex, { target_reps: Math.min(100, (item.target_reps || 10) + 1) })}>+</button>
						</div>
					</div>
				{/if}

				<div class="form-section">
					<label class="form-label">Отдых после (секунд)</label>
					<div class="number-input">
						<button onclick={() => updateExerciseSettings(editingExerciseIndex, { rest_seconds: Math.max(0, item.rest_seconds - 5) })}>-</button>
						<input
							type="number"
							value={item.rest_seconds}
							min="0"
							max="120"
							onchange={(e) => updateExerciseSettings(editingExerciseIndex, { rest_seconds: parseInt(e.currentTarget.value) || 30 })}
						/>
						<button onclick={() => updateExerciseSettings(editingExerciseIndex, { rest_seconds: Math.min(120, item.rest_seconds + 5) })}>+</button>
					</div>
				</div>
			</div>

			<div class="settings-footer">
				<PixelButton variant="primary" fullWidth onclick={() => editingExerciseIndex = null}>
					Готово
				</PixelButton>
			</div>
		</div>
	</div>
{/if}

<!-- Exercise Info Modal -->
<ExerciseInfoModal
	exercise={showInfoExercise}
	open={showInfoExercise !== null}
	onclose={() => showInfoExercise = null}
/>

<!-- Filter Modal for Picker -->
<FilterModal
	open={showPickerFilterModal}
	initialFilters={{
		equipment: pickerSelectedEquipment,
		difficulties: pickerSelectedDifficulties,
		tags: pickerSelectedTags
	}}
	onClose={() => showPickerFilterModal = false}
	onApply={handlePickerFilterApply}
/>

<style>
	.editor-overlay {
		position: fixed;
		inset: 0;
		background: var(--pixel-bg);
		z-index: 1000;
		display: flex;
		flex-direction: column;
	}

	.editor-container {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.editor-header {
		display: flex;
		align-items: center;
		padding: var(--spacing-md);
		border-bottom: 2px solid var(--border-color);
	}

	.back-btn, .save-btn {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		cursor: pointer;
	}

	.save-btn {
		background: var(--pixel-green);
		border-color: var(--pixel-green);
	}

	.save-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.editor-title {
		flex: 1;
		text-align: center;
		font-size: var(--font-size-md);
		margin: 0;
	}

	.error-banner {
		background: var(--pixel-red);
		color: white;
		padding: var(--spacing-sm);
		text-align: center;
		font-size: var(--font-size-xs);
	}

	.editor-tabs {
		display: flex;
		border-bottom: 2px solid var(--border-color);
	}

	.tab {
		flex: 1;
		padding: var(--spacing-sm) var(--spacing-md);
		background: transparent;
		border: none;
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-xs);
	}

	.tab.active {
		color: var(--pixel-accent);
		border-bottom: 2px solid var(--pixel-accent);
		margin-bottom: -2px;
	}

	.tab-badge {
		background: var(--pixel-accent);
		color: var(--pixel-bg);
		padding: 2px 6px;
		font-size: 10px;
		border-radius: 2px;
	}

	.editor-content {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-md);
	}

	/* Form styles */
	.form-section {
		margin-bottom: var(--spacing-md);
	}

	.form-label {
		display: block;
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		margin-bottom: var(--spacing-xs);
		text-transform: uppercase;
	}

	.form-input, .form-textarea {
		width: 100%;
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-primary);
	}

	.form-input:focus, .form-textarea:focus {
		outline: none;
		border-color: var(--pixel-accent);
	}

	.form-textarea {
		resize: none;
	}

	.type-selector {
		display: flex;
		gap: var(--spacing-xs);
	}

	.type-btn {
		flex: 1;
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
	}

	.type-btn.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	.summary-card {
		display: flex;
		justify-content: center;
		gap: var(--spacing-lg);
		padding: var(--spacing-md);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		margin-top: var(--spacing-lg);
	}

	.summary-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
	}

	/* Exercise list */
	.empty-exercises {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-muted);
	}

	.exercise-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.exercise-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
	}

	.exercise-order {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
	}

	.order-btn {
		width: 20px;
		height: 16px;
		font-size: 8px;
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
	}

	.order-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.order-num {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.exercise-info {
		flex: 1;
		min-width: 0;
	}

	.exercise-name {
		display: block;
		font-size: var(--font-size-xs);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.exercise-params {
		display: flex;
		gap: var(--spacing-sm);
		margin-top: 2px;
	}

	.param {
		font-size: 10px;
		color: var(--pixel-green);
	}

	.param.rest {
		color: var(--text-muted);
	}

	.exercise-actions {
		display: flex;
		gap: 4px;
	}

	.action-btn {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
		cursor: pointer;
	}

	.action-btn.delete {
		border-color: var(--pixel-red);
	}

	.add-exercise-btn {
		margin-top: var(--spacing-md);
	}

	/* Picker modal */
	.picker-overlay, .settings-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.8);
		z-index: 1100;
		display: flex;
		align-items: flex-end;
	}

	.picker-container, .settings-container {
		width: 100%;
		max-height: 80vh;
		background: var(--pixel-bg);
		border-top: 2px solid var(--border-color);
		display: flex;
		flex-direction: column;
	}

	.picker-header, .settings-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-md);
		border-bottom: 2px solid var(--border-color);
	}

	.picker-header h3, .settings-header h3 {
		font-size: var(--font-size-sm);
		margin: 0;
	}

	.close-btn {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: none;
		cursor: pointer;
	}

	.search-box {
		padding: var(--spacing-sm) var(--spacing-md);
		border-bottom: 2px solid var(--border-color);
	}

	.search-input {
		width: 100%;
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-primary);
	}

	/* Picker filter header */
	.picker-filter-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-xs) var(--spacing-md);
		border-bottom: 2px solid var(--border-color);
	}

	.picker-filter-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.picker-filter-actions {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.picker-filter-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
	}

	.picker-filter-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.picker-filter-badge {
		background: var(--pixel-accent);
		color: var(--pixel-bg);
		padding: 1px 4px;
		font-size: 8px;
		min-width: 12px;
		text-align: center;
	}

	.picker-clear-btn {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		text-decoration: underline;
	}

	/* Picker category tabs */
	.picker-category-tabs {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm) var(--spacing-md);
		border-bottom: 2px solid var(--border-color);
	}

	.picker-category-tab {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--cat-color);
		color: var(--cat-color);
		cursor: pointer;
	}

	.picker-category-tab.active {
		background: var(--cat-color);
		color: var(--pixel-bg);
	}

	.picker-list {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-sm);
	}

	.picker-item {
		width: 100%;
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		margin-bottom: var(--spacing-xs);
	}

	.picker-item:hover {
		border-color: var(--pixel-accent);
	}

	.picker-item.added {
		opacity: 0.5;
	}

	.picker-item-main {
		flex: 1;
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		background: transparent;
		border: none;
		cursor: pointer;
		text-align: left;
		min-width: 0;
	}

	.picker-item-main:disabled {
		cursor: not-allowed;
	}

	.picker-item-info {
		flex: 1;
		min-width: 0;
	}

	.picker-item-name {
		display: block;
		font-size: var(--font-size-sm);
		font-weight: 500;
		margin-bottom: 2px;
	}

	.picker-item-type {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.picker-item-action {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: none;
		cursor: pointer;
		flex-shrink: 0;
	}

	.picker-item-action.info {
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		font-weight: bold;
		color: var(--text-secondary);
	}

	.picker-item-action.info:hover {
		border-color: var(--pixel-accent);
		color: var(--pixel-accent);
	}

	.picker-item-action:hover {
		transform: scale(1.1);
	}

	.picker-item-action:disabled {
		cursor: not-allowed;
		opacity: 0.5;
	}

	/* Settings modal */
	.settings-container {
		max-height: 60vh;
	}

	.settings-content {
		padding: var(--spacing-md);
	}

	.number-input {
		display: flex;
		align-items: center;
	}

	.number-input button {
		width: 40px;
		height: 40px;
		font-size: var(--font-size-lg);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-primary);
		cursor: pointer;
	}

	.number-input input {
		flex: 1;
		text-align: center;
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-md);
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		border-left: none;
		border-right: none;
		color: var(--text-primary);
	}

	.settings-footer {
		padding: var(--spacing-md);
		border-top: 2px solid var(--border-color);
	}

	.spinner {
		width: 16px;
		height: 16px;
		border: 2px solid var(--pixel-bg);
		border-top-color: transparent;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}
</style>
