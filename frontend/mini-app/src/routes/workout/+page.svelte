<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon } from '$lib/components/ui';
	import PixelExerciseDemo from '$lib/components/ui/PixelExerciseDemo.svelte';
	import RoutinePlayer from '$lib/components/RoutinePlayer.svelte';
	import ExerciseCard from '$lib/components/ExerciseCard.svelte';
	import FilterModal from '$lib/components/FilterModal.svelte';
	import type { FilterState } from '$lib/components/FilterModal.svelte';
	import { api } from '$lib/api/client';
	import { workoutStore } from '$lib/stores/workout.svelte';
	import { favoritesStore } from '$lib/stores/favorites.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { ExerciseCategory, Exercise, Routine, RoutineCategory } from '$lib/types';

	// Data
	let categories = $state<ExerciseCategory[]>([]);
	let exercises = $state<Exercise[]>([]);
	let routines = $state<Routine[]>([]);

	// Main tab state
	type MainTab = 'routines' | 'favorites' | 'exercises';
	let activeMainTab = $state<MainTab>('routines');

	// UI state
	let activeCategory = $state<string | null>(null);
	let selectedRoutine = $state<Routine | null>(null);
	let showRoutinePlayer = $state(false);
	let activeRoutineCategory = $state<RoutineCategory>('morning');

	// Filter state
	let showFilterModal = $state(false);
	let selectedEquipment = $state<string[]>([]);
	let selectedDifficulties = $state<number[]>([]);
	let selectedTags = $state<string[]>([]);

	// Filtered exercises by all criteria
	const filteredExercises = $derived(() => {
		let result = exercises;

		// Category filter
		if (activeCategory) {
			result = result.filter(e => e.category_slug === activeCategory);
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

		return result;
	});

	// Favorite exercises
	const favoriteExercises = $derived(
		exercises.filter(e => favoritesStore.isFavorite(e.id))
	);

	// Filtered routines by category
	const filteredRoutines = $derived(
		routines.filter(r => r.category === activeRoutineCategory)
	);

	// Active filter count for badge
	const activeFilterCount = $derived(
		selectedEquipment.length + selectedDifficulties.length + selectedTags.length
	);

	// Category colors (by load type)
	const categoryColors: Record<string, string> = {
		strength: '#d82800',
		cardio: '#ff6b35',
		static: '#0058f8',
		'dynamic-stretch': '#00a800',
		'static-stretch': '#00a8a8'
	};

	const routineCategoryTabs: { id: RoutineCategory; name: string }[] = [
		{ id: 'morning', name: 'Зарядка' },
		{ id: 'home', name: 'Дома' },
		{ id: 'pullup-bar', name: 'Турник' },
		{ id: 'dip-bars', name: 'Брусья' }
	];

	const mainTabs: { id: MainTab; label: string }[] = [
		{ id: 'routines', label: 'Комплексы' },
		{ id: 'favorites', label: 'Избранное' },
		{ id: 'exercises', label: 'Упражнения' }
	];

	// Handle visibility change for pause/resume
	function handleVisibilityChange() {
		if (document.hidden) {
			workoutStore.pauseTimer();
		} else {
			workoutStore.resumeTimer();
		}
	}

	onMount(async () => {
		// Check for active workout first
		await workoutStore.loadActiveWorkout();

		// Load data in parallel
		const [cats, exs, rts] = await Promise.all([
			api.getCategories(),
			api.getExercises(),
			api.getRoutines()
		]);
		categories = cats;
		exercises = exs;
		routines = rts;

		// Load favorites
		await favoritesStore.loadFavorites();

		// Listen for page visibility changes
		document.addEventListener('visibilitychange', handleVisibilityChange);
	});

	onDestroy(() => {
		// Clean up visibility listener
		document.removeEventListener('visibilitychange', handleVisibilityChange);
		// Pause timer when leaving page
		workoutStore.pauseTimer();
	});

	function switchMainTab(tab: MainTab) {
		activeMainTab = tab;
		telegram.hapticImpact('light');
	}

	function selectCategory(slug: string) {
		activeCategory = activeCategory === slug ? null : slug;
		telegram.hapticImpact('light');
	}

	function toggleExercise(exercise: Exercise) {
		workoutStore.toggleExerciseSelection(exercise);
	}

	async function startWorkout() {
		await workoutStore.startWorkout();
	}

	// Check if workout has any sets
	const hasSets = $derived(workoutStore.totalSets > 0);

	async function finishWorkout() {
		await workoutStore.completeWorkout();
	}

	// Cancel workout state
	let showCancelConfirm = $state(false);

	// Animation demo state - track which exercise demo is shown
	let showDemoForExercise = $state<number | null>(null);

	// Exercise info modal state
	let showInfoForExercise = $state<Exercise | null>(null);

	function toggleExerciseDemo(exerciseId: number) {
		showDemoForExercise = showDemoForExercise === exerciseId ? null : exerciseId;
		telegram.hapticImpact('light');
	}

	function openExerciseInfo(exercise: Exercise) {
		showInfoForExercise = exercise;
		telegram.hapticImpact('light');
	}

	function closeExerciseInfo() {
		showInfoForExercise = null;
	}

	// Map exercise slug to animation name - all exercises have animations
	function getAnimationSlug(exerciseSlug: string): string {
		// All slugs match directly, just return the slug
		return exerciseSlug;
	}

	function requestCancelWorkout() {
		showCancelConfirm = true;
		telegram.hapticImpact('medium');
	}

	function confirmCancelWorkout() {
		workoutStore.cancelWorkout();
		showCancelConfirm = false;
		telegram.hapticNotification('warning');
	}

	function dismissCancelConfirm() {
		showCancelConfirm = false;
	}

	// Routine handling
	function selectRoutine(routine: Routine) {
		selectedRoutine = routine;
		showRoutinePlayer = true;
		telegram.hapticImpact('medium');
	}

	function handleRoutineClose() {
		showRoutinePlayer = false;
		selectedRoutine = null;
	}

	function handleRoutineComplete() {
		showRoutinePlayer = false;
		selectedRoutine = null;
	}

	function getDifficultyStars(difficulty: number): string {
		return '\u2605'.repeat(difficulty) + '\u2606'.repeat(5 - difficulty);
	}

	// Filter modal handlers
	function openFilterModal() {
		showFilterModal = true;
		telegram.hapticImpact('light');
	}

	function handleFilterApply(filters: FilterState) {
		selectedEquipment = filters.equipment;
		selectedDifficulties = filters.difficulties;
		selectedTags = filters.tags;
	}

	function clearAllFilters() {
		selectedEquipment = [];
		selectedDifficulties = [];
		selectedTags = [];
		activeCategory = null;
		telegram.hapticImpact('light');
	}
</script>

<div class="page container">
	{#if workoutStore.isActive}
		<!-- ACTIVE WORKOUT VIEW -->
		<header class="workout-header">
			<h1>Тренировка</h1>
			<div class="timer" class:paused={workoutStore.isPaused}>
				<PixelIcon name="timer" color={workoutStore.isPaused ? "var(--text-secondary)" : "var(--pixel-accent)"} />
				<span class="timer-value">{workoutStore.formattedDuration}</span>
			</div>
		</header>

		<!-- Stats summary -->
		<PixelCard variant="accent" padding="md">
			<div class="workout-stats">
				<div class="stat">
					<span class="stat-value">{workoutStore.totalSets}</span>
					<span class="stat-label">Подходов</span>
				</div>
				<div class="stat">
					<span class="stat-value">{workoutStore.totalReps}</span>
					<span class="stat-label">Повторов</span>
				</div>
				<div class="stat">
					<span class="stat-value text-green">+{workoutStore.totalXp}</span>
					<span class="stat-label">XP</span>
				</div>
			</div>
		</PixelCard>

		<!-- Exercise cards with inline input -->
		<div class="exercise-cards">
			{#if workoutStore.selectedExercises.length > 0}
				<!-- New workout with selected exercises -->
				{#each workoutStore.selectedExercises as exercise (exercise.id)}
					{@const data = workoutStore.getExerciseData(exercise.id)}
					{@const animationSlug = getAnimationSlug(exercise.slug)}
					{@const isFavorite = favoritesStore.isFavorite(exercise.id)}
					<PixelCard padding="md">
						<div class="exercise-card">
							<div class="exercise-header">
								<span class="exercise-name">{exercise.name_ru}</span>
								<div class="exercise-header-right">
									<button
										class="favorite-toggle"
										onclick={() => favoritesStore.toggleFavorite(exercise.id)}
										title={isFavorite ? 'Убрать из избранного' : 'Добавить в избранное'}
									>
										<PixelIcon
											name={isFavorite ? 'heart' : 'heart-empty'}
											size="sm"
											color={isFavorite ? 'var(--pixel-red)' : 'var(--text-secondary)'}
										/>
									</button>
									<button
										class="info-toggle"
										onclick={() => openExerciseInfo(exercise)}
										title="Описание упражнения"
									>
										?
									</button>
									{#if animationSlug}
										<button
											class="demo-toggle"
											class:active={showDemoForExercise === exercise.id}
											onclick={() => toggleExerciseDemo(exercise.id)}
											title="Показать технику"
										>
											<PixelIcon name="play" size="sm" color={showDemoForExercise === exercise.id ? "var(--pixel-bg)" : "var(--pixel-accent)"} />
										</button>
									{/if}
									<span class="exercise-difficulty" style="color: {categoryColors[exercise.category_slug]}">
										{getDifficultyStars(exercise.difficulty)}
									</span>
								</div>
							</div>

							<!-- Animation demo -->
							{#if showDemoForExercise === exercise.id && animationSlug}
								<div class="demo-container">
									<PixelExerciseDemo exercise={animationSlug} size="md" autoplay={true} />
								</div>
							{/if}

							{#if data && data.sets.length > 0}
								<div class="sets-list">
									{#each data.sets as reps, i}
										<span class="set-badge">{reps}</span>
									{/each}
								</div>
							{/if}

							<div class="input-row">
								<PixelButton
									variant="secondary"
									size="sm"
									onclick={() => workoutStore.decrementReps(exercise.id)}
								>
									<PixelIcon name="minus" size="sm" />
								</PixelButton>
								<span class="reps-input">{data?.inputReps ?? 10}</span>
								<PixelButton
									variant="secondary"
									size="sm"
									onclick={() => workoutStore.incrementReps(exercise.id)}
								>
									<PixelIcon name="plus" size="sm" />
								</PixelButton>
								<PixelButton
									variant="success"
									size="sm"
									onclick={() => workoutStore.addSet(exercise.id)}
									disabled={workoutStore.isLoading}
								>
									<PixelIcon name="check" size="sm" />
									Подход
								</PixelButton>
							</div>
						</div>
					</PixelCard>
				{/each}
			{:else if workoutStore.session?.exercises && workoutStore.session.exercises.length > 0}
				<!-- Restored workout from server - show exercises with add set controls -->
				{#each workoutStore.session.exercises as we (we.exercise_id)}
					{@const data = workoutStore.getExerciseData(we.exercise_id)}
					<PixelCard padding="md">
						<div class="exercise-card">
							<div class="exercise-header">
								<span class="exercise-name">{we.exercise_name_ru}</span>
							</div>

							<!-- Show previous totals -->
							<div class="sets-list">
								<span class="set-badge">{we.total_reps} повт.</span>
								<span class="set-badge">{we.sets_completed} подх.</span>
								<span class="set-badge text-green">+{we.xp_earned} XP</span>
							</div>

							<!-- Add more sets -->
							<div class="input-row">
								<PixelButton
									variant="secondary"
									size="sm"
									onclick={() => workoutStore.decrementReps(we.exercise_id)}
								>
									<PixelIcon name="minus" size="sm" />
								</PixelButton>
								<span class="reps-input">{data?.inputReps ?? 10}</span>
								<PixelButton
									variant="secondary"
									size="sm"
									onclick={() => workoutStore.incrementReps(we.exercise_id)}
								>
									<PixelIcon name="plus" size="sm" />
								</PixelButton>
								<PixelButton
									variant="success"
									size="sm"
									onclick={() => workoutStore.addSet(we.exercise_id)}
									disabled={workoutStore.isLoading}
								>
									<PixelIcon name="check" size="sm" />
									Подход
								</PixelButton>
							</div>
						</div>
					</PixelCard>
				{/each}
			{:else}
				<PixelCard variant="warning" padding="md">
					<p>У вас есть активная тренировка без упражнений. Завершите или отмените её.</p>
				</PixelCard>
			{/if}
		</div>

		<!-- Finish buttons -->
		<div class="workout-actions">
			<PixelButton
				variant="success"
				size="lg"
				fullWidth
				onclick={finishWorkout}
				disabled={!hasSets || workoutStore.isLoading}
			>
				<PixelIcon name="check" />
				Завершить тренировку
			</PixelButton>
			{#if !hasSets}
				<p class="hint-text">Добавьте хотя бы один подход</p>
			{/if}
			<PixelButton variant="ghost" fullWidth onclick={requestCancelWorkout}>
				Отменить тренировку
			</PixelButton>
		</div>

		<!-- Cancel confirmation modal -->
		{#if showCancelConfirm}
			<div class="modal-overlay" onclick={dismissCancelConfirm}>
				<div class="modal-content" onclick={(e) => e.stopPropagation()}>
					<PixelCard padding="lg">
						<h3 class="modal-title">Отменить тренировку?</h3>
						<p class="modal-text">Весь прогресс тренировки будет потерян.</p>
						<div class="modal-actions">
							<PixelButton variant="danger" fullWidth onclick={confirmCancelWorkout}>
								Да, отменить
							</PixelButton>
							<PixelButton variant="secondary" fullWidth onclick={dismissCancelConfirm}>
								Продолжить тренировку
							</PixelButton>
						</div>
					</PixelCard>
				</div>
			</div>
		{/if}

	{:else}
		<!-- SELECTION VIEW -->

		<!-- Main navigation tabs -->
		<div class="main-tabs">
			{#each mainTabs as tab}
				<button
					class="main-tab"
					class:active={activeMainTab === tab.id}
					onclick={() => switchMainTab(tab.id)}
				>
					{tab.label}
					{#if tab.id === 'favorites' && favoritesStore.count > 0}
						<span class="tab-badge">{favoritesStore.count}</span>
					{/if}
				</button>
			{/each}
		</div>

		<!-- Tab content -->
		{#if activeMainTab === 'routines'}
			<!-- Routines section -->
			{#if routines.length > 0}
				<section class="tab-section">
					<div class="routine-tabs">
						{#each routineCategoryTabs as tab}
							<button
								class="routine-tab"
								class:active={activeRoutineCategory === tab.id}
								onclick={() => { activeRoutineCategory = tab.id; telegram.hapticImpact('light'); }}
							>
								{tab.name}
							</button>
						{/each}
					</div>
					<div class="routines-list">
						{#each filteredRoutines as routine}
							<PixelCard hoverable onclick={() => selectRoutine(routine)} padding="sm">
								<div class="routine-item">
									<div class="routine-info">
										<span class="routine-name">{routine.name}</span>
										<span class="routine-meta">{routine.duration_minutes} мин</span>
									</div>
									<PixelIcon name="play" size="sm" color="var(--text-secondary)" />
								</div>
							</PixelCard>
						{/each}
						{#if filteredRoutines.length === 0}
							<div class="empty-state">
								<p>Нет комплексов в этой категории</p>
							</div>
						{/if}
					</div>
				</section>
			{:else}
				<div class="empty-state">
					<PixelIcon name="play" size="lg" color="var(--text-secondary)" />
					<p>Комплексы загружаются...</p>
				</div>
			{/if}

		{:else if activeMainTab === 'favorites'}
			<!-- Favorites section -->
			<section class="tab-section">
				{#if favoriteExercises.length > 0}
					<div class="exercises-list">
						{#each favoriteExercises as exercise (exercise.id)}
							<ExerciseCard
								{exercise}
								isSelected={workoutStore.isExerciseSelected(exercise.id)}
								categoryColor={categoryColors[exercise.category_slug]}
								onSelect={() => toggleExercise(exercise)}
							/>
						{/each}
					</div>
				{:else}
					<div class="empty-state">
						<PixelIcon name="heart-empty" size="lg" color="var(--text-secondary)" />
						<p>Нет избранных упражнений</p>
						<p class="empty-hint">Нажми на сердечко, чтобы добавить</p>
					</div>
				{/if}
			</section>

		{:else}
			<!-- All exercises section -->
			<section class="tab-section">
				<!-- Filter header -->
				<div class="filter-header">
					<span class="filter-label">
						{filteredExercises.length} упражнений
					</span>
					<div class="filter-actions-row">
						{#if activeFilterCount > 0 || activeCategory}
							<button class="clear-filters-btn" onclick={clearAllFilters}>
								Сбросить
							</button>
						{/if}
						<button class="filter-btn" onclick={openFilterModal}>
							<PixelIcon name="settings" size="sm" />
							Фильтр
							{#if activeFilterCount > 0}
								<span class="filter-badge">{activeFilterCount}</span>
							{/if}
						</button>
					</div>
				</div>

				<!-- Category tabs -->
				<div class="category-tabs">
					{#each categories as category}
						<button
							class="category-tab"
							class:active={activeCategory === category.slug}
							style="--cat-color: {categoryColors[category.slug]}"
							onclick={() => selectCategory(category.slug)}
						>
							{category.name_ru}
						</button>
					{/each}
				</div>

				<!-- Exercise list -->
				<div class="exercises-list">
					{#each filteredExercises as exercise (exercise.id)}
						<ExerciseCard
							{exercise}
							isSelected={workoutStore.isExerciseSelected(exercise.id)}
							categoryColor={categoryColors[exercise.category_slug]}
							onSelect={() => toggleExercise(exercise)}
						/>
					{/each}
					{#if filteredExercises.length === 0}
						<div class="empty-state">
							<PixelIcon name="search" size="lg" color="var(--text-secondary)" />
							<p>Ничего не найдено</p>
							<PixelButton variant="ghost" onclick={clearAllFilters}>
								Сбросить фильтры
							</PixelButton>
						</div>
					{/if}
				</div>
			</section>
		{/if}

		<!-- Fixed bottom panel -->
		{#if workoutStore.selectedCount > 0}
			<div class="selection-panel">
				<div class="selection-info">
					<span class="selection-count">Выбрано: {workoutStore.selectedCount}</span>
					<button class="clear-btn" onclick={() => workoutStore.clearSelection()}>
						Очистить
					</button>
				</div>
				<PixelButton variant="primary" size="lg" fullWidth onclick={startWorkout}>
					<PixelIcon name="play" />
					Начать тренировку
				</PixelButton>
			</div>
		{/if}
	{/if}
</div>

{#if showRoutinePlayer && selectedRoutine}
	<RoutinePlayer
		routine={selectedRoutine}
		onclose={handleRoutineClose}
		oncomplete={handleRoutineComplete}
	/>
{/if}

<!-- Filter modal -->
<FilterModal
	open={showFilterModal}
	initialFilters={{
		equipment: selectedEquipment,
		difficulties: selectedDifficulties,
		tags: selectedTags
	}}
	onClose={() => showFilterModal = false}
	onApply={handleFilterApply}
/>

<!-- Exercise info modal -->
{#if showInfoForExercise}
	{@const exercise = showInfoForExercise}
	<div class="modal-overlay" onclick={closeExerciseInfo}>
		<div class="modal-content exercise-info-modal" onclick={(e) => e.stopPropagation()}>
			<PixelCard padding="lg">
				<div class="info-modal-header">
					<h3 class="modal-title">{exercise.name_ru}</h3>
					<button class="close-btn" onclick={closeExerciseInfo}>&#10005;</button>
				</div>

				<!-- Animation -->
				<div class="info-demo-container">
					<PixelExerciseDemo exercise={exercise.slug} size="lg" autoplay={true} />
				</div>

				<!-- Description -->
				<div class="info-description">
					<p>{exercise.description_ru || exercise.description || 'Описание отсутствует'}</p>
				</div>

				<PixelButton variant="secondary" fullWidth onclick={closeExerciseInfo}>
					Закрыть
				</PixelButton>
			</PixelCard>
		</div>
	</div>
{/if}

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: 180px; /* Space for fixed panel + nav */
	}

	/* Main tabs */
	.main-tabs {
		display: flex;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-md);
	}

	.main-tab {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.main-tab:hover {
		border-color: var(--pixel-accent);
	}

	.main-tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	.tab-badge {
		background: var(--pixel-bg);
		color: var(--pixel-accent);
		padding: 1px 4px;
		font-size: 8px;
		min-width: 14px;
		text-align: center;
	}

	.main-tab.active .tab-badge {
		background: var(--pixel-bg);
		color: var(--pixel-accent);
	}

	.tab-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	/* Filter header */
	.filter-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-sm);
	}

	.filter-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.filter-actions-row {
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

	/* Empty state */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-xl);
		text-align: center;
		color: var(--text-secondary);
	}

	.empty-state p {
		margin: 0;
		font-size: var(--font-size-sm);
	}

	.empty-hint {
		font-size: var(--font-size-xs) !important;
		color: var(--text-muted);
	}

	/* Favorite toggle in workout */
	.favorite-toggle {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: none;
		cursor: pointer;
		transition: transform var(--transition-fast);
	}

	.favorite-toggle:active {
		transform: scale(1.2);
	}

	.section-title {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin-bottom: var(--spacing-sm);
		color: var(--pixel-accent);
	}

	.section-subtitle {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		margin-bottom: var(--spacing-md);
	}

	/* Workout header */
	.workout-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-md);
	}

	.workout-header h1 {
		margin: 0;
	}

	.timer {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.timer-value {
		font-size: var(--font-size-lg);
		color: var(--pixel-accent);
	}

	.timer.paused .timer-value {
		color: var(--text-secondary);
		animation: blink 1s ease-in-out infinite;
	}

	@keyframes blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}

	/* Workout stats */
	.workout-stats {
		display: flex;
		justify-content: space-around;
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
	}

	.stat-value {
		font-size: var(--font-size-lg);
	}

	.stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	/* Exercise cards in workout */
	.exercise-cards {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-md);
	}

	.exercise-card {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.exercise-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.exercise-header-right {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.demo-toggle {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-card);
		border: 2px solid var(--pixel-accent);
		cursor: pointer;
		transition: background 0.15s;
	}

	.demo-toggle:hover {
		background: rgba(var(--pixel-accent-rgb), 0.2);
	}

	.demo-toggle.active {
		background: var(--pixel-accent);
	}

	.demo-container {
		display: flex;
		justify-content: center;
		padding: var(--spacing-sm) 0;
		border-bottom: 1px solid var(--border-color);
		margin-bottom: var(--spacing-xs);
	}

	.exercise-name {
		font-size: var(--font-size-sm);
	}

	.exercise-difficulty {
		font-size: var(--font-size-xs);
		letter-spacing: 1px;
	}

	.sets-list {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}

	.set-badge {
		background: var(--pixel-accent);
		color: var(--pixel-bg);
		padding: 2px 8px;
		font-size: var(--font-size-xs);
	}

	.input-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.reps-input {
		font-size: var(--font-size-lg);
		min-width: 48px;
		text-align: center;
	}

	.workout-actions {
		margin-top: var(--spacing-xl);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	/* Routines section */
	.routine-tabs {
		display: flex;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-sm);
		overflow-x: auto;
	}

	.routine-tab {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		white-space: nowrap;
	}

	.routine-tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	.routines-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.routine-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.routine-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.routine-name {
		font-size: var(--font-size-sm);
	}

	.routine-meta {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	/* Category tabs */
	.category-tabs {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-md);
	}

	.category-tab {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: 2px solid var(--cat-color);
		color: var(--cat-color);
		cursor: pointer;
	}

	.category-tab.active {
		background: var(--cat-color);
		color: var(--pixel-bg);
	}

	/* Exercises list */
	.exercises-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	/* Selection panel */
	.selection-panel {
		position: fixed;
		bottom: 72px;
		left: 0;
		right: 0;
		background: var(--pixel-bg);
		border-top: 2px solid var(--border-color);
		padding: var(--spacing-md);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		z-index: 100;
	}

	.selection-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.selection-count {
		font-size: var(--font-size-sm);
		color: var(--pixel-accent);
	}

	.clear-btn {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		background: none;
		border: none;
		color: var(--text-secondary);
		cursor: pointer;
		text-decoration: underline;
	}

	.text-green { color: var(--pixel-green); }

	.hint-text {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-align: center;
		margin: 0;
	}

	/* Modal overlay */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-md);
	}

	.modal-content {
		width: 100%;
		max-width: 320px;
	}

	.modal-title {
		margin: 0 0 var(--spacing-sm);
		font-size: var(--font-size-md);
		text-align: center;
	}

	.modal-text {
		margin: 0 0 var(--spacing-lg);
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		text-align: center;
	}

	.modal-actions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	/* Info button */
	.info-toggle {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-card);
		border: 2px solid var(--pixel-accent);
		color: var(--pixel-accent);
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		font-weight: bold;
		cursor: pointer;
		transition: background 0.15s, color 0.15s;
	}

	.info-toggle:hover {
		background: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	/* Exercise info modal */
	.exercise-info-modal {
		max-width: 360px;
		max-height: 90vh;
		overflow-y: auto;
	}

	.info-modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-md);
	}

	.info-modal-header .modal-title {
		margin: 0;
		text-align: left;
	}

	.close-btn {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: none;
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		font-size: var(--font-size-md);
		cursor: pointer;
		transition: border-color 0.15s, color 0.15s;
	}

	.close-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--pixel-accent);
	}

	.info-demo-container {
		display: flex;
		justify-content: center;
		padding: var(--spacing-md) 0;
		background: rgba(0, 0, 0, 0.2);
		margin-bottom: var(--spacing-md);
	}

	.info-description {
		margin-bottom: var(--spacing-md);
	}

	.info-description p {
		margin: 0;
		font-size: var(--font-size-sm);
		line-height: 1.6;
		color: var(--text-primary);
		white-space: pre-wrap;
	}
</style>
