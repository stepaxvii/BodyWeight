<script lang="ts">
	import { PixelButton, PixelCard, PixelIcon, PixelProgress } from '$lib/components/ui';
	import ExerciseInfoModal from '$lib/components/ExerciseInfoModal.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { exercisesStore } from '$lib/stores/exercises.svelte';
	import { calculateExerciseXp, calculateTimedXp } from '$lib/utils/xp';
	import type { Routine, RoutineExercise, Exercise } from '$lib/types';
	import { onMount, onDestroy } from 'svelte';

	interface Props {
		routine: Routine;
		exercises?: Exercise[];
		onclose?: () => void;
		oncomplete?: (xp: number, coins: number) => void;
	}

	let { routine, exercises: exercisesProp = [], onclose, oncomplete }: Props = $props();

	// All exercises data for descriptions
	// Initialize as empty array to force loading in onMount
	let allExercises = $state<Exercise[]>([]);
	let exercisesLoading = $state(false);

	// Current step in the routine
	let currentStep = $state(0);
	let isStarted = $state(false);
	let isPaused = $state(false);
	let isCompleted = $state(false);
	let isSubmitting = $state(false);

	// Timer state
	let timerSeconds = $state(0);
	let exerciseTimerSeconds = $state(0);
	let timerInterval: ReturnType<typeof setInterval> | null = null;
	let isExerciseTimerStarted = $state(false); // User must start timer manually for time-based exercises

	// Workout session - collect exercises to submit at the end
	let workoutStartTime = $state<Date | null>(null);
	let completedExercises = $state<Array<{
		exercise_slug: string;
		sets: number[];
		is_timed: boolean;
	}>>([]);
	let totalXpEarned = $state(0);
	let totalCoinsEarned = $state(0);
	let completedExercisesCount = $state(0);
	let showInfoExercise = $state<Exercise | null>(null);

	const currentExercise = $derived(routine.exercises[currentStep]);
	const exerciseData = $derived(allExercises.find(e => e.slug === currentExercise?.slug));
	const progress = $derived(((currentStep + 1) / routine.exercises.length) * 100);
	const isTimeBased = $derived(!!currentExercise?.duration);
	const targetValue = $derived(currentExercise?.duration || currentExercise?.reps || 0);

	// Format timer display
	function formatTime(seconds: number): string {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
	}

	const formattedTotalTime = $derived(formatTime(timerSeconds));
	const formattedExerciseTime = $derived(formatTime(exerciseTimerSeconds));

	onMount(async () => {
		// Load all exercises from cache or API
		exercisesLoading = true;
		try {
			const fetchedExercises = await exercisesStore.loadAll();
			// Merge with prop exercises to avoid duplicates
			const exerciseMap = new Map<string, Exercise>();
			// First add prop exercises
			exercisesProp.forEach(ex => exerciseMap.set(ex.slug, ex));
			// Then add fetched exercises (will override if duplicate)
			fetchedExercises.forEach(ex => exerciseMap.set(ex.slug, ex));
			allExercises = Array.from(exerciseMap.values());

			// Debug: check if all routine exercises are found
			const routineSlugs = routine.exercises.map(ex => ex.slug);
			const missingSlugs = routineSlugs.filter(slug => !exerciseMap.has(slug));
			if (missingSlugs.length > 0) {
				console.warn('RoutinePlayer: Missing exercises in allExercises:', missingSlugs);
			}
		} catch (error) {
			console.error('Failed to load exercises:', error);
			// Fallback to prop if available
			if (exercisesProp.length > 0) {
				allExercises = exercisesProp;
			}
		} finally {
			exercisesLoading = false;
		}
	});

	onDestroy(() => {
		stopTimer();
	});

	function startTimer() {
		if (timerInterval) return;
		timerInterval = setInterval(() => {
			if (!isPaused) {
				timerSeconds++;
				// Only count down exercise timer if user has started it
				if (isTimeBased && isExerciseTimerStarted && exerciseTimerSeconds > 0) {
					exerciseTimerSeconds--;
					if (exerciseTimerSeconds === 0) {
						telegram.hapticNotification('success');
					}
				}
			}
		}, 1000);
	}

	function startExerciseTimer() {
		isExerciseTimerStarted = true;
		telegram.hapticImpact('medium');
	}

	function stopTimer() {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
	}

	async function startRoutine() {
		isStarted = true;
		workoutStartTime = new Date();
		completedExercises = [];

		try {
			telegram.hapticImpact('medium');
		} catch (e) {
			console.warn('[RoutinePlayer] hapticImpact failed (probably offline / no Telegram API):', e);
		}

		// Start the total workout timer immediately
		startTimer();
		resetExerciseTimer();
	}

	function resetExerciseTimer() {
		isExerciseTimerStarted = false; // Reset - user must start timer again for next exercise
		if (isTimeBased) {
			exerciseTimerSeconds = currentExercise?.duration || 0;
		} else {
			exerciseTimerSeconds = 0;
		}
	}

	function togglePause() {
		isPaused = !isPaused;
		telegram.hapticImpact('light');
	}

	async function completeExercise() {
		if (!currentExercise) return;
		if (isSubmitting) return;

		telegram.hapticImpact('medium');

		// Record the exercise locally
		const exerciseData = allExercises.find(e => e.slug === currentExercise.slug);
		const isTimed = exerciseData?.is_timed || !!currentExercise.duration;

		let sets: number[];
		if (isTimed) {
			// For timed exercises, use the target duration
			const duration = currentExercise.duration || 0;
			sets = [duration];
		} else {
			// For rep-based exercises, use the target reps
			const reps = currentExercise.reps || 0;
			sets = [reps];
		}

		completedExercises.push({
			exercise_slug: currentExercise.slug,
			sets,
			is_timed: isTimed,
		});

		completedExercisesCount++;

		// Move to next exercise or complete
		if (currentStep < routine.exercises.length - 1) {
			currentStep++;
			resetExerciseTimer();
		} else {
			await finishRoutine();
		}
	}

	async function finishRoutine() {
		if (isSubmitting) return;
		if (!workoutStartTime || completedExercises.length === 0) return;

		isSubmitting = true;
		stopTimer();

		const workoutData = {
			duration_seconds: timerSeconds,
			exercises: completedExercises,
			completed_at: new Date().toISOString(),
		};

		try {
			const completed = await api.submitWorkout(workoutData);

			isCompleted = true;
			totalXpEarned = completed.workout.total_xp_earned;
			totalCoinsEarned = completed.workout.total_coins_earned;

			userStore.addXp(completed.workout.total_xp_earned);
			userStore.addCoins(completed.workout.total_coins_earned);

			telegram.hapticNotification('success');
		} catch (err) {
			console.error('Failed to complete routine:', err);

			// Offline: save for later sync and show completion screen anyway
			if (!navigator.onLine) {
				try {
					const pending = JSON.parse(localStorage.getItem('pending_workouts') || '[]');
					pending.push({ data: workoutData, timestamp: Date.now() });
					localStorage.setItem('pending_workouts', JSON.stringify(pending));
				} catch { /* ignore */ }

				isCompleted = true;
				// Estimate XP (mirrors backend: total volume Г— base_xp Г— rate Г— streak)
				totalXpEarned = completedExercises.reduce((sum, ex) => {
					const exercise = allExercises.find(e => e.slug === ex.exercise_slug);
					if (!exercise) return sum;
					const baseXp = exercise.base_xp ?? 5;
					const totalVolume = ex.sets.reduce((s, v) => s + v, 0);
					const xp = ex.is_timed
						? calculateTimedXp(baseXp, totalVolume, userStore.streak)
						: calculateExerciseXp(baseXp, totalVolume, userStore.streak);
					return sum + xp;
				}, 0);
				totalCoinsEarned = 0;
				telegram.hapticNotification('success');
			} else {
				telegram.hapticNotification('error');
			}
		} finally {
			isSubmitting = false;
		}
	}

	function handleClose() {
		stopTimer();
		if (isCompleted) {
			oncomplete?.(totalXpEarned, totalCoinsEarned);
		}
		onclose?.();
	}

	async function shareWorkout() {
		telegram.hapticImpact('medium');

		// Р“СЂСѓРїРїРёСЂСѓРµРј РїРѕ СѓРїСЂР°Р¶РЅРµРЅРёСЋ Рё СЃСѓРјРјРёСЂСѓРµРј РїРѕРІС‚РѕСЂС‹/СЃРµРєСѓРЅРґС‹
		const bySlug = new Map<string, { total: number; is_timed: boolean }>();
		for (const ce of completedExercises) {
			const sum = ce.sets.reduce((a, b) => a + b, 0);
			const existing = bySlug.get(ce.exercise_slug);
			if (existing) {
				existing.total += sum;
			} else {
				bySlug.set(ce.exercise_slug, { total: sum, is_timed: ce.is_timed });
			}
		}
		const exerciseLines = Array.from(bySlug.entries()).map(([slug, { total, is_timed }]) => {
			const ex = allExercises.find((e) => e.slug === slug);
			const name = ex?.name_ru || slug;
			const totalStr = is_timed ? `${total} СЃРµРє` : `${total} РїРѕРІС‚.`;
			return `  в–ё ${name}: ${totalStr}`;
		});

		const shareText = [
			`рџЏ† ${routine.name}`,
			'',
			`вЏ±пёЏ ${formattedTotalTime}`,
			`рџЊџ +${totalXpEarned} XP`,
			`рџЄ™ ${totalCoinsEarned} РјРѕРЅРµС‚`,
			'',
			'в”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓ',
			'рџ’Є РЈРїСЂР°Р¶РЅРµРЅРёСЏ',
			'в”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓв”Ѓ',
			...exerciseLines
		].join('\n');

		// Р’РЅСѓС‚СЂРё Telegram WebApp вЂ“ РІСЃС‘ РєР°Рє СЂР°РЅСЊС€Рµ
		if (telegram.webApp) {
			const botUsername = 'pixelfitbot';
			const botLink = `https://t.me/${botUsername}`;
			const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(botLink)}&text=${encodeURIComponent(shareText)}`;
			telegram.openTelegramLink(shareUrl);
		}
		// Р’ Р±СЂР°СѓР·РµСЂРµ вЂ” СЃРёСЃС‚РµРјРЅРѕРµ РјРµРЅСЋ В«РџРѕРґРµР»РёС‚СЊСЃСЏВ» С‚РѕР»СЊРєРѕ СЃ С‚РµРєСЃС‚РѕРј С‚СЂРµРЅРёСЂРѕРІРєРё
		else if (navigator.share) {
			try {
				await navigator.share({
					title: `PixelFit - ${routine.name}`,
					text: shareText
					// Р±РµР· url: С‡С‚РѕР±С‹ РЅРµ С„РѕСЂСЃРёС‚СЊ РїРµСЂРµС…РѕРґ РІ Telegram
				});
			} catch {
				// РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ Р·Р°РєСЂС‹Р» С€РµР№СЂ вЂ“ РїСЂРѕСЃС‚Рѕ РёРіРЅРѕСЂРёСЂСѓРµРј
			}
		} else {
			// Fallback: СЃРєРѕРїРёСЂРѕРІР°С‚СЊ РІ Р±СѓС„РµСЂ РѕР±РјРµРЅР° РІРµСЃСЊ С‚РµРєСЃС‚
			try {
				await navigator.clipboard.writeText(shareText);
			} catch {
				// РЅРµС‚ РґРѕСЃС‚СѓРїР° Рє Р±СѓС„РµСЂСѓ вЂ“ РЅРёС‡РµРіРѕ РЅРµ РґРµР»Р°РµРј
			}
		}

		telegram.hapticNotification('success');
	}

	function skipExercise() {
		telegram.hapticImpact('light');
		if (currentStep < routine.exercises.length - 1) {
			currentStep++;
			resetExerciseTimer();
		} else {
			finishRoutine();
		}
	}
</script>

<div class="player">
	{#if !isStarted}
		<!-- PRE-START -->
		<div class="player__scroll">
			<div class="player__bar">
				<button class="player__x" onclick={handleClose} aria-label="Р—Р°РєСЂС‹С‚СЊ"><PixelIcon name="close" size="sm" /></button>
				<span class="player__title">{routine.name}</span>
				<span class="player__x-spacer"></span>
			</div>

			<div class="feat">
				<div class="feat__band"><span>РџСЂРѕРіСЂР°РјРјР°</span></div>
				<div class="feat__body">
					<span class="feat__art slot slot--lg"><PixelIcon name="dumbbell" size="xl" color="var(--accent)" /></span>
					<div class="feat__info">
						<span class="feat__sub">{routine.description}</span>
						<div class="feat__stats">
							<span class="feat__stat"><PixelIcon name="timer" size="sm" color="var(--accent2)" /> ~{routine.duration_minutes} РјРёРЅ</span>
							<span class="feat__stat"><PixelIcon name="dumbbell" size="sm" color="var(--accent)" /> {routine.exercises.length} СѓРїСЂ.</span>
						</div>
					</div>
				</div>
			</div>

			<div class="player__listhead">РЈРїСЂР°Р¶РЅРµРЅРёСЏ</div>
			<div class="player__list">
				{#each routine.exercises as ex, i}
					{@const exData = allExercises.find((e) => e.slug === ex.slug)}
					<div class="prerow">
						<span class="prerow__n">{i + 1}</span>
						<span class="prerow__name">{exData?.name_ru || ex.slug}</span>
						<span class="prerow__t">{ex.duration ? `${ex.duration} СЃРµРє` : ex.reps ? `${ex.reps} РїРѕРІС‚.` : ''}</span>
						{#if exData}
							<button class="prerow__i" onclick={() => { showInfoExercise = exData; telegram.hapticImpact('light'); }} aria-label="РџРѕРґСЂРѕР±РЅРµРµ"><PixelIcon name="search" size="sm" color="var(--muted)" /></button>
						{/if}
					</div>
				{/each}
			</div>

			<div class="player__start">
				<PixelButton variant="primary" size="lg" fullWidth onclick={startRoutine}>
					<PixelIcon name="play" /> РќР°С‡Р°С‚СЊ
				</PixelButton>
			</div>
		</div>
	{:else if isCompleted}
		<!-- COMPLETION -->
		<div class="player__done">
			<span class="done__burst" aria-hidden="true"></span>
			<PixelIcon name="trophy" size="xl" color="var(--gold)" class="done__trophy" />
			<span class="done__title">{routine.name}</span>
			<span class="done__sub">Р·Р°РІРµСЂС€С‘РЅ!</span>
			<div class="done__grid">
				<div class="done__stat"><PixelIcon name="timer" size="md" color="var(--accent2)" /><span class="done__v">{formattedTotalTime}</span><span class="done__l">Р’СЂРµРјСЏ</span></div>
				<div class="done__stat"><PixelIcon name="xp" size="md" color="var(--accent)" /><span class="done__v done__v--green">+{totalXpEarned}</span><span class="done__l">РћРїС‹С‚</span></div>
				<div class="done__stat"><PixelIcon name="coin" size="md" color="var(--gold)" /><span class="done__v done__v--gold">+{totalCoinsEarned}</span><span class="done__l">РњРѕРЅРµС‚С‹</span></div>
				<div class="done__stat"><PixelIcon name="dumbbell" size="md" color="var(--accent)" /><span class="done__v">{completedExercisesCount}/{routine.exercises.length}</span><span class="done__l">РЈРїСЂ.</span></div>
			</div>
			<div class="player__doneactions">
				<PixelButton variant="secondary" fullWidth onclick={shareWorkout}><PixelIcon name="share" /> РџРѕРґРµР»РёС‚СЊСЃСЏ</PixelButton>
				<PixelButton variant="success" fullWidth onclick={handleClose}><PixelIcon name="check" /> Р“РѕС‚РѕРІРѕ</PixelButton>
			</div>
		</div>
	{:else}
		<!-- ACTIVE -->
		<div class="player__active">
			<div class="player__bar">
				<button class="player__x" onclick={handleClose} aria-label="Р—Р°РєСЂС‹С‚СЊ"><PixelIcon name="close" size="sm" /></button>
				<span class="player__step">{currentStep + 1} / {routine.exercises.length}</span>
				<span class="player__clock"><PixelIcon name="timer" size="sm" color="var(--accent2)" /> {formattedTotalTime}</span>
			</div>

			<div class="gauge"><div class="gauge__fill" style="width: {progress}%;"></div></div>

			<div class="player__stage">
				<span class="player__exname">{exerciseData?.name_ru || currentExercise?.slug}</span>
				{#if exerciseData?.description_ru}
					<span class="player__exdesc">{exerciseData.description_ru}</span>
				{/if}

				<div class="ring" class:ring--done={isTimeBased && exerciseTimerSeconds === 0 && isExerciseTimerStarted}>
					<div class="ring__bg"></div>
					<div class="ring__fill">
						{#if isTimeBased}
							<span class="ring__v">{formattedExerciseTime}</span>
							<span class="ring__l">{!isExerciseTimerStarted ? 'РЅР°Р¶РјРё СЃС‚Р°СЂС‚' : exerciseTimerSeconds === 0 ? 'РіРѕС‚РѕРІРѕ!' : 'РѕСЃС‚Р°Р»РѕСЃСЊ'}</span>
						{:else}
							<span class="ring__v">{targetValue}</span>
							<span class="ring__l">РїРѕРІС‚РѕСЂРµРЅРёР№</span>
						{/if}
					</div>
				</div>

				{#if currentStep < routine.exercises.length - 1}
					{@const nextEx = routine.exercises[currentStep + 1]}
					{@const nextExData = allExercises.find((e) => e.slug === nextEx.slug)}
					<div class="player__next"><span class="player__nextl">Р”Р°Р»РµРµ:</span> {nextExData?.name_ru || nextEx.slug}</div>
				{/if}
			</div>

			<div class="player__controls">
				{#if isTimeBased && !isExerciseTimerStarted}
					<PixelButton variant="primary" size="lg" fullWidth onclick={startExerciseTimer}><PixelIcon name="play" /> РЎС‚Р°СЂС‚ С‚Р°Р№РјРµСЂР°</PixelButton>
				{:else if isTimeBased && exerciseTimerSeconds > 0}
					<PixelButton variant="secondary" size="lg" fullWidth onclick={togglePause}><PixelIcon name={isPaused ? 'play' : 'pause'} /> {isPaused ? 'РџСЂРѕРґРѕР»Р¶РёС‚СЊ' : 'РџР°СѓР·Р°'}</PixelButton>
				{:else}
					<PixelButton variant="success" size="lg" fullWidth disabled={isSubmitting} onclick={completeExercise}><PixelIcon name="check" /> {isSubmitting ? 'РћС‚РїСЂР°РІРєР°вЂ¦' : 'Р“РѕС‚РѕРІРѕ'}</PixelButton>
				{/if}
				<PixelButton variant="ghost" fullWidth onclick={skipExercise}>РџСЂРѕРїСѓСЃС‚РёС‚СЊ</PixelButton>
			</div>
		</div>
	{/if}
</div>

<!-- Exercise Info Modal -->
<ExerciseInfoModal
	exercise={showInfoExercise}
	open={showInfoExercise !== null}
	onclose={() => showInfoExercise = null}
/>

<style>
	/* The .player kit (hud.css) positions the overlay absolute at a low z-index
	   for the prototype phone frame; the app needs it fixed to the viewport. */
	.player {
		position: fixed;
		z-index: 1000;
	}

	.player__x {
		flex: 0 0 auto;
		width: 36px;
		height: 36px;
		display: grid;
		place-items: center;
		background: var(--bg2);
		border: 2px solid var(--line);
		color: var(--text);
		cursor: pointer;
	}
	.player__x-spacer {
		flex: 0 0 auto;
		width: 36px;
	}

	.player__listhead {
		font-family: var(--font-display);
		font-size: var(--font-size-md);
		text-transform: uppercase;
		color: var(--text);
	}

	.player__doneactions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		width: 100%;
		margin-top: var(--spacing-md);
	}

	.done__v--green {
		color: var(--green);
	}
	.done__v--gold {
		color: var(--gold);
	}
</style>
