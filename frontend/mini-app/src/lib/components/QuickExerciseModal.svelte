<script lang="ts">
	import { PixelButton, PixelCard, PixelModal, PixelIcon } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { favoritesStore } from '$lib/stores/favorites.svelte';
	import { exercisesStore } from '$lib/stores/exercises.svelte';
	import { calculateCyclingXp } from '$lib/utils/xp';
	import { getTagName } from '$lib/utils';
	import type { Exercise, EquipmentType, ExerciseCategory } from '$lib/types';
	import { onMount } from 'svelte';

	interface Props {
		open?: boolean;
		onclose?: () => void;
		onsave?: (xp: number, coins: number) => void;
	}

	let { open = false, onclose, onsave }: Props = $props();

	type Step = 'mode' | 'exercise' | 'input' | 'filters' | 'cycling-input';
	type ExerciseMode = 'favorites' | 'all';

	let step = $state<Step>('mode');
	let exerciseMode = $state<ExerciseMode>('all');
	let exercises = $state<Exercise[]>([]);
	let filteredExercises = $state<Exercise[]>([]);
	let selectedExercise = $state<Exercise | null>(null);
	let reps = $state(10);
	let duration = $state(30);
	let cyclingDistanceKm = $state(6.5);
	let cyclingDurationMin = $state(23);
	let isSubmitting = $state(false);
	
	// Search and filter state
	let searchQuery = $state('');
	let selectedEquipment = $state<string[]>([]);
	let selectedDifficulties = $state<number[]>([]);
	let selectedTags = $state<string[]>([]);
	let selectedCategory = $state<string | null>(null);
	let categories = $state<ExerciseCategory[]>([]);

	// Filter options
	const EQUIPMENT_OPTIONS = [
		{ id: 'none', label: 'Без снаряжения' },
		{ id: 'pullup-bar', label: 'Турник' },
		{ id: 'dip-bars', label: 'Брусья' },
		{ id: 'bench', label: 'Скамья' },
		{ id: 'wall', label: 'Стена' },
		{ id: 'bike', label: 'Велосипед' }
		{ id: 'dumbbell', label: 'Гантели' }
	];

	const MUSCLE_TAG_IDS = [
		'chest', 'back', 'shoulders', 'triceps', 'core',
		'quads', 'glutes', 'calves', 'full-body'
	];

	onMount(async () => {
		try {
			const [exercisesResponse, categoriesResponse] = await Promise.all([
				exercisesStore.loadAll(),
				api.getCategories().catch(() => [])
			]);
			exercises = exercisesResponse;
			categories = categoriesResponse;
		} catch {
			// exercisesStore.loadAll() handles localStorage fallback internally
			exercises = exercisesStore.exercises;
		}
		try {
			await favoritesStore.loadFavorites();
		} catch {
			// Favorites may not load offline, that's ok
		}
	});

	// Filtered exercises based on mode, search, and filters
	const displayedExercises = $derived.by(() => {
		let result = exercises;

		// Mode filter: favorites or all
		if (exerciseMode === 'favorites') {
			result = result.filter(e => favoritesStore.isFavorite(e.id));
		}

		// Search query filter
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			result = result.filter(e =>
				e.name_ru.toLowerCase().includes(query) ||
				e.name.toLowerCase().includes(query)
			);
		}

		// Category filter
		if (selectedCategory) {
			result = result.filter(e => e.category_slug === selectedCategory);
		}

		// Equipment filter
		if (selectedEquipment.length > 0) {
			result = result.filter(e => selectedEquipment.includes(e.equipment));
		}

		// Difficulty filter
		if (selectedDifficulties.length > 0) {
			result = result.filter(e => selectedDifficulties.includes(e.difficulty));
		}

		// Tags filter (OR logic)
		if (selectedTags.length > 0) {
			result = result.filter(e => e.tags.some(t => selectedTags.includes(t)));
		}

		// Cycling is handled by a dedicated quick-flow (distance + duration),
		// not by the generic reps/sets UI.
		result = result.filter(e => e.slug !== 'cycling');

		return result;
	});

	const activeFilterCount = $derived(
		selectedEquipment.length + selectedDifficulties.length + selectedTags.length + (selectedCategory ? 1 : 0)
	);

	function selectMode(mode: ExerciseMode) {
		exerciseMode = mode;
		step = 'exercise';
		telegram.hapticImpact('light');
	}

	function selectExercise(ex: Exercise) {
		selectedExercise = ex;
		step = 'input';
		telegram.hapticImpact('light');
	}

	function selectCycling() {
		step = 'cycling-input';
		telegram.hapticImpact('light');
	}

	function goBack() {
		if (step === 'exercise') {
			step = 'mode';
			// Reset filters when going back
			searchQuery = '';
			selectedEquipment = [];
			selectedDifficulties = [];
			selectedTags = [];
			selectedCategory = null;
		} else if (step === 'input') {
			step = 'exercise';
		} else if (step === 'filters') {
			step = 'exercise';
		} else if (step === 'cycling-input') {
			step = 'mode';
		}
		telegram.hapticImpact('light');
	}

	function openFilters() {
		step = 'filters';
		telegram.hapticImpact('light');
	}

	function toggleEquipment(id: string) {
		telegram.hapticImpact('light');
		if (selectedEquipment.includes(id)) {
			selectedEquipment = selectedEquipment.filter(e => e !== id);
		} else {
			selectedEquipment = [...selectedEquipment, id];
		}
	}

	function toggleDifficulty(level: number) {
		telegram.hapticImpact('light');
		if (selectedDifficulties.includes(level)) {
			selectedDifficulties = selectedDifficulties.filter(d => d !== level);
		} else {
			selectedDifficulties = [...selectedDifficulties, level];
		}
	}

	function toggleTag(id: string) {
		telegram.hapticImpact('light');
		if (selectedTags.includes(id)) {
			selectedTags = selectedTags.filter(t => t !== id);
		} else {
			selectedTags = [...selectedTags, id];
		}
	}

	function toggleCategory(slug: string) {
		telegram.hapticImpact('light');
		if (selectedCategory === slug) {
			selectedCategory = null;
		} else {
			selectedCategory = slug;
		}
	}

	function clearFilters() {
		telegram.hapticImpact('medium');
		selectedEquipment = [];
		selectedDifficulties = [];
		selectedTags = [];
		selectedCategory = null;
		searchQuery = '';
	}

	function handleClose() {
		step = 'mode';
		exerciseMode = 'all';
		selectedExercise = null;
		reps = 10;
		duration = 30;
		cyclingDistanceKm = 6.5;
		cyclingDurationMin = 23;
		searchQuery = '';
		selectedEquipment = [];
		selectedDifficulties = [];
		selectedTags = [];
		selectedCategory = null;
		onclose?.();
	}

	// Check if exercise is time-based (planks, stretches, etc)
	function isTimeBased(ex: Exercise): boolean {
		// Use is_timed flag from backend, fallback to category check
		if (ex.is_timed !== undefined) {
			return ex.is_timed;
		}
		const timeBasedCategories = ['static', 'stretch'];
		return timeBasedCategories.includes(ex.category_slug);
	}

	async function handleSave() {
		if (!selectedExercise || isSubmitting) return;

		isSubmitting = true;
		telegram.hapticNotification('success');

		const timeBased = isTimeBased(selectedExercise);
		const workoutData = {
			duration_seconds: timeBased ? duration : 30,
			exercises: [{
				exercise_slug: selectedExercise.slug,
				sets: timeBased ? [duration] : [reps],
				is_timed: timeBased,
			}],
			completed_at: new Date().toISOString(),
		};

		try {
			const response = await api.submitWorkout(workoutData);
			const completed = response.workout;
			await userStore.loadUser();
			onsave?.(completed.total_xp_earned, completed.total_coins_earned);
			handleClose();
		} catch (err) {
			// Offline: save to pending queue for later sync
			if (!navigator.onLine) {
				savePendingWorkout(workoutData);
				telegram.hapticNotification('success');
				onsave?.(selectedExercise.base_xp, 0);
				handleClose();
			} else {
				console.error('Failed to save exercise:', err);
				telegram.hapticNotification('error');
			}
		} finally {
			isSubmitting = false;
		}
	}

	async function handleSaveCycling() {
		if (isSubmitting) return;
		if (cyclingDistanceKm <= 0 || cyclingDurationMin < 5) {
			telegram.hapticNotification('error');
			return;
		}

		isSubmitting = true;
		telegram.hapticNotification('success');

		const workoutData = {
			duration_seconds: cyclingDurationMin * 60,
			exercises: [{
				exercise_slug: 'cycling',
				sets: [Math.max(1, Math.round(cyclingDistanceKm * 10))], // 100m units
				is_timed: false,
				distance_km: cyclingDistanceKm,
				duration_minutes: cyclingDurationMin
			}],
			completed_at: new Date().toISOString()
		};

		try {
			const response = await api.submitWorkout(workoutData);
			const completed = response.workout;
			await userStore.loadUser();
			onsave?.(completed.total_xp_earned, completed.total_coins_earned);
			handleClose();
		} catch (err) {
			if (!navigator.onLine) {
				savePendingWorkout(workoutData);
				telegram.hapticNotification('success');
				onsave?.(calculateCyclingXp(cyclingDistanceKm, cyclingDurationMin), 0);
				handleClose();
			} else {
				console.error('Failed to save cycling activity:', err);
				telegram.hapticNotification('error');
			}
		} finally {
			isSubmitting = false;
		}
	}

		const cyclingSpeedKmh = $derived.by(() => {
		if (cyclingDurationMin <= 0) return 0;
		return cyclingDistanceKm / (cyclingDurationMin / 60);
	});

	const cyclingEstimatedXp = $derived.by(() => (
		calculateCyclingXp(cyclingDistanceKm, cyclingDurationMin)
	));

	function savePendingWorkout(data: Parameters<typeof api.submitWorkout>[0]) {
		try {
			const pending = JSON.parse(localStorage.getItem('pending_workouts') || '[]');
			pending.push({ data, timestamp: Date.now() });
			localStorage.setItem('pending_workouts', JSON.stringify(pending));
		} catch (e) {
			console.error('Failed to save pending workout:', e);
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
		{#if step === 'mode'}
			<p class="step-hint">Выбери режим:</p>
			<div class="mode-list">
				<button
					class="mode-option"
					onclick={selectCycling}
				>
					<PixelIcon name="workout" size="lg" color="var(--pixel-green)" />
					<span>Поездка на велосипеде</span>
				</button>
				<button
					class="mode-option"
					onclick={() => selectMode('favorites')}
				>
					<PixelIcon name="heart" size="lg" color="var(--pixel-red)" />
					<span>Избранные</span>
					{#if favoritesStore.count > 0}
						<span class="mode-badge">{favoritesStore.count}</span>
					{/if}
				</button>
				<button
					class="mode-option"
					onclick={() => selectMode('all')}
				>
					<PixelIcon name="settings" size="lg" color="var(--pixel-accent)" />
					<span>Все упражнения</span>
				</button>
			</div>
		{:else if step === 'exercise'}
			<div class="step-header">
				<button class="back-btn" onclick={goBack}>
					<PixelIcon name="arrow-left" size="sm" />
				</button>
				<p class="step-hint">
					{exerciseMode === 'favorites' ? 'Избранные упражнения' : 'Выбери упражнение:'}
				</p>
			</div>

			<!-- Search box -->
			<div class="search-box">
				<input
					type="text"
					class="search-input"
					placeholder="Поиск упражнений..."
					bind:value={searchQuery}
				/>
				{#if searchQuery}
					<button class="clear-search-btn" onclick={() => searchQuery = ''}>
						<PixelIcon name="close" size="sm" />
					</button>
				{:else}
					<PixelIcon name="search" size="sm" color="var(--text-secondary)" class="search-icon" />
				{/if}
			</div>

			<!-- Filter bar -->
			<div class="filter-bar">
				<button class="filter-btn" onclick={openFilters}>
					<PixelIcon name="settings" size="sm" />
					Фильтр
					{#if activeFilterCount > 0}
						<span class="filter-badge">{activeFilterCount}</span>
					{/if}
				</button>
				{#if activeFilterCount > 0 || searchQuery}
					<button class="clear-filters-btn" onclick={clearFilters}>
						Сбросить
					</button>
				{/if}
			</div>

			<!-- Category tabs (if any selected or in all mode) -->
			{#if exerciseMode === 'all' && categories.length > 0}
				<div class="category-tabs">
					<button
						class="category-tab"
						class:active={selectedCategory === null}
						onclick={() => selectedCategory = null}
					>
						Все
					</button>
					{#each categories as cat}
						<button
							class="category-tab"
							class:active={selectedCategory === cat.slug}
							onclick={() => toggleCategory(cat.slug)}
						>
							{cat.name_ru}
						</button>
					{/each}
				</div>
			{/if}

			<!-- Exercise list -->
			<div class="exercise-list">
				{#each displayedExercises as ex}
					<button
						class="exercise-option"
						onclick={() => selectExercise(ex)}
					>
						<span class="exercise-name">{ex.name_ru}</span>
						<span class="exercise-xp">+{ex.base_xp} XP</span>
					</button>
				{/each}
				{#if displayedExercises.length === 0}
					<p class="no-exercises">
						{#if exerciseMode === 'favorites'}
							Нет избранных упражнений
						{:else if searchQuery || activeFilterCount > 0}
							Ничего не найдено
						{:else}
							Нет упражнений
						{/if}
					</p>
				{/if}
			</div>
		{:else if step === 'filters'}
			<div class="step-header">
				<button class="back-btn" onclick={goBack}>
					<PixelIcon name="arrow-left" size="sm" />
				</button>
				<p class="step-hint">Фильтры</p>
			</div>

			<div class="filter-sections">
				<!-- Category filter -->
				<div class="filter-section">
					<h4 class="filter-section-title">Категория</h4>
					<div class="filter-options">
						<button
							class="filter-option"
							class:active={selectedCategory === null}
							onclick={() => selectedCategory = null}
						>
							Все
						</button>
						{#each categories as cat}
							<button
								class="filter-option"
								class:active={selectedCategory === cat.slug}
								onclick={() => toggleCategory(cat.slug)}
							>
								{cat.name_ru}
							</button>
						{/each}
					</div>
				</div>

				<!-- Equipment filter -->
				<div class="filter-section">
					<h4 class="filter-section-title">Оборудование</h4>
					<div class="filter-options">
						{#each EQUIPMENT_OPTIONS as eq}
							<button
								class="filter-option"
								class:active={selectedEquipment.includes(eq.id)}
								onclick={() => toggleEquipment(eq.id)}
							>
								{eq.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- Difficulty filter -->
				<div class="filter-section">
					<h4 class="filter-section-title">Сложность</h4>
					<div class="filter-options">
						{#each [1, 2, 3, 4, 5] as level}
							<button
								class="filter-option"
								class:active={selectedDifficulties.includes(level)}
								onclick={() => toggleDifficulty(level)}
							>
								{'★'.repeat(level) + '☆'.repeat(5 - level)}
							</button>
						{/each}
					</div>
				</div>

				<!-- Tags filter -->
				<div class="filter-section">
					<h4 class="filter-section-title">Группы мышц</h4>
					<div class="filter-options">
						{#each MUSCLE_TAG_IDS as tagId}
							<button
								class="filter-option"
								class:active={selectedTags.includes(tagId)}
								onclick={() => toggleTag(tagId)}
							>
								{getTagName(tagId)}
							</button>
						{/each}
					</div>
				</div>
			</div>

			<div class="filter-actions">
				<PixelButton variant="secondary" fullWidth onclick={clearFilters}>
					Сбросить все
				</PixelButton>
				<PixelButton variant="primary" fullWidth onclick={goBack}>
					Применить
				</PixelButton>
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
		{:else if step === 'cycling-input'}
			<div class="step-header">
				<button class="back-btn" onclick={goBack}>
					<PixelIcon name="arrow-left" size="sm" />
				</button>
				<p class="step-hint">Поездка на велосипеде</p>
			</div>
			<div class="input-section">
				<p class="input-label">Дистанция (км):</p>
				<input
					type="number"
					min="0.1"
					step="0.1"
					class="search-input"
					bind:value={cyclingDistanceKm}
				/>

				<p class="input-label">Время (мин):</p>
				<input
					type="number"
					min="5"
					step="1"
					class="search-input"
					bind:value={cyclingDurationMin}
				/>

				<div class="cycling-summary">
					<span>Ср. скорость: {cyclingSpeedKmh.toFixed(1)} км/ч</span>
					<span>Ожидаемо: +{cyclingEstimatedXp} XP</span>
				</div>
			</div>
			<div class="save-section">
				<PixelButton
					variant="success"
					size="lg"
					fullWidth
					loading={isSubmitting}
					onclick={handleSaveCycling}
				>
					Записать поездку
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
		max-height: 70vh;
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

	.mode-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.mode-option {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		cursor: pointer;
		transition: all var(--transition-fast);
		position: relative;
	}

	.mode-option:hover {
		border-color: var(--pixel-accent);
		background: var(--pixel-card-hover);
	}

	.mode-option span {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
	}

	.mode-badge {
		margin-left: auto;
		background: var(--pixel-accent);
		color: var(--pixel-bg);
		padding: 2px 6px;
		font-size: var(--font-size-xs);
		border-radius: 2px;
	}

	/* Search box */
	.search-box {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-input {
		width: 100%;
		padding: var(--spacing-sm) var(--spacing-md);
		padding-right: 40px;
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-primary);
	}

	.search-input:focus {
		outline: none;
		border-color: var(--pixel-accent);
	}

	.search-input::placeholder {
		color: var(--text-muted);
	}

	.search-icon {
		position: absolute;
		right: var(--spacing-sm);
		pointer-events: none;
	}

	.clear-search-btn {
		position: absolute;
		right: var(--spacing-xs);
		background: none;
		border: none;
		padding: var(--spacing-xs);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-secondary);
	}

	.clear-search-btn:hover {
		color: var(--text-primary);
	}

	/* Filter bar */
	.filter-bar {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.filter-btn {
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

	.filter-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.filter-badge {
		background: var(--pixel-accent);
		color: var(--pixel-bg);
		padding: 1px 4px;
		font-size: 8px;
		min-width: 12px;
		text-align: center;
	}

	.clear-filters-btn {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		text-decoration: underline;
	}

	/* Category tabs */
	.category-tabs {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}

	.category-tab {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
	}

	.category-tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
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

	/* Filter sections */
	.filter-sections {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		max-height: 400px;
		overflow-y: auto;
	}

	.filter-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.filter-section-title {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
		margin: 0;
	}

	.filter-options {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}

	.filter-option {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.filter-option:hover {
		border-color: var(--pixel-accent);
	}

	.filter-option.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	.filter-actions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		padding-top: var(--spacing-md);
		border-top: 2px solid var(--border-color);
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

	.cycling-summary {
		display: flex;
		flex-direction: column;
		gap: 6px;
		align-items: center;
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
	}
</style>
