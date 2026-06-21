<script lang="ts">
	import { PixelButton, PixelCard, PixelIcon, PixelProgress } from '$lib/components/ui';
	import ExerciseInfoModal from '$lib/components/ExerciseInfoModal.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { sound } from '$lib/stores/sound.svelte';
	import { exercisesStore } from '$lib/stores/exercises.svelte';
	import { calculateExerciseXp, calculateTimedXp } from '$lib/utils/xp';
	import type { Routine, RoutineExercise, Exercise, ChallengeProgressSummary } from '$lib/types';
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

	// Rest-between-exercises state (roadmap 4.3)
	let isResting = $state(false);
	let restSeconds = $state(0);
	let restInterval: ReturnType<typeof setInterval> | null = null;
	const DEFAULT_REST_SECONDS = 30;

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
	// Challenge progress this workout credited (shown on the done screen)
	let challengeProgress = $state<ChallengeProgressSummary[]>([]);
	let showInfoExercise = $state<Exercise | null>(null);

	const currentExercise = $derived(routine.exercises[currentStep]);
	const exerciseData = $derived(allExercises.find(e => e.slug === currentExercise?.slug));
	const progress = $derived(((currentStep + 1) / routine.exercises.length) * 100);
	const isTimeBased = $derived(!!currentExercise?.duration);
	const targetValue = $derived(currentExercise?.duration || currentExercise?.reps || 0);
	const PROGRESS_SEGMENTS = 16;
	const segOn = $derived(Math.round((progress / 100) * PROGRESS_SEGMENTS));

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
		stopRestInterval();
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
						sound.exerciseDone();
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

		// Unlock audio on this user gesture, then play the start cue.
		sound.unlock();
		sound.start();

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

	// ---- Rest between exercises (roadmap 4.3) ----
	function stopRestInterval() {
		if (restInterval) {
			clearInterval(restInterval);
			restInterval = null;
		}
	}

	function advanceToNext() {
		currentStep++;
		resetExerciseTimer();
	}

	function startRest() {
		// Rest after the just-completed exercise (custom routines carry rest_seconds;
		// built-in routines fall back to a sensible default).
		const rs = currentExercise?.rest_seconds ?? DEFAULT_REST_SECONDS;
		if (rs <= 0) {
			advanceToNext();
			return;
		}
		isResting = true;
		restSeconds = rs;
		telegram.hapticImpact('light');
		stopRestInterval();
		restInterval = setInterval(() => {
			restSeconds--;
			if (restSeconds <= 0) endRest();
		}, 1000);
	}

	function endRest() {
		stopRestInterval();
		isResting = false;
		sound.restEnd();
		telegram.hapticNotification('success');
		advanceToNext();
	}

	function skipRest() {
		stopRestInterval();
		isResting = false;
		sound.click();
		telegram.hapticImpact('light');
		advanceToNext();
	}

	function addRest(sec: number) {
		restSeconds = Math.max(1, restSeconds + sec);
		telegram.hapticImpact('light');
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

		// Rep-based sets cue on press; timed sets already cued when the timer hit 0.
		if (!isTimed) sound.exerciseDone();

		// Rest before the next exercise, or finish the routine.
		if (currentStep < routine.exercises.length - 1) {
			startRest();
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
			challengeProgress = completed.challenge_progress ?? [];

			userStore.addXp(completed.workout.total_xp_earned);
			userStore.addCoins(completed.workout.total_coins_earned);

			telegram.hapticNotification('success');
			if (completed.level_up) sound.levelUp();
			else sound.complete();
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
				// Estimate XP (mirrors backend: total volume × base_xp × rate × streak)
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
				sound.complete();
			} else {
				telegram.hapticNotification('error');
				sound.error();
			}
		} finally {
			isSubmitting = false;
		}
	}

	function handleClose() {
		stopTimer();
		stopRestInterval();
		if (isCompleted) {
			oncomplete?.(totalXpEarned, totalCoinsEarned);
		}
		onclose?.();
	}

	async function shareWorkout() {
		telegram.hapticImpact('medium');

		// Группируем по упражнению и суммируем повторы/секунды
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
			const totalStr = is_timed ? `${total} сек` : `${total} повт.`;
			return `  ▸ ${name}: ${totalStr}`;
		});

		const shareText = [
			`🏆 ${routine.name}`,
			'',
			`⏱️ ${formattedTotalTime}`,
			`🌟 +${totalXpEarned} XP`,
			`🪙 ${totalCoinsEarned} монет`,
			'',
			'━━━━━━━━━━',
			'💪 Упражнения',
			'━━━━━━━━━━',
			...exerciseLines
		].join('\n');

		// Внутри Telegram WebApp – всё как раньше
		if (telegram.webApp) {
			const botUsername = 'pixelfitbot';
			const botLink = `https://t.me/${botUsername}`;
			const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(botLink)}&text=${encodeURIComponent(shareText)}`;
			telegram.openTelegramLink(shareUrl);
		}
		// В браузере — системное меню «Поделиться» только с текстом тренировки
		else if (navigator.share) {
			try {
				await navigator.share({
					title: `PixelFit - ${routine.name}`,
					text: shareText
					// без url: чтобы не форсить переход в Telegram
				});
			} catch {
				// пользователь закрыл шейр – просто игнорируем
			}
		} else {
			// Fallback: скопировать в буфер обмена весь текст
			try {
				await navigator.clipboard.writeText(shareText);
			} catch {
				// нет доступа к буферу – ничего не делаем
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
				<button class="player__x" onclick={handleClose} aria-label="Закрыть"><PixelIcon name="close" size="sm" /></button>
				<span class="player__title">{routine.name}</span>
				<span class="player__x-spacer"></span>
			</div>

			<div class="feat">
				<div class="feat__band"><span>Программа</span></div>
				<div class="feat__body">
					<span class="feat__art slot slot--lg"><PixelIcon name="dumbbell" size="xl" color="var(--accent)" /></span>
					<div class="feat__info">
						<span class="feat__sub">{routine.description}</span>
						<div class="feat__stats">
							<span class="feat__stat"><PixelIcon name="timer" size="sm" color="var(--accent2)" /> ~{routine.duration_minutes} мин</span>
							<span class="feat__stat"><PixelIcon name="dumbbell" size="sm" color="var(--accent)" /> {routine.exercises.length} упр.</span>
						</div>
					</div>
				</div>
			</div>

			<div class="player__listhead">Упражнения</div>
			<div class="player__list">
				{#each routine.exercises as ex, i}
					{@const exData = allExercises.find((e) => e.slug === ex.slug)}
					<div class="prerow">
						<span class="prerow__n">{i + 1}</span>
						<span class="prerow__name">{exData?.name_ru || ex.slug}</span>
						<span class="prerow__t">{ex.duration ? `${ex.duration} сек` : ex.reps ? `${ex.reps} повт.` : ''}</span>
						{#if exData}
							<button class="prerow__i" onclick={() => { showInfoExercise = exData; telegram.hapticImpact('light'); }} aria-label="Подробнее"><PixelIcon name="search" size="sm" color="var(--muted)" /></button>
						{/if}
					</div>
				{/each}
			</div>

			<div class="player__start">
				<PixelButton variant="primary" size="lg" fullWidth onclick={startRoutine}>
					<PixelIcon name="play" /> Начать
				</PixelButton>
			</div>
		</div>
	{:else if isCompleted}
		<!-- COMPLETION -->
		<div class="player__done">
			<span class="done__burst" aria-hidden="true"></span>
			<PixelIcon name="trophy" size="xl" color="var(--gold)" class="done__trophy" />
			<span class="done__title">{routine.name}</span>
			<span class="done__sub">завершён!</span>
			<div class="done__grid">
				<div class="done__stat"><PixelIcon name="timer" size="md" color="var(--accent2)" /><span class="done__v">{formattedTotalTime}</span><span class="done__l">Время</span></div>
				<div class="done__stat"><PixelIcon name="xp" size="md" color="var(--accent)" /><span class="done__v done__v--green">+{totalXpEarned}</span><span class="done__l">Опыт</span></div>
				<div class="done__stat"><PixelIcon name="coin" size="md" color="var(--gold)" /><span class="done__v done__v--gold">+{totalCoinsEarned}</span><span class="done__l">Монеты</span></div>
				<div class="done__stat"><PixelIcon name="dumbbell" size="md" color="var(--accent)" /><span class="done__v">{completedExercisesCount}/{routine.exercises.length}</span><span class="done__l">Упр.</span></div>
			</div>
			{#if challengeProgress.length > 0}
				<div class="done__chal">
					{#each challengeProgress as cp (cp.challenge_id)}
						<div class="done__chalcard" class:done__chalcard--full={cp.day_completed}>
							<div class="done__chalhead">
								<PixelIcon name="trophy" size="sm" color={cp.day_completed ? 'var(--gold)' : 'var(--accent)'} />
								<span class="done__chaltitle">{cp.challenge_title}</span>
								{#if cp.day_completed}
									<span class="done__chalbadge"><PixelIcon name="check" size="sm" color="var(--on-accent)" /> день закрыт</span>
								{/if}
							</div>
							{#each cp.exercises as ex (ex.exercise_name_ru)}
								<div class="done__chalrow">
									<span class="done__chalname">{ex.exercise_name_ru}</span>
									<span class="done__chalval" class:done__chalval--done={ex.completed}>
										+{ex.added}{ex.is_timed ? ' сек' : ''} · {ex.accumulated}/{ex.target}{ex.completed ? ' ✓' : ''}
									</span>
								</div>
							{/each}
						</div>
					{/each}
				</div>
			{/if}
			<div class="player__doneactions">
				<PixelButton variant="secondary" fullWidth onclick={shareWorkout}><PixelIcon name="share" /> Поделиться</PixelButton>
				<PixelButton variant="success" fullWidth onclick={handleClose}><PixelIcon name="check" /> Готово</PixelButton>
			</div>
		</div>
	{:else}
		<!-- ACTIVE -->
		<div class="player__active pa2">
			<div class="pa2-hero">
				<div class="pa2-hero__bar">
					<button class="pa2-x" onclick={handleClose} aria-label="Закрыть"><PixelIcon name="close" size="sm" /></button>
					<span class="pa2-hero__step">Упражнение {currentStep + 1}/{routine.exercises.length}</span>
					<span class="pa2-hero__clock"><PixelIcon name="timer" size="sm" color="var(--hero-num)" /> {formattedTotalTime}</span>
				</div>
				<div class="pa2-prog">
					<div class="pa2-gauge">
						{#each Array(PROGRESS_SEGMENTS) as _, i}
							<span class="pa2-seg" class:on={i < segOn}></span>
						{/each}
					</div>
					<span class="pa2-prog__pct">{Math.round(progress)}%</span>
				</div>
			</div>

			<div class="pa2-stage">
				<span class="pa2-hero__name">{isResting ? 'Отдых' : (exerciseData?.name_ru || currentExercise?.slug)}</span>

				{#if isResting}
					{@const restNextEx = routine.exercises[currentStep + 1]}
					{@const restNextData = allExercises.find((e) => e.slug === restNextEx?.slug)}
					<div class="pa2-count pa2-count--rest">
						<span class="pa2-count__box"><span class="pa2-count__v">{restSeconds}</span></span>
						<span class="pa2-count__u">секунд отдыха</span>
					</div>
					{#if restNextEx}
						<div class="pa2-next"><PixelIcon name="arrow-right" size="sm" color="var(--muted)" /> {restNextData?.name_ru || restNextEx.slug} — {restNextEx.duration ? restNextEx.duration + 'с.' : restNextEx.reps + 'п.'}</div>
					{/if}
				{:else}
					<div class="pa2-count" class:pa2-count--time={isTimeBased} class:pa2-count--done={isTimeBased && exerciseTimerSeconds === 0 && isExerciseTimerStarted}>
						<span class="pa2-count__box">
							{#if isTimeBased}
								<span class="pa2-count__v">{formattedExerciseTime}</span>
							{:else}
								<span class="pa2-count__v">{targetValue}</span>
							{/if}
							<span class="pa2-count__u">
								{#if isTimeBased}
									{!isExerciseTimerStarted ? 'нажми старт' : exerciseTimerSeconds === 0 ? 'готово!' : 'осталось'}
								{:else}
									повторений
								{/if}
							</span>
						</span>
					</div>

					{#if exerciseData?.description_ru}
						<div class="pa2-tech">
							<div class="pa2-tech__band">Техника</div>
							<div class="pa2-tech__body">{exerciseData.description_ru}</div>
						</div>
					{/if}

					{#if currentStep < routine.exercises.length - 1}
						{@const nextEx = routine.exercises[currentStep + 1]}
						{@const nextExData = allExercises.find((e) => e.slug === nextEx.slug)}
						<div class="pa2-next"><PixelIcon name="arrow-right" size="sm" color="var(--muted)" /> {nextExData?.name_ru || nextEx.slug} — {nextEx.duration ? nextEx.duration + 'с.' : nextEx.reps + 'п.'}</div>
					{/if}
				{/if}
			</div>

			<div class="player__controls">
				{#if isResting}
					<PixelButton variant="primary" size="lg" fullWidth onclick={skipRest}><PixelIcon name="play" /> Пропустить отдых</PixelButton>
					<PixelButton variant="ghost" fullWidth onclick={() => addRest(15)}>+15 секунд</PixelButton>
				{:else}
					{#if isTimeBased && !isExerciseTimerStarted}
						<PixelButton variant="primary" size="lg" fullWidth onclick={startExerciseTimer}><PixelIcon name="play" /> Старт таймера</PixelButton>
					{:else if isTimeBased && exerciseTimerSeconds > 0}
						<PixelButton variant="secondary" size="lg" fullWidth onclick={togglePause}><PixelIcon name={isPaused ? 'play' : 'pause'} /> {isPaused ? 'Продолжить' : 'Пауза'}</PixelButton>
					{:else}
						<PixelButton variant="success" size="lg" fullWidth disabled={isSubmitting} onclick={completeExercise}><PixelIcon name="check" /> {isSubmitting ? 'Отправка…' : 'Готово'}</PixelButton>
					{/if}
					<PixelButton variant="ghost" fullWidth onclick={skipExercise}>Пропустить</PixelButton>
				{/if}
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

	/* Challenge progress credited by this workout (feedback loop) */
	.done__chal {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
		width: 100%;
		margin-top: var(--spacing-md);
	}
	.done__chalcard {
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		padding: var(--spacing-sm) var(--spacing-md);
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.done__chalcard--full {
		border-color: var(--gold);
	}
	.done__chalhead {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.done__chaltitle {
		flex: 1;
		min-width: 0;
		font-family: var(--font-display);
		font-size: var(--font-size-sm);
		color: var(--text);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.done__chalbadge {
		flex: 0 0 auto;
		display: inline-flex;
		align-items: center;
		gap: 3px;
		font-family: var(--font-display);
		font-size: 10px;
		padding: 2px 6px;
		background: var(--accent2);
		color: var(--on-accent);
	}
	.done__chalrow {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--spacing-sm);
	}
	.done__chalname {
		font-size: var(--font-size-xs);
		color: var(--muted);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.done__chalval {
		flex: 0 0 auto;
		font-family: var(--font-data);
		font-size: 12px;
		color: var(--text);
	}
	.done__chalval--done {
		color: var(--green);
	}

	/* ============ ACTIVE screen — game-HUD redesign ============
	   Full-bleed mocha hero (name + segmented progress), the rep/timer as a big
	   number in a beveled slot, and a banded "Техника" scroll panel that caps
	   its height and scrolls internally — so a long description can never grow
	   the stage and push the controls off-screen. Controls stay pinned. Scoped. */
	.player__active {
		padding: 0;
		gap: 10px;
		min-height: 0;
	}

	/* hero — full-bleed mocha header */
	.pa2-hero {
		flex: 0 0 auto;
		background: var(--hero-bg);
		color: var(--hero-text);
		border-bottom: var(--bw) solid var(--hero-edge);
		padding: 12px 14px;
		display: flex;
		flex-direction: column;
		gap: 9px;
	}
	.pa2-hero__bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
	}
	.pa2-x {
		flex: 0 0 auto;
		width: 32px;
		height: 32px;
		display: grid;
		place-items: center;
		background: rgba(0, 0, 0, 0.22);
		border: 2px solid var(--hero-edge);
		color: var(--hero-text);
		cursor: pointer;
	}
	.pa2-hero__step {
		flex: 1;
		text-align: center;
		font-family: var(--font-display);
		font-size: 17px;
		letter-spacing: 0.6px;
		color: var(--hero-text);
		opacity: 0.9;
	}
	.pa2-hero__clock {
		flex: 0 0 auto;
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-family: var(--font-data);
		font-size: 14px;
		color: var(--hero-num);
	}
	.pa2-hero__name {
		font-family: var(--font-display);
		font-size: 22px;
		line-height: 1.15;
		text-align: center;
		padding: var(--spacing-sm) 0;
	}
	.pa2-prog {
		display: flex;
		align-items: center;
		gap: 9px;
	}
	.pa2-gauge {
		flex: 1;
		display: flex;
		gap: 2px;
		height: 13px;
	}
	.pa2-seg {
		flex: 1;
		background: rgba(0, 0, 0, 0.28);
		border: 1px solid var(--hero-edge);
	}
	.pa2-seg.on {
		background: var(--hero-num);
	}
	.pa2-prog__pct {
		flex: 0 0 auto;
		min-width: 34px;
		text-align: right;
		font-family: var(--font-data);
		font-size: 12px;
		color: var(--hero-text);
		opacity: 0.9;
	}

	/* stage — number + technique + next; centers when short, technique
	   shrinks/scrolls when long, so the column never overflows. */
	.pa2-stage {
		flex: 1 1 auto;
		min-height: 0;
		overflow: hidden;
		padding: 0 14px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 13px;
		text-align: center;
	}

	/* big number in a beveled inventory-style slot */
	.pa2-count {
		flex: 0 0 auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 7px;
	}
	.pa2-count__box {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-width: 134px;
		height: 108px;
		padding: 0 18px;
		background: var(--bg3);
		border: var(--bw) solid var(--line);
		box-shadow: inset 2px 2px 0 rgba(255, 255, 255, 0.14),
			inset -2px -2px 0 rgba(0, 0, 0, 0.32), var(--shadow);
	}
	.pa2-count__v {
		font-family: var(--font-display);
		font-size: 64px;
		line-height: 1;
		color: var(--accent);
	}
	.pa2-count--time .pa2-count__v {
		font-size: 44px;
	}
	.pa2-count--done .pa2-count__box {
		background: var(--green);
	}
	.pa2-count--done .pa2-count__v {
		color: var(--on-accent);
	}
	.pa2-count--rest .pa2-count__box {
		background: var(--accent2);
	}
	.pa2-count--rest .pa2-count__v {
		color: var(--on-accent);
	}
	.pa2-count__u {
		font-family: var(--font-ui);
		font-size: 12px;
		letter-spacing: 0.5px;
		color: var(--muted);
	}

	/* technique "scroll" — accent band header + internally-scrolling body */
	.pa2-tech {
		flex: 0 1 auto;
		min-height: 0;
		max-height: 34vh;
		overflow: hidden;
		width: 100%;
		max-width: 340px;
		display: flex;
		flex-direction: column;
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
	}
	.pa2-tech__band {
		flex: 0 0 auto;
		background: var(--accent);
		color: var(--on-accent);
		font-family: var(--font-display);
		font-size: 11px;
		letter-spacing: 0.6px;
		padding: 5px 11px;
		text-align: left;
	}
	.pa2-tech__body {
		flex: 1 1 auto;
		min-height: 0;
		overflow-y: auto;
		padding: 10px 12px;
		font-size: 14px;
		line-height: 1.6;
		color: var(--text);
		text-align: left;
	}
	.pa2-tech__body::-webkit-scrollbar {
		width: 0;
	}

	.pa2-next {
		flex: 0 0 auto;
		font-size: 16px;
		color: var(--muted);
	}
	.pa2-next__l {
		font-family: var(--font-display);
		font-size: 11px;
		letter-spacing: 0.5px;
		color: var(--dim);
		margin-right: 5px;
	}

	.player__controls {
		padding: 0 14px 14px;
	}
</style>
