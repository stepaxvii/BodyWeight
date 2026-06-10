<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon, EmptyState, PixelTabs } from '$lib/components/ui';
	import RoutinePlayer from '$lib/components/RoutinePlayer.svelte';
	import ExerciseCard from '$lib/components/ExerciseCard.svelte';
	import FilterModal from '$lib/components/FilterModal.svelte';
	import CustomRoutineEditor from '$lib/components/CustomRoutineEditor.svelte';
	import CustomRoutineList from '$lib/components/CustomRoutineList.svelte';
	import type { FilterState } from '$lib/components/FilterModal.svelte';
	import { api } from '$lib/api/client';
	import { workoutStore } from '$lib/stores/workout.svelte';
	import { favoritesStore } from '$lib/stores/favorites.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { calculateExerciseXp, calculateTimedXp } from '$lib/utils/xp';
	import type { ExerciseCategory, Exercise, Routine, RoutineCategory, CustomRoutineListItem, CustomRoutine } from '$lib/types';

	// Data
	let categories = $state<ExerciseCategory[]>([]);
	let exercises = $state<Exercise[]>([]);
	let routines = $state<Routine[]>([]);
	let customRoutines = $state<CustomRoutineListItem[]>([]);
	
	// Pagination state for exercises
	let exercisesLoading = $state(false);
	let exercisesHasMore = $state(false);
	let exercisesTotal = $state(0);
	let exercisesSkip = $state(0);
	const exercisesLimit = 30;
	let allExercisesLoaded = $state(false); // Track if all exercises are loaded for search

	// Main tab state
	type MainTab = 'routines' | 'my-routines' | 'favorites' | 'exercises';
	let activeMainTab = $state<MainTab>('routines');

	// UI state
	let activeCategory = $state<string | null>(null);
	let selectedRoutine = $state<Routine | null>(null);
	let selectedCustomRoutine = $state<CustomRoutine | null>(null);
	let showRoutinePlayer = $state(false);
	let activeRoutineCategory = $state<RoutineCategory>('morning');

	// Custom routine editor state
	let showCustomRoutineEditor = $state(false);
	let editingCustomRoutine = $state<CustomRoutine | null>(null);

	// Confirmation dialog state
	let confirmDelete = $state<{ id: number; name: string } | null>(null);

	// Page loading state
	let isPageLoading = $state(true);

	// Filter state
	let showFilterModal = $state(false);
	let selectedEquipment = $state<string[]>([]);
	let selectedDifficulties = $state<number[]>([]);
	let selectedTags = $state<string[]>([]);
	let searchQuery = $state('');

	/**
	 * Estimated XP for the active workout (preview). Mirrors the backend
	 * exactly: per exercise, XP = total reps (or total seconds for timed)
	 * × base_xp × XP_PER_REP_RATE × streak_mult, floored per exercise then
	 * summed. The number of sets never affects XP.
	 */
	const estimatedXp = $derived.by(() => {
		// CRITICAL: For active workouts, NEVER use session.total_xp_earned
		// Always recalculate from current exerciseData
		if (!workoutStore.isActive) {
			// Only for completed workouts, use the authoritative backend value
			if (workoutStore.session?.total_xp_earned) {
				return workoutStore.session.total_xp_earned;
			}
			return 0;
		}

		// For active workouts: calculate from current exerciseData
		if (workoutStore.totalSets === 0) {
			return 0;
		}

		const streak = userStore.streak;
		let total = 0;

		// CRITICAL: Convert Map to Array to ensure reactivity in Svelte 5
		const exerciseDataArray = Array.from(workoutStore.exerciseData.values());

		for (const data of exerciseDataArray) {
			if (!data.exercise || data.sets.length === 0) {
				continue;
			}

			// Sum the whole exercise's volume; set boundaries are irrelevant.
			const totalVolume = data.sets.reduce((sum, v) => sum + v, 0);
			total += data.isTimed
				? calculateTimedXp(data.exercise.base_xp, totalVolume, streak)
				: calculateExerciseXp(data.exercise.base_xp, totalVolume, streak);
		}

		return total;
	});

	// Load all exercises when any filter is active (search, equipment, difficulty, tags)
	$effect(() => {
		const hasActiveFilters =
			searchQuery.trim() ||
			selectedEquipment.length > 0 ||
			selectedDifficulties.length > 0 ||
			selectedTags.length > 0;

		if (hasActiveFilters && !allExercisesLoaded && !exercisesLoading) {
			loadAllExercisesForSearch();
		}
	});

	// Filtered exercises by all criteria
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

		// Cycling is handled by dedicated input UI (Quick record),
		// so we don't offer it in the generic workout builder.
		result = result.filter(e => e.slug !== 'cycling');

		return result;
	});

	// Favorite exercises - must load all exercises for favorites to work properly
	let favoriteExercises = $state<Exercise[]>([]);

	// Load all favorite exercises when favorites tab is active
	$effect(() => {
		async function loadFavorites() {
			if (activeMainTab === 'favorites' && favoritesStore.count > 0) {
				try {
					// Get all exercises without pagination
					const allExercises = await api.getAllExercises();
					favoriteExercises = allExercises.filter(e => favoritesStore.isFavorite(e.id));
				} catch (err) {
					console.error('Failed to load favorite exercises:', err);
				}
			}
		}
		loadFavorites();
	});

	// Filtered routines by category
	const filteredRoutines = $derived(
		routines.filter(r => r.category === activeRoutineCategory)
	);

	// Group favorite exercises by category
	const groupedFavorites = $derived.by(() => {
		const groups = new Map<string, { category: ExerciseCategory; exercises: Exercise[] }>();

		for (const exercise of favoriteExercises) {
			const category = categories.find(c => c.slug === exercise.category_slug);
			if (!category) continue;

			if (!groups.has(category.slug)) {
				groups.set(category.slug, { category, exercises: [] });
			}
			groups.get(category.slug)!.exercises.push(exercise);
		}

		return Array.from(groups.values()).sort((a, b) => a.category.sort_order - b.category.sort_order);
	});

	// Active filter count for badge
	const activeFilterCount = $derived(
		selectedEquipment.length + selectedDifficulties.length + selectedTags.length
	);

	// Category colors (by load type) — theme tokens so they track the palette
	const categoryColors: Record<string, string> = {
		strength: 'var(--pixel-red)',
		cardio: 'var(--pixel-orange)',
		static: 'var(--pixel-accent)',
		'dynamic-stretch': 'var(--pixel-green)',
		'static-stretch': 'var(--pixel-cyan)'
	};

	const routineCategoryTabs: { id: RoutineCategory; name: string }[] = [
		{ id: 'morning', name: 'Зарядка' },
		{ id: 'home', name: 'Дома' },
		{ id: 'pullup-bar', name: 'Турник' },
		{ id: 'dip-bars', name: 'Брусья' },
		{ id: 'dumbbell', name: 'Гантели' },
		{ id: 'resistance-band', name: 'Эспандер' }
	];

	const mainTabs = $derived.by(() => [
		{ id: 'routines' as const, label: 'Сеты' },
		{ id: 'my-routines' as const, label: 'Мои', badge: customRoutines.length },
		{ id: 'favorites' as const, label: 'Избранное', badge: favoritesStore.count },
		{ id: 'exercises' as const, label: 'Упражнения' }
	]);

	// Handle visibility change for pause/resume
	function handleVisibilityChange() {
		if (document.hidden) {
			workoutStore.pauseTimer();
		} else {
			workoutStore.resumeTimer();
		}
	}

	async function loadExercises(reset = false) {
		if (exercisesLoading) return;

		exercisesLoading = true;
		try {
			if (reset) {
				exercisesSkip = 0;
				exercises = [];
				allExercisesLoaded = false;
			}

			const response = await api.getExercises(activeCategory || undefined, {
				skip: exercisesSkip,
				limit: exercisesLimit
			});

			exercises = reset ? response.items : [...exercises, ...response.items];
			exercisesHasMore = response.has_more;
			exercisesTotal = response.total;
			exercisesSkip = exercises.length;

			// Mark as fully loaded if no more pages
			if (!response.has_more) {
				allExercisesLoaded = true;
			}
		} catch (error) {
			console.error('Failed to load exercises:', error);
			// Offline fallback: use exercisesStore localStorage cache
			if (exercises.length === 0) {
				try {
					const cached = localStorage.getItem('exercises_cache');
					if (cached) {
						const { data } = JSON.parse(cached);
						exercises = activeCategory
							? data.filter((e: Exercise) => e.category_slug === activeCategory)
							: data;
						exercisesHasMore = false;
						allExercisesLoaded = true;
					}
				} catch {}
			}
		} finally {
			exercisesLoading = false;
		}
	}

	// Load all exercises when search is used
	async function loadAllExercisesForSearch() {
		if (allExercisesLoaded || exercisesLoading) return;
		
		exercisesLoading = true;
		try {
			// Load all remaining exercises
			while (exercisesHasMore) {
				const response = await api.getExercises(activeCategory || undefined, {
					skip: exercisesSkip,
					limit: exercisesLimit
				});
				
				exercises = [...exercises, ...response.items];
				exercisesHasMore = response.has_more;
				exercisesSkip = exercises.length;
				
				if (!response.has_more) {
					break;
				}
			}
			allExercisesLoaded = true;
		} catch (error) {
			console.error('Failed to load all exercises:', error);
		} finally {
			exercisesLoading = false;
		}
	}

	async function loadMoreExercises() {
		await loadExercises(false);
		telegram.hapticImpact('light');
	}

	onMount(async () => {
		// Load data in parallel for faster page load
		// Each call has its own try/catch for offline resilience
		const [cats, rts, customRts] = await Promise.all([
			api.getCategories().then(data => {
				try { localStorage.setItem('cache_categories', JSON.stringify(data)); } catch {}
				return data;
			}).catch(() => {
				try {
					const cached = localStorage.getItem('cache_categories');
					return cached ? JSON.parse(cached) : [];
				} catch { return []; }
			}),
			api.getRoutines().then(data => {
				try { localStorage.setItem('cache_routines', JSON.stringify(data)); } catch {}
				return data;
			}).catch(() => {
				try {
					const cached = localStorage.getItem('cache_routines');
					return cached ? JSON.parse(cached) : [];
				} catch { return []; }
			}),
			api.getCustomRoutines().then(data => {
				try { localStorage.setItem('cache_custom_routines', JSON.stringify(data)); } catch {}
				return data;
			}).catch(() => {
				try {
					const cached = localStorage.getItem('cache_custom_routines');
					return cached ? JSON.parse(cached) : [];
				} catch { return []; }
			}),
		]);

		// These already handle errors internally
		await Promise.all([
			workoutStore.loadActiveWorkout(),
			favoritesStore.loadFavorites()
		]);

		categories = cats;
		routines = rts;
		customRoutines = customRts;

		// Load exercises with pagination
		await loadExercises();

		// After exercises are loaded, update exerciseData with exercise objects
		// This is needed for restored workouts where exercise was null
		if (workoutStore.isActive) {
			workoutStore.updateExerciseObjects(exercises);
		}

		isPageLoading = false;

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
	}

	async function selectCategory(slug: string) {
		activeCategory = activeCategory === slug ? null : slug;
		allExercisesLoaded = false; // Reset flag when changing category
		await loadExercises(true); // Reset and reload exercises
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

	// Exercise info modal state
	let showInfoForExercise = $state<Exercise | null>(null);

	function openExerciseInfo(exercise: Exercise) {
		showInfoForExercise = exercise;
		telegram.hapticImpact('light');
	}

	function closeExerciseInfo() {
		showInfoForExercise = null;
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
		selectedCustomRoutine = null;
	}

	function handleRoutineComplete() {
		showRoutinePlayer = false;
		selectedRoutine = null;
		selectedCustomRoutine = null;
	}

	// Custom routine handlers
	async function playCustomRoutine(routineId: number) {
		try {
			const routine = await api.getCustomRoutine(routineId);
			selectedCustomRoutine = routine;
			showRoutinePlayer = true;
			telegram.hapticImpact('medium');
		} catch (err) {
			console.error('Failed to load custom routine:', err);
			telegram.hapticNotification('error');
		}
	}

	async function editCustomRoutine(routineId: number) {
		try {
			const routine = await api.getCustomRoutine(routineId);
			editingCustomRoutine = routine;
			showCustomRoutineEditor = true;
			telegram.hapticImpact('light');
		} catch (err) {
			console.error('Failed to load custom routine:', err);
			telegram.hapticNotification('error');
		}
	}

	function createCustomRoutine() {
		editingCustomRoutine = null;
		showCustomRoutineEditor = true;
		telegram.hapticImpact('light');
	}

	function handleCustomRoutineSave(routine: CustomRoutine) {
		// Update list
		const existingIndex = customRoutines.findIndex(r => r.id === routine.id);

		if (existingIndex >= 0) {
			// Update existing routine
			customRoutines = customRoutines.map((r, i) =>
				i === existingIndex ? {
					id: routine.id,
					name: routine.name,
					routine_type: routine.routine_type,
					duration_minutes: routine.duration_minutes,
					exercises_count: routine.exercises.length
				} : r
			);
		} else {
			// Add new routine
			customRoutines = [{
				id: routine.id,
				name: routine.name,
				routine_type: routine.routine_type,
				duration_minutes: routine.duration_minutes,
				exercises_count: routine.exercises.length
			}, ...customRoutines];
		}

		showCustomRoutineEditor = false;
		editingCustomRoutine = null;
	}

	function handleCustomRoutineDelete(routineId: number, routineName: string) {
		confirmDelete = { id: routineId, name: routineName };
		telegram.hapticImpact('light');
	}

	function cancelDelete() {
		confirmDelete = null;
	}

	async function confirmDeleteRoutine() {
		if (!confirmDelete) return;

		telegram.hapticImpact('medium');
		try {
			await api.deleteCustomRoutine(confirmDelete.id);
			customRoutines = customRoutines.filter(r => r.id !== confirmDelete!.id);
			telegram.hapticNotification('success');
		} catch (err) {
			telegram.hapticNotification('error');
			console.error('Failed to delete routine:', err);
		} finally {
			confirmDelete = null;
		}
	}

	function closeCustomRoutineEditor() {
		showCustomRoutineEditor = false;
		editingCustomRoutine = null;
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

	async function clearAllFilters() {
		selectedEquipment = [];
		selectedDifficulties = [];
		selectedTags = [];
		activeCategory = null;
		searchQuery = '';
		allExercisesLoaded = false; // Reset flag when clearing
		await loadExercises(true); // Reset and reload exercises
		telegram.hapticImpact('light');
	}
</script>

<div class="page container">
	{#if isPageLoading}
		<!-- Loading state -->
		<div class="loading-container">
			<div class="loading-spinner"></div>
			<p class="loading-text">Загрузка...</p>
		</div>
	{:else if workoutStore.isActive}
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
					{#if !workoutStore.isActive && workoutStore.session?.total_xp_earned}
						<!-- Completed workout - show actual XP from backend -->
						<span class="stat-value text-green">+{workoutStore.totalXp}</span>
					{:else if workoutStore.totalSets === 0}
						<!-- No sets yet - show dash -->
						<span class="stat-value text-green">—</span>
					{:else if workoutStore.isActive && estimatedXp > 0}
						<!-- Active workout with sets - show estimated XP -->
						<span class="stat-value text-green">~{estimatedXp}</span>
					{:else}
						<span class="stat-value text-green">—</span>
					{/if}
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
									<span class="exercise-difficulty" style="color: {categoryColors[exercise.category_slug]}">
										{getDifficultyStars(exercise.difficulty)}
									</span>
								</div>
							</div>

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
					{@const fullExercise = exercises.find(e => e.slug === we.exercise_slug)}
					{@const isFavorite = favoritesStore.isFavorite(we.exercise_id)}
					<PixelCard padding="md">
						<div class="exercise-card">
							<div class="exercise-header">
								<span class="exercise-name">{we.exercise_name_ru}</span>
								<div class="exercise-header-right">
									<button
										class="favorite-toggle"
										onclick={() => favoritesStore.toggleFavorite(we.exercise_id)}
										title={isFavorite ? 'Убрать из избранного' : 'Добавить в избранное'}
									>
										<PixelIcon
											name={isFavorite ? 'heart' : 'heart-empty'}
											size="sm"
											color={isFavorite ? 'var(--pixel-red)' : 'var(--text-secondary)'}
										/>
									</button>
									{#if fullExercise}
										<button
											class="info-toggle"
											onclick={() => openExerciseInfo(fullExercise)}
											title="Описание упражнения"
										>
											?
										</button>
									{/if}
								</div>
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
		<PixelTabs tabs={mainTabs} activeTab={activeMainTab} onTabChange={switchMainTab} />

		<!-- Tab content -->
		{#if activeMainTab === 'routines'}
			<!-- Routines section -->
			{#if routines.length > 0}
				<section class="tab-section">
					<PixelTabs
						tabs={routineCategoryTabs.map(t => ({ id: t.id, label: t.name }))}
						activeTab={activeRoutineCategory}
						onTabChange={(id) => activeRoutineCategory = id}
					/>
					<div class="routines-list anim-rows">
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
							<EmptyState message="Нет сетов в этой категории" />
						{/if}
					</div>
				</section>
			{:else}
				<EmptyState icon="play" message="Сеты загружаются..." />
			{/if}

		{:else if activeMainTab === 'my-routines'}
			<!-- My custom routines section -->
			<section class="tab-section">
				<CustomRoutineList
					routines={customRoutines}
					onplay={playCustomRoutine}
					onedit={editCustomRoutine}
					ondelete={handleCustomRoutineDelete}
					oncreate={createCustomRoutine}
				/>
			</section>

		{:else if activeMainTab === 'favorites'}
			<!-- Favorites section -->
			<section class="tab-section">
				{#if favoriteExercises.length > 0}
					{#each groupedFavorites as group (group.category.slug)}
						<div class="category-group">
							<div class="category-group-header">
								<span class="category-group-title" style="color: {categoryColors[group.category.slug]}">
									{group.category.name_ru}
								</span>
								<span class="category-group-count">
									{group.exercises.length}
								</span>
							</div>
							<div class="exercises-list anim-rows">
								{#each group.exercises as exercise (exercise.id)}
									<ExerciseCard
										{exercise}
										isSelected={workoutStore.isExerciseSelected(exercise.id)}
										categoryColor={categoryColors[exercise.category_slug]}
										onSelect={() => toggleExercise(exercise)}
										onInfoClick={() => openExerciseInfo(exercise)}
									/>
								{/each}
							</div>
						</div>
					{/each}
				{:else}
					<EmptyState
						icon="heart-empty"
						message="Нет избранных упражнений"
						hint="Нажми на сердечко, чтобы добавить"
					/>
				{/if}
			</section>

		{:else if activeMainTab === 'exercises'}
			<!-- All exercises section -->
			<section class="tab-section">
				<!-- Filter header -->
				<div class="filter-header">
					<span class="filter-label">
						{filteredExercises.length} / {exercisesTotal || filteredExercises.length} упражнений
					</span>
					<div class="filter-actions-row">
						{#if activeFilterCount > 0 || activeCategory || searchQuery}
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
				<div class="exercises-list anim-rows">
					{#each filteredExercises as exercise (exercise.id)}
						<ExerciseCard
							{exercise}
							isSelected={workoutStore.isExerciseSelected(exercise.id)}
							categoryColor={categoryColors[exercise.category_slug]}
							onSelect={() => toggleExercise(exercise)}
							onInfoClick={() => openExerciseInfo(exercise)}
						/>
					{/each}
					{#if filteredExercises.length === 0 && !exercisesLoading}
						<EmptyState
							icon="search"
							message="Ничего не найдено"
							buttonText="Сбросить фильтры"
							onButtonClick={clearAllFilters}
						/>
					{/if}

					{#if exercisesHasMore && filteredExercises.length > 0 && !searchQuery && selectedEquipment.length === 0 && selectedDifficulties.length === 0 && selectedTags.length === 0}
						<div class="load-more-container">
							<PixelButton
								variant="secondary"
								onclick={loadMoreExercises}
								disabled={exercisesLoading}
								fullWidth
							>
								{#if exercisesLoading}
									Загрузка...
								{:else}
									Загрузить ещё
								{/if}
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
		{exercises}
		onclose={handleRoutineClose}
		oncomplete={handleRoutineComplete}
	/>
{/if}

{#if showRoutinePlayer && selectedCustomRoutine}
	{@const convertedRoutine = {
		slug: `custom-${selectedCustomRoutine.id}`,
		name: selectedCustomRoutine.name,
		description: selectedCustomRoutine.description || '',
		category: selectedCustomRoutine.routine_type === 'morning' ? 'morning' as const : 'home' as const,
		duration_minutes: selectedCustomRoutine.duration_minutes,
		difficulty: 2 as const,
		exercises: selectedCustomRoutine.exercises.map(ex => ({
			slug: ex.exercise_slug,
			reps: ex.target_reps,
			duration: ex.target_duration
		}))
	}}
	<RoutinePlayer
		routine={convertedRoutine}
		{exercises}
		onclose={handleRoutineClose}
		oncomplete={handleRoutineComplete}
	/>
{/if}

{#if showCustomRoutineEditor}
	<CustomRoutineEditor
		{categories}
		editingRoutine={editingCustomRoutine}
		onclose={closeCustomRoutineEditor}
		onsave={handleCustomRoutineSave}
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

<!-- Delete confirmation modal -->
{#if confirmDelete}
	<div class="modal-overlay" onclick={cancelDelete}>
		<div class="modal-dialog" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<PixelIcon name="warning" size="lg" color="var(--pixel-yellow)" />
			</div>
			<div class="modal-body">
				<p class="modal-title">Удалить сет?</p>
				<p class="modal-text">
					Вы уверены, что хотите удалить сет "{confirmDelete.name}"?
				</p>
			</div>
			<div class="modal-actions">
				<PixelButton variant="secondary" onclick={cancelDelete}>
					Отмена
				</PixelButton>
				<PixelButton variant="danger" onclick={confirmDeleteRoutine}>
					Удалить
				</PixelButton>
			</div>
		</div>
	</div>
{/if}

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
		border: var(--border-width) solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
	}

	.filter-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.filter-badge {
		background: var(--pixel-accent);
		color: var(--on-accent);
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

	/* Search box */
	.search-box {
		position: relative;
		display: flex;
		align-items: center;
		margin-bottom: var(--spacing-md);
	}

	.search-input {
		width: 100%;
		padding: var(--spacing-sm) var(--spacing-md);
		padding-right: 40px;
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
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
		color: var(--on-accent);
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
		border: var(--border-width) solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		white-space: nowrap;
	}

	.routine-tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--on-accent);
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
		border: var(--border-width) solid var(--cat-color);
		color: var(--cat-color);
		cursor: pointer;
	}

	.category-tab.active {
		background: var(--cat-color);
		color: var(--on-accent);
	}

	/* Exercises list */
	.load-more-container {
		margin-top: var(--spacing-md);
		padding: 0 var(--spacing-md);
	}

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
		border-top: var(--border-width) solid var(--border-color);
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
		border: var(--border-width) solid var(--pixel-accent);
		color: var(--pixel-accent);
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		font-weight: bold;
		cursor: pointer;
		transition: background 0.15s, color 0.15s;
	}

	.info-toggle:hover {
		background: var(--pixel-accent);
		color: var(--on-accent);
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
		border: var(--border-width) solid var(--border-color);
		color: var(--text-secondary);
		font-size: var(--font-size-md);
		cursor: pointer;
		transition: border-color 0.15s, color 0.15s;
	}

	.close-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--pixel-accent);
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

	/* Loading state */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 50vh;
		gap: var(--spacing-md);
	}

	.loading-spinner {
		width: 32px;
		height: 32px;
		border: 3px solid var(--border-color);
		border-top-color: var(--pixel-accent);
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.loading-text {
		color: var(--text-secondary);
		font-size: var(--font-size-sm);
	}

	/* Delete Confirmation Modal */
	.modal-dialog {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		max-width: 320px;
		width: 100%;
		animation: modal-appear 0.2s ease-out;
	}

	@keyframes modal-appear {
		from {
			opacity: 0;
			transform: scale(0.9);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	.modal-header {
		display: flex;
		justify-content: center;
		padding: var(--spacing-md);
		background: var(--pixel-bg-dark);
		border-bottom: var(--border-width) solid var(--border-color);
	}

	.modal-body {
		padding: var(--spacing-md);
		text-align: center;
	}

	.modal-body .modal-title {
		font-family: var(--font-pixel);
		font-size: var(--font-size-md);
		margin-bottom: var(--spacing-sm);
		color: var(--text-primary);
	}

	.modal-text {
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		line-height: 1.4;
	}

	.modal-actions {
		display: flex;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		border-top: var(--border-width) solid var(--border-color);
	}

	.modal-actions > :global(*) {
		flex: 1;
	}

	/* Category Groups */
	.category-group {
		margin-bottom: var(--spacing-xl);
	}

	.category-group:last-child {
		margin-bottom: 0;
	}

	.category-group-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-sm) var(--spacing-xs);
		margin-bottom: var(--spacing-sm);
		border-bottom: var(--border-width) solid var(--border-color);
	}

	.category-group-title {
		font-family: var(--font-pixel);
		font-size: var(--font-size-md);
		font-weight: bold;
		text-transform: uppercase;
	}

	.category-group-count {
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		background: var(--pixel-bg-dark);
		padding: 2px 8px;
		border: var(--border-width) solid var(--border-color);
	}
</style>
