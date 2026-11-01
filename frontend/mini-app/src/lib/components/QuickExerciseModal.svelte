<script lang="ts">
	import { PixelButton, PixelCard, PixelModal, PixelIcon } from '$lib/components/ui';
	import { api, newClientRequestId } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { favoritesStore } from '$lib/stores/favorites.svelte';
	import { exercisesStore } from '$lib/stores/exercises.svelte';
	import { calculateCyclingXp, calculateRunningXp, calculateWalkingXp, calculateExerciseXp, calculateTimedXp, xpPerRep } from '$lib/utils/xp';
	import { getTagName } from '$lib/utils';
	import type { Exercise, EquipmentType, ExerciseCategory } from '$lib/types';
	import { onMount } from 'svelte';

	interface Props {
		open?: boolean;
		onclose?: () => void;
		onsave?: (xp: number, coins: number) => void;
	}

	let { open = $bindable(false), onclose, onsave }: Props = $props();

	type Step = 'mode' | 'exercise' | 'input' | 'filters' | 'cycling-input' | 'running-input' | 'walking-input';
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
	let runningDistanceKm = $state(5.0);
	let runningDurationMin = $state(30);
	let walkingSteps = $state(10000);
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
		{ id: 'bike', label: 'Велосипед' },
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

		// Cycling, running and walking are handled by dedicated quick-flows,
		// not by the generic reps/sets UI.
		result = result.filter(e => e.slug !== 'cycling' && e.slug !== 'running' && e.slug !== 'walking');

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
		// Cycling/walking use dedicated flows,
		// so route them explicitly even if they appear in some lists (e.g. cached favorites).
		if (ex.slug === 'cycling') {
			step = 'cycling-input';
			selectedExercise = null;
			telegram.hapticImpact('light');
			return;
		}
		if (ex.slug === 'running') {
			step = 'running-input';
			selectedExercise = null;
			telegram.hapticImpact('light');
			return;
		}
		if (ex.slug === 'walking') {
			step = 'walking-input';
			selectedExercise = null;
			telegram.hapticImpact('light');
			return;
		}

		selectedExercise = ex;
		step = 'input';
		telegram.hapticImpact('light');
	}

	function selectCycling() {
		step = 'cycling-input';
		telegram.hapticImpact('light');
	}

	function selectRunning() {
		step = 'running-input';
		telegram.hapticImpact('light');
	}

	function selectWalking() {
		step = 'walking-input';
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
		} else if (step === 'running-input') {
			step = 'mode';
		} else if (step === 'walking-input') {
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
		runningDistanceKm = 5.0;
		runningDurationMin = 30;
		walkingSteps = 10000;
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
			client_request_id: newClientRequestId(),
		};

		try {
			const response = await api.submitWorkout(workoutData);
			const completed = response.workout;
			// Reflect earned XP/coins optimistically and refresh in the background
			// so we don't block on a second round-trip before closing.
			userStore.addXp(completed.total_xp_earned);
			userStore.addCoins(completed.total_coins_earned);
			void userStore.loadUser();
			onsave?.(completed.total_xp_earned, completed.total_coins_earned);
			handleClose();
		} catch (err) {
			// Offline: save to pending queue for later sync
			if (!navigator.onLine) {
				savePendingWorkout(workoutData);
				telegram.hapticNotification('success');
				onsave?.(
					timeBased
						? calculateTimedXp(selectedExercise.base_xp, duration, userStore.streak)
						: calculateExerciseXp(selectedExercise.base_xp, reps, userStore.streak),
					0
				);
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
			completed_at: new Date().toISOString(),
			client_request_id: newClientRequestId()
		};

		try {
			const response = await api.submitWorkout(workoutData);
			const completed = response.workout;
			// Reflect earned XP/coins optimistically and refresh in the background
			// so we don't block on a second round-trip before closing.
			userStore.addXp(completed.total_xp_earned);
			userStore.addCoins(completed.total_coins_earned);
			void userStore.loadUser();
			onsave?.(completed.total_xp_earned, completed.total_coins_earned);
			handleClose();
		} catch (err) {
			if (!navigator.onLine) {
				savePendingWorkout(workoutData);
				telegram.hapticNotification('success');
				onsave?.(calculateCyclingXp(cyclingDistanceKm, cyclingDurationMin, userStore.streak), 0);
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
		calculateCyclingXp(cyclingDistanceKm, cyclingDurationMin, userStore.streak)
	));

	const runningSpeedKmh = $derived.by(() => {
		if (runningDurationMin <= 0) return 0;
		return runningDistanceKm / (runningDurationMin / 60);
	});

	const runningEstimatedXp = $derived.by(() => (
		calculateRunningXp(runningDistanceKm, runningDurationMin, userStore.streak)
	));

	async function handleSaveRunning() {
		if (isSubmitting) return;
		if (runningDistanceKm <= 0 || runningDurationMin < 3) {
			telegram.hapticNotification('error');
			return;
		}

		isSubmitting = true;
		telegram.hapticNotification('success');

		const workoutData = {
			duration_seconds: runningDurationMin * 60,
			exercises: [{
				exercise_slug: 'running',
				sets: [Math.max(1, Math.round(runningDistanceKm * 10))], // 100m units
				is_timed: false,
				distance_km: runningDistanceKm,
				duration_minutes: runningDurationMin
			}],
			completed_at: new Date().toISOString(),
			client_request_id: newClientRequestId()
		};

		try {
			const response = await api.submitWorkout(workoutData);
			const completed = response.workout;
			userStore.addXp(completed.total_xp_earned);
			userStore.addCoins(completed.total_coins_earned);
			void userStore.loadUser();
			onsave?.(completed.total_xp_earned, completed.total_coins_earned);
			handleClose();
		} catch (err) {
			if (!navigator.onLine) {
				savePendingWorkout(workoutData);
				telegram.hapticNotification('success');
				onsave?.(calculateRunningXp(runningDistanceKm, runningDurationMin, userStore.streak), 0);
				handleClose();
			} else {
				console.error('Failed to save running activity:', err);
				telegram.hapticNotification('error');
			}
		} finally {
			isSubmitting = false;
		}
	}

	const walkingEstimatedXp = $derived.by(() => calculateWalkingXp(walkingSteps, userStore.streak));

	async function handleSaveWalking() {
		if (isSubmitting) return;
		if (walkingSteps <= 0) {
			telegram.hapticNotification('error');
			return;
		}

		isSubmitting = true;
		telegram.hapticNotification('success');

		const workoutData = {
			duration_seconds: 0,
			exercises: [{
				exercise_slug: 'walking',
				sets: [walkingSteps],
				is_timed: false,
				steps: walkingSteps
			}],
			completed_at: new Date().toISOString(),
			client_request_id: newClientRequestId()
		};

		try {
			const response = await api.submitWorkout(workoutData);
			const completed = response.workout;
			// Reflect earned XP/coins optimistically and refresh in the background
			// so we don't block on a second round-trip before closing.
			userStore.addXp(completed.total_xp_earned);
			userStore.addCoins(completed.total_coins_earned);
			void userStore.loadUser();
			onsave?.(completed.total_xp_earned, completed.total_coins_earned);
			handleClose();
		} catch (err) {
			if (!navigator.onLine) {
				savePendingWorkout(workoutData);
				telegram.hapticNotification('success');
				onsave?.(calculateWalkingXp(walkingSteps, userStore.streak), 0);
				handleClose();
			} else {
				console.error('Failed to save walking activity:', err);
				telegram.hapticNotification('error');
			}
		} finally {
			isSubmitting = false;
		}
	}

	function savePendingWorkout(data: Parameters<typeof api.submitWorkout>[0]) {
		try {
			const pending = JSON.parse(localStorage.getItem('pending_workouts') || '[]');
			pending.push({ data, timestamp: Date.now() });
			localStorage.setItem('pending_workouts', JSON.stringify(pending));
		} catch (e) {
			console.error('Failed to save pending workout:', e);
		}
	}

	// Ручной ввод значений: во время набора применяем число с верхним капом
	// (нижний не зажимаем, чтобы «3» по пути к «30» не прыгала на минимум),
	// нижнюю границу приводим на blur. Пустое/недопечатанное поле состояние
	// не трогает — в нём остаётся последнее валидное значение.
	function typedInt(e: Event): number | null {
		const v = parseInt((e.currentTarget as HTMLInputElement).value.replace(/\D/g, ''), 10);
		return Number.isNaN(v) ? null : v;
	}

	function typeRepsOrDuration(e: Event) {
		const v = typedInt(e);
		if (v === null) return;
		if (isTimeBased(selectedExercise!)) duration = Math.min(300, v);
		else reps = Math.min(999, v);
	}
	function blurRepsOrDuration(e: Event) {
		if (isTimeBased(selectedExercise!)) duration = Math.max(5, duration);
		else reps = Math.max(1, reps);
		(e.currentTarget as HTMLInputElement).value = String(isTimeBased(selectedExercise!) ? duration : reps);
	}

	function typeCyclingKm(e: Event) {
		const cleaned = (e.currentTarget as HTMLInputElement).value
			.replace(',', '.')
			.replace(/[^\d.]/g, '');
		// «12.» — незаконченный ввод дроби, ждём следующую цифру
		if (!cleaned || cleaned.endsWith('.')) return;
		const v = parseFloat(cleaned);
		if (!Number.isNaN(v)) cyclingDistanceKm = Math.min(300, v);
	}
	function blurCyclingKm(e: Event) {
		cyclingDistanceKm = Math.max(0.5, +cyclingDistanceKm.toFixed(1));
		(e.currentTarget as HTMLInputElement).value = String(cyclingDistanceKm);
	}

	function typeCyclingMin(e: Event) {
		const v = typedInt(e);
		if (v !== null) cyclingDurationMin = Math.min(600, v);
	}
	function blurCyclingMin(e: Event) {
		cyclingDurationMin = Math.max(5, cyclingDurationMin);
		(e.currentTarget as HTMLInputElement).value = String(cyclingDurationMin);
	}

	function typeRunningKm(e: Event) {
		const cleaned = (e.currentTarget as HTMLInputElement).value
			.replace(',', '.')
			.replace(/[^\d.]/g, '');
		if (!cleaned || cleaned.endsWith('.')) return;
		const v = parseFloat(cleaned);
		if (!Number.isNaN(v)) runningDistanceKm = Math.min(300, v);
	}
	function blurRunningKm(e: Event) {
		runningDistanceKm = Math.max(0.1, +runningDistanceKm.toFixed(1));
		(e.currentTarget as HTMLInputElement).value = String(runningDistanceKm);
	}

	function typeRunningMin(e: Event) {
		const v = typedInt(e);
		if (v !== null) runningDurationMin = Math.min(600, v);
	}
	function blurRunningMin(e: Event) {
		runningDurationMin = Math.max(3, runningDurationMin);
		(e.currentTarget as HTMLInputElement).value = String(runningDurationMin);
	}

	function typeWalkingSteps(e: Event) {
		const v = typedInt(e);
		if (v !== null) walkingSteps = Math.min(200000, v);
	}
	function blurWalkingSteps(e: Event) {
		walkingSteps = Math.max(100, walkingSteps);
		(e.currentTarget as HTMLInputElement).value = String(walkingSteps);
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
	<div class="ql">
		{#if step === 'mode'}
			<div class="ql-modes">
				<button class="ql-mode" onclick={selectRunning}>
					<span class="slot slot--md"><PixelIcon name="run" size="md" color="var(--gold)" /></span>
					<span class="ql-mode__l">Бег · дистанция</span>
					<PixelIcon name="chevron" size="sm" color="var(--muted)" class="ql-chev" />
				</button>
				<button class="ql-mode" onclick={selectCycling}>
					<span class="slot slot--md"><PixelIcon name="bike" size="md" color="var(--green)" /></span>
					<span class="ql-mode__l">Поездка на велосипеде</span>
					<PixelIcon name="chevron" size="sm" color="var(--muted)" class="ql-chev" />
				</button>
				<button class="ql-mode" onclick={selectWalking}>
					<span class="slot slot--md"><PixelIcon name="steps" size="md" color="var(--accent)" /></span>
					<span class="ql-mode__l">Ходьба · шаги</span>
					<PixelIcon name="chevron" size="sm" color="var(--muted)" class="ql-chev" />
				</button>
				<button class="ql-mode" onclick={() => selectMode('favorites')}>
					<span class="slot slot--md"><PixelIcon name="heart" size="md" color="var(--danger)" /></span>
					<span class="ql-mode__l">Избранные упражнения</span>
					{#if favoritesStore.count > 0}
						<span class="ql-mode__badge">{favoritesStore.count}</span>
					{:else}
						<PixelIcon name="chevron" size="sm" color="var(--muted)" class="ql-chev" />
					{/if}
				</button>
				<button class="ql-mode" onclick={() => selectMode('all')}>
					<span class="slot slot--md"><PixelIcon name="dumbbell" size="md" color="var(--accent)" /></span>
					<span class="ql-mode__l">Все упражнения</span>
					<PixelIcon name="chevron" size="sm" color="var(--muted)" class="ql-chev" />
				</button>
			</div>
		{:else if step === 'exercise'}
			<div class="ql-back">
				<button class="ql-backbtn" onclick={goBack} aria-label="Назад"><PixelIcon name="arrowleft" size="sm" /></button>
				<span class="ql-back__t">{exerciseMode === 'favorites' ? 'Избранные' : 'Все упражнения'}</span>
			</div>
			<div class="ql-search">
				<PixelIcon name="search" size="sm" color="var(--muted)" />
				<input class="ql-search__in" placeholder="Поиск упражнений..." bind:value={searchQuery} />
				<button class="ql-search__filter" onclick={openFilters} aria-label="Фильтр">
					<PixelIcon name="gear" size="sm" />
					{#if activeFilterCount > 0}<span class="ql-fbadge">{activeFilterCount}</span>{/if}
				</button>
			</div>
			{#if exerciseMode === 'all' && categories.length > 0}
				<div class="ql-cats">
					<button class="ql-pill" class:is-active={selectedCategory === null} onclick={() => (selectedCategory = null)}>Все</button>
					{#each categories as cat}
						<button class="ql-pill" class:is-active={selectedCategory === cat.slug} onclick={() => toggleCategory(cat.slug)}>{cat.name_ru}</button>
					{/each}
				</div>
			{/if}
			<div class="ql-list">
				{#each displayedExercises as ex}
					<button class="ql-ex" onclick={() => selectExercise(ex)}>
						<span class="ql-ex__n">{ex.name_ru}</span>
						<span class="ql-ex__xp">+{Number(xpPerRep(ex.base_xp).toFixed(1))} XP/{isTimeBased(ex) ? '10с' : 'повт'}</span>
					</button>
				{/each}
				{#if displayedExercises.length === 0}
					<p class="ql-empty">
						{#if exerciseMode === 'favorites'}Нет избранных упражнений{:else if searchQuery || activeFilterCount > 0}Ничего не найдено{:else}Нет упражнений{/if}
					</p>
				{/if}
			</div>
		{:else if step === 'filters'}
			<div class="ql-back">
				<button class="ql-backbtn" onclick={goBack} aria-label="Назад"><PixelIcon name="arrowleft" size="sm" /></button>
				<span class="ql-back__t">Фильтры</span>
			</div>
			<div class="filter-sections">
				<div class="filter-section">
					<h4 class="filter-section-title">Категория</h4>
					<div class="filter-options">
						<button class="ql-pill" class:is-active={selectedCategory === null} onclick={() => (selectedCategory = null)}>Все</button>
						{#each categories as cat}
							<button class="ql-pill" class:is-active={selectedCategory === cat.slug} onclick={() => toggleCategory(cat.slug)}>{cat.name_ru}</button>
						{/each}
					</div>
				</div>
				<div class="filter-section">
					<h4 class="filter-section-title">Оборудование</h4>
					<div class="filter-options">
						{#each EQUIPMENT_OPTIONS as eq}
							<button class="ql-pill" class:is-active={selectedEquipment.includes(eq.id)} onclick={() => toggleEquipment(eq.id)}>{eq.label}</button>
						{/each}
					</div>
				</div>
				<div class="filter-section">
					<h4 class="filter-section-title">Сложность</h4>
					<div class="filter-options">
						{#each [1, 2, 3, 4, 5] as level}
							<button class="ql-pill" class:is-active={selectedDifficulties.includes(level)} onclick={() => toggleDifficulty(level)}>{'★'.repeat(level) + '☆'.repeat(5 - level)}</button>
						{/each}
					</div>
				</div>
				<div class="filter-section">
					<h4 class="filter-section-title">Группы мышц</h4>
					<div class="filter-options">
						{#each MUSCLE_TAG_IDS as tagId}
							<button class="ql-pill" class:is-active={selectedTags.includes(tagId)} onclick={() => toggleTag(tagId)}>{getTagName(tagId)}</button>
						{/each}
					</div>
				</div>
			</div>
			<div class="ql-filteractions">
				<PixelButton variant="secondary" fullWidth onclick={clearFilters}>Сбросить все</PixelButton>
				<PixelButton variant="primary" fullWidth onclick={goBack}>Применить</PixelButton>
			</div>
		{:else if step === 'input' && selectedExercise}
			<div class="ql-back">
				<button class="ql-backbtn" onclick={goBack} aria-label="Назад"><PixelIcon name="arrowleft" size="sm" /></button>
				<span class="ql-back__t">{selectedExercise.name_ru}</span>
			</div>
			<span class="ql-label">{isTimeBased(selectedExercise!) ? 'Длительность (секунды)' : 'Количество повторений'}</span>
			<div class="qty">
				<button class="qty__btn" onclick={() => adjustValue(isTimeBased(selectedExercise!) ? -10 : -5)} aria-label="Меньше"><PixelIcon name="minus" size="sm" /></button>
				<div class="qty__mid"><input class="qty__v qty__in" type="text" inputmode="numeric" maxlength="3" value={String(isTimeBased(selectedExercise!) ? duration : reps)} oninput={typeRepsOrDuration} onblur={blurRepsOrDuration} aria-label={isTimeBased(selectedExercise!) ? 'Секунды' : 'Повторения'} /><span class="qty__u">{isTimeBased(selectedExercise!) ? 'сек' : 'повт.'}</span></div>
				<button class="qty__btn" onclick={() => adjustValue(isTimeBased(selectedExercise!) ? 10 : 5)} aria-label="Больше"><PixelIcon name="plus" size="sm" /></button>
			</div>
			<PixelButton variant="success" size="lg" fullWidth loading={isSubmitting} onclick={handleSave}><PixelIcon name="check" /> Записать</PixelButton>
		{:else if step === 'cycling-input'}
			<div class="ql-back">
				<button class="ql-backbtn" onclick={goBack} aria-label="Назад"><PixelIcon name="arrowleft" size="sm" /></button>
				<span class="ql-back__t">Велосипед</span>
			</div>
			<span class="ql-label">Дистанция</span>
			<div class="qty">
				<button class="qty__btn" onclick={() => (cyclingDistanceKm = Math.max(0.5, +(cyclingDistanceKm - 0.5).toFixed(1)))} aria-label="Меньше"><PixelIcon name="minus" size="sm" /></button>
				<div class="qty__mid"><input class="qty__v qty__in" type="text" inputmode="decimal" maxlength="5" value={String(cyclingDistanceKm)} oninput={typeCyclingKm} onblur={blurCyclingKm} aria-label="Дистанция, км" /><span class="qty__u">км</span></div>
				<button class="qty__btn" onclick={() => (cyclingDistanceKm = +(cyclingDistanceKm + 0.5).toFixed(1))} aria-label="Больше"><PixelIcon name="plus" size="sm" /></button>
			</div>
			<span class="ql-label">Время</span>
			<div class="qty">
				<button class="qty__btn" onclick={() => (cyclingDurationMin = Math.max(5, cyclingDurationMin - 1))} aria-label="Меньше"><PixelIcon name="minus" size="sm" /></button>
				<div class="qty__mid"><input class="qty__v qty__in" type="text" inputmode="numeric" maxlength="3" value={String(cyclingDurationMin)} oninput={typeCyclingMin} onblur={blurCyclingMin} aria-label="Время, минуты" /><span class="qty__u">мин</span></div>
				<button class="qty__btn" onclick={() => (cyclingDurationMin = cyclingDurationMin + 1)} aria-label="Больше"><PixelIcon name="plus" size="sm" /></button>
			</div>
			<div class="ql-sum"><span>Ср. скорость: {cyclingSpeedKmh.toFixed(1)} км/ч</span><span class="ql-sum__xp">+{cyclingEstimatedXp} XP</span></div>
			<PixelButton variant="success" size="lg" fullWidth loading={isSubmitting} onclick={handleSaveCycling}><PixelIcon name="check" /> Записать поездку</PixelButton>
			{:else if step === 'running-input'}
				<div class="ql-back">
					<button class="ql-backbtn" onclick={goBack} aria-label="Назад"><PixelIcon name="arrowleft" size="sm" /></button>
					<span class="ql-back__t">Бег</span>
				</div>
				<span class="ql-label">Дистанция</span>
				<div class="qty">
					<button class="qty__btn" onclick={() => (runningDistanceKm = Math.max(0.1, +(runningDistanceKm - 0.5).toFixed(1)))} aria-label="Меньше"><PixelIcon name="minus" size="sm" /></button>
					<div class="qty__mid"><input class="qty__v qty__in" type="text" inputmode="decimal" maxlength="5" value={String(runningDistanceKm)} oninput={typeRunningKm} onblur={blurRunningKm} aria-label="Дистанция, км" /><span class="qty__u">км</span></div>
					<button class="qty__btn" onclick={() => (runningDistanceKm = +(runningDistanceKm + 0.5).toFixed(1))} aria-label="Больше"><PixelIcon name="plus" size="sm" /></button>
				</div>
				<span class="ql-label">Время</span>
				<div class="qty">
					<button class="qty__btn" onclick={() => (runningDurationMin = Math.max(3, runningDurationMin - 1))} aria-label="Меньше"><PixelIcon name="minus" size="sm" /></button>
					<div class="qty__mid"><input class="qty__v qty__in" type="text" inputmode="numeric" maxlength="3" value={String(runningDurationMin)} oninput={typeRunningMin} onblur={blurRunningMin} aria-label="Время, минуты" /><span class="qty__u">мин</span></div>
					<button class="qty__btn" onclick={() => (runningDurationMin = runningDurationMin + 1)} aria-label="Больше"><PixelIcon name="plus" size="sm" /></button>
				</div>
				<div class="ql-sum"><span>Ср. темп: {runningSpeedKmh.toFixed(1)} км/ч</span><span class="ql-sum__xp">+{runningEstimatedXp} XP</span></div>
				<PixelButton variant="success" size="lg" fullWidth loading={isSubmitting} onclick={handleSaveRunning}><PixelIcon name="check" /> Записать пробежку</PixelButton>
		{:else if step === 'walking-input'}
			<div class="ql-back">
				<button class="ql-backbtn" onclick={goBack} aria-label="Назад"><PixelIcon name="arrowleft" size="sm" /></button>
				<span class="ql-back__t">Ходьба</span>
			</div>
			<span class="ql-label">Количество шагов</span>
			<div class="qty">
				<button class="qty__btn" onclick={() => (walkingSteps = Math.max(100, walkingSteps - 500))} aria-label="Меньше"><PixelIcon name="minus" size="sm" /></button>
				<div class="qty__mid"><input class="qty__v qty__in" type="text" inputmode="numeric" maxlength="6" value={String(walkingSteps)} oninput={typeWalkingSteps} onblur={blurWalkingSteps} aria-label="Количество шагов" /><span class="qty__u">шагов</span></div>
				<button class="qty__btn" onclick={() => (walkingSteps = walkingSteps + 500)} aria-label="Больше"><PixelIcon name="plus" size="sm" /></button>
			</div>
			<div class="ql-sum"><span>≈ {(walkingSteps / 1300).toFixed(1)} км</span><span class="ql-sum__xp">+{walkingEstimatedXp} XP</span></div>
			<PixelButton variant="success" size="lg" fullWidth loading={isSubmitting} onclick={handleSaveWalking}><PixelIcon name="check" /> Записать ходьбу</PixelButton>
		{/if}
	</div>
</PixelModal>

<style>
	.ql {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		min-height: 180px;
	}

	.ql-modes {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.ql-chev {
		transform: rotate(180deg);
		flex: 0 0 auto;
	}

	.ql-back {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}
	.ql-backbtn {
		flex: 0 0 auto;
		width: 36px;
		height: 36px;
		display: grid;
		place-items: center;
		background: var(--bg3);
		border: 2px solid var(--line);
		cursor: pointer;
	}
	.ql-back__t {
		font-family: var(--font-display);
		font-size: var(--font-size-sm);
		color: var(--text);
	}

	.ql-label {
		font-size: var(--font-size-xs);
		color: var(--muted);
	}

	.ql-search {
		display: flex;
		align-items: center;
		gap: 9px;
		padding: 0 11px;
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
	}
	.ql-search__in {
		flex: 1;
		min-width: 0;
		border: none;
		outline: none;
		background: none;
		padding: 12px 0;
		font-family: var(--font-ui);
		font-size: var(--font-size-sm);
		color: var(--text);
	}
	.ql-search__in::placeholder {
		color: var(--muted);
	}
	.ql-search__filter {
		position: relative;
		flex: 0 0 auto;
		width: 30px;
		height: 30px;
		display: grid;
		place-items: center;
		background: var(--bg3);
		border: 2px solid var(--line);
		cursor: pointer;
	}
	.ql-fbadge {
		position: absolute;
		top: -6px;
		right: -6px;
		min-width: 16px;
		height: 16px;
		padding: 0 3px;
		display: grid;
		place-items: center;
		background: var(--accent);
		color: var(--on-accent);
		font-family: var(--font-data);
		font-size: 11px;
		border: 2px solid var(--line);
	}

	.ql-cats {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}
	.ql-pill {
		font-family: var(--font-ui);
		font-size: var(--font-size-xs);
		padding: 6px 10px;
		background: var(--bg2);
		border: 2px solid var(--line);
		color: var(--muted);
		cursor: pointer;
	}
	.ql-pill.is-active {
		background: var(--accent);
		color: var(--on-accent);
	}

	.ql-list {
		display: flex;
		flex-direction: column;
		gap: 7px;
		max-height: 320px;
		overflow-y: auto;
	}
	.ql-empty {
		font-size: var(--font-size-sm);
		color: var(--muted);
		text-align: center;
		padding: var(--spacing-lg);
		margin: 0;
	}

	.ql-sum__xp {
		color: var(--green);
	}

	.filter-sections {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		max-height: 360px;
		overflow-y: auto;
	}
	.filter-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}
	.filter-section-title {
		font-size: var(--font-size-xs);
		color: var(--muted);
		margin: 0;
	}
	.filter-options {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}
	.ql-filteractions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		padding-top: var(--spacing-md);
		border-top: var(--bw) solid var(--line);
	}
</style>
