<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { PixelButton, PixelIcon } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { exercisesStore } from '$lib/stores/exercises.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { t, ln } from '$lib/i18n/index.svelte';
	import type { Exercise, ChallengeExerciseInput } from '$lib/types';

	const MAX_EXERCISES = 5;
	const DURATION_PRESETS = [7, 14, 30, 60];
	// Reward tiers — must mirror backend REWARD_TIERS in services/challenges.py
	const REWARD_TIERS = [
		{ pct: 100, coins: 200, labelKey: 'challenges.tiers.perfect' },
		{ pct: 80, coins: 100, labelKey: 'challenges.tiers.great' },
		{ pct: 50, coins: 40, labelKey: 'challenges.tiers.good' },
		{ pct: 1, coins: 10, labelKey: 'challenges.tiers.participation' }
	];

	let title = $state('');
	let description = $state('');
	let startDate = $state(addDaysIso(todayIso(), 1)); // default tomorrow → join window
	let durationDays = $state(30);
	let pickedExercises = $state<{ exercise: Exercise; daily_target: number }[]>([]);
	let showPicker = $state(false);
	let pickerSearch = $state('');
	let exercises = $state<Exercise[]>([]);
	let submitting = $state(false);
	let error = $state<string | null>(null);

	function todayIso(): string {
		return new Date().toISOString().split('T')[0];
	}
	function addDaysIso(fromIso: string, days: number): string {
		// UTC-anchored so date math never drifts a day across timezones.
		const d = new Date(fromIso + 'T00:00:00Z');
		d.setUTCDate(d.getUTCDate() + days);
		return d.toISOString().split('T')[0];
	}

	// End date is derived from start + chosen duration (inclusive of the start day).
	const endDate = $derived(addDaysIso(startDate, durationDays - 1));

	function fmtDate(iso: string): string {
		return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
	}

	onMount(async () => {
		try {
			exercises = await exercisesStore.loadAll();
		} catch (e) {
			console.error('Failed to load exercises:', e);
			exercises = exercisesStore.exercises;
		}
	});

	const filteredExercises = $derived.by(() => {
		const q = pickerSearch.trim().toLowerCase();
		const pickedIds = new Set(pickedExercises.map((p) => p.exercise.id));
		const candidates = exercises.filter(
			(e) =>
				!pickedIds.has(e.id) &&
				// Cycling/running/walking work but their semantics are weird for daily-target
				e.slug !== 'cycling' &&
				e.slug !== 'running'
		);
		if (!q) return candidates.slice(0, 50);
		return candidates
			.filter(
				(e) =>
					e.name_ru.toLowerCase().includes(q) ||
					e.name.toLowerCase().includes(q)
			)
			.slice(0, 50);
	});

	function addExercise(ex: Exercise) {
		const defaultTarget = ex.is_timed ? 60 : ex.slug === 'walking' ? 8000 : 30;
		pickedExercises = [...pickedExercises, { exercise: ex, daily_target: defaultTarget }];
		showPicker = false;
		pickerSearch = '';
		telegram.hapticImpact('light');
	}

	function removeExercise(idx: number) {
		pickedExercises = pickedExercises.filter((_, i) => i !== idx);
		telegram.hapticImpact('light');
	}

	function stepTarget(idx: number, delta: number) {
		pickedExercises = pickedExercises.map((p, i) =>
			i === idx ? { ...p, daily_target: Math.max(1, p.daily_target + delta) } : p
		);
		telegram.hapticImpact('light');
	}

	function targetUnit(ex: Exercise): string {
		if (ex.is_timed) return t('challenges.new.unitSec');
		if (ex.slug === 'walking') return t('challenges.new.unitSteps');
		return t('challenges.new.unitReps');
	}

	function stepFor(ex: Exercise): number {
		if (ex.slug === 'walking') return 500;
		return 5;
	}

	async function submit() {
		error = null;

		if (!title.trim()) {
			error = t('challenges.new.errorNoTitle');
			return;
		}
		if (pickedExercises.length === 0) {
			error = t('challenges.new.errorNoExercises');
			return;
		}

		submitting = true;
		try {
			const payload = {
				title: title.trim(),
				description: description.trim() || undefined,
				start_date: startDate,
				end_date: endDate,
				exercises: pickedExercises.map(
					(p): ChallengeExerciseInput => ({
						exercise_slug: p.exercise.slug,
						daily_target: p.daily_target
					})
				)
			};
			const created = await api.createChallenge(payload);
			telegram.hapticNotification('success');
			goto(`${base}/challenges/${created.id}`);
		} catch (e) {
			error = e instanceof Error ? e.message : t('challenges.new.errorCreate');
			telegram.hapticNotification('error');
		} finally {
			submitting = false;
		}
	}
</script>

<div class="new-page">
	<header class="cn-head">
		<a href="{base}/challenges" class="cn-back" aria-label={t('challenges.new.backAria')}>
			<PixelIcon name="arrowleft" size="md" color="var(--text)" />
		</a>
		<h1 class="cn-title">{t('challenges.new.title')}</h1>
	</header>

	<!-- Название -->
	<section class="cn-sec">
		<div class="sec-head"><span class="sec-head__t">{t('challenges.new.nameSection')}</span></div>
		<div class="searchbar">
			<PixelIcon name="edit" size="sm" color="var(--muted)" />
			<input
				class="searchbar__in"
				type="text"
				maxlength="120"
				bind:value={title}
				placeholder={t('challenges.new.namePlaceholder')}
			/>
		</div>
		<textarea
			class="cn-textarea"
			bind:value={description}
			placeholder={t('challenges.new.descPlaceholder')}
			rows="2"
		></textarea>
	</section>

	<!-- Старт + длительность -->
	<section class="cn-sec">
		<div class="sec-head"><span class="sec-head__t">{t('challenges.new.startSection')}</span></div>
		<input class="cn-date" type="date" min={todayIso()} bind:value={startDate} />
		<p class="cn-hint">{t('challenges.new.startHint')}</p>

		<div class="sec-head sec-head--mt"><span class="sec-head__t">{t('challenges.new.durationSection')}</span><span class="sec-head__m">{t('challenges.new.durationValue', { count: durationDays })}</span></div>
		<div class="qty-row">
			{#each DURATION_PRESETS as d}
				<button class="pill" class:is-active={durationDays === d} onclick={() => { durationDays = d; telegram.hapticImpact('light'); }}>
					{t('challenges.new.presetDays', { count: d })}
				</button>
			{/each}
		</div>
		<p class="cn-hint">{fmtDate(startDate)} — {fmtDate(endDate)}</p>
	</section>

	<!-- Упражнения и цели -->
	<section class="cn-sec">
		<div class="sec-head"><span class="sec-head__t">{t('challenges.new.exercisesSection')}</span><span class="sec-head__m">{pickedExercises.length}/{MAX_EXERCISES}</span></div>

		<div class="cn-callout">
			<PixelIcon name="warning" size="sm" color="var(--accent)" />
			<span>{@html t('challenges.new.callout')}</span>
		</div>

		{#if pickedExercises.length === 0}
			<p class="cn-empty">{t('challenges.new.emptyExercises')}</p>
		{:else}
			<div class="cn-list">
				{#each pickedExercises as p, i (p.exercise.id)}
					<div class="cn-ex is-on">
						<button class="cn-ex__pick" onclick={() => removeExercise(i)} aria-label={t('challenges.new.removeAria')}>
							<span class="slot slot--sm slot--filled cn-ex__slot">
								<PixelIcon name="check" size="sm" color="var(--on-accent)" />
							</span>
							<span class="cn-ex__name">{ln(p.exercise.name, p.exercise.name_ru)}</span>
						</button>
						<div class="cn-ex__tgt">
							<button class="cn-step" onclick={() => stepTarget(i, -stepFor(p.exercise))} aria-label={t('challenges.new.stepLessAria')}><PixelIcon name="minus" size="sm" /></button>
							<span class="cn-ex__val">{p.daily_target} <span class="cn-ex__u">{targetUnit(p.exercise)}</span></span>
							<button class="cn-step" onclick={() => stepTarget(i, stepFor(p.exercise))} aria-label={t('challenges.new.stepMoreAria')}><PixelIcon name="plus" size="sm" /></button>
						</div>
					</div>
				{/each}
			</div>
		{/if}

		{#if pickedExercises.length < MAX_EXERCISES}
			<button class="cn-add" onclick={() => (showPicker = !showPicker)}>
				<PixelIcon name="plus" size="sm" />
				<span>{showPicker ? t('challenges.new.pickerClose') : t('challenges.new.pickerAdd')}</span>
			</button>

			{#if showPicker}
				<div class="cn-picker">
					<div class="searchbar">
						<PixelIcon name="search" size="sm" color="var(--muted)" />
						<input class="searchbar__in" type="text" placeholder={t('challenges.new.pickerSearchPlaceholder')} bind:value={pickerSearch} />
					</div>
					<div class="cn-picker__list">
						{#each filteredExercises as ex (ex.id)}
							<button class="cn-picker__item" onclick={() => addExercise(ex)}>
								<span>{ln(ex.name, ex.name_ru)}</span>
								{#if ex.is_timed}
									<span class="cn-picker__tag">{t('challenges.new.pickerTagTimed')}</span>
								{:else if ex.slug === 'walking'}
									<span class="cn-picker__tag">{t('challenges.new.pickerTagSteps')}</span>
								{/if}
							</button>
						{/each}
						{#if filteredExercises.length === 0}
							<div class="cn-picker__empty">{t('challenges.new.pickerEmpty')}</div>
						{/if}
					</div>
				</div>
			{/if}
		{/if}
	</section>

	<!-- Награды -->
	<section class="cn-sec">
		<div class="sec-head"><span class="sec-head__t">{t('challenges.new.rewardsSection')}</span><span class="sec-head__m">{t('challenges.new.rewardsSub')}</span></div>
		<div class="cn-tiers">
			{#each REWARD_TIERS as tier}
				<div class="cn-tier">
					<span class="cn-tier__pct">{tier.pct}%+</span>
					<span class="cn-tier__label">{t(tier.labelKey)}</span>
					<span class="cn-tier__coins"><PixelIcon name="coin" size="sm" color="var(--gold)" /> {tier.coins}</span>
				</div>
			{/each}
		</div>
	</section>

	{#if error}
		<div class="cn-error">{error}</div>
	{/if}

	<PixelButton variant="success" size="lg" fullWidth loading={submitting} onclick={submit}>
		<PixelIcon name="check" /> {t('challenges.new.submit')}
	</PixelButton>
</div>

<style>
	.new-page {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
	}

	/* Header */
	.cn-head {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}
	.cn-back {
		flex: 0 0 auto;
		width: 40px;
		height: 40px;
		display: grid;
		place-items: center;
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		text-decoration: none;
	}
	.cn-back:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}
	.cn-title {
		flex: 1;
		margin: 0;
		font-family: var(--font-display);
		font-size: var(--font-size-md);
		color: var(--text);
	}

	.cn-sec {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	/* Section head (neo prototype look) */
	.sec-head {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 8px;
	}
	.sec-head--mt {
		margin-top: var(--spacing-sm);
	}
	.sec-head__t {
		font-family: var(--font-display);
		font-size: var(--font-size-sm);
		color: var(--text);
	}
	.sec-head__m {
		font-family: var(--font-data);
		font-size: 12px;
		color: var(--muted);
	}

	/* Searchbar-style input */
	.searchbar {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 9px 11px;
		background: var(--bg3);
		border: var(--bw) solid var(--line);
	}
	.searchbar__in {
		flex: 1;
		min-width: 0;
		background: none;
		border: none;
		outline: none;
		color: var(--text);
		font-family: var(--font-ui);
		font-size: 14px;
	}
	.searchbar__in::placeholder {
		color: var(--dim);
	}

	.cn-textarea {
		width: 100%;
		padding: 9px 11px;
		background: var(--bg3);
		border: var(--bw) solid var(--line);
		color: var(--text);
		font-family: var(--font-ui);
		font-size: 14px;
		outline: none;
		resize: vertical;
	}
	.cn-textarea:focus,
	.searchbar:focus-within {
		border-color: var(--accent);
	}

	.cn-date {
		width: 100%;
		padding: 9px 11px;
		background: var(--bg3);
		border: var(--bw) solid var(--line);
		color: var(--text);
		font-family: var(--font-ui);
		font-size: 14px;
		outline: none;
	}
	.cn-date:focus {
		border-color: var(--accent);
	}

	.cn-hint {
		margin: 0;
		font-size: 11px;
		color: var(--muted);
		line-height: 1.4;
	}

	/* Duration / preset pills (base .pill not in hud.css — defined here) */
	.pill {
		padding: 8px 10px;
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		color: var(--muted);
		font-family: var(--font-display);
		font-size: 12px;
		cursor: pointer;
		box-shadow: var(--shadow);
	}
	.pill:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}
	.pill.is-active {
		background: var(--accent);
		color: var(--on-accent);
		border-color: var(--line);
	}

	/* AND-logic explainer */
	.cn-callout {
		display: flex;
		gap: 8px;
		padding: 9px 11px;
		background: var(--bg2);
		border: var(--bw) solid var(--accent);
		font-size: 11px;
		color: var(--muted);
		line-height: 1.45;
	}
	.cn-callout b {
		color: var(--text);
	}

	.cn-empty {
		margin: 0;
		font-size: 12px;
		color: var(--dim);
		font-style: italic;
	}

	.cn-list {
		display: flex;
		flex-direction: column;
		gap: 9px;
	}
	.cn-ex__slot {
		width: 30px;
		height: 30px;
	}

	/* Add button */
	.cn-add {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		padding: 9px 11px;
		background: var(--bg2);
		border: var(--bw) dashed var(--line);
		color: var(--muted);
		font-family: var(--font-display);
		font-size: 12px;
		cursor: pointer;
		width: 100%;
	}
	.cn-add:active {
		transform: translate(2px, 2px);
	}

	.cn-picker {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.cn-picker__list {
		max-height: 240px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.cn-picker__item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 8px;
		padding: 9px 11px;
		background: var(--bg3);
		border: 2px solid var(--line);
		color: var(--text);
		font-family: var(--font-ui);
		font-size: 13px;
		cursor: pointer;
		text-align: left;
	}
	.cn-picker__item:active {
		transform: translate(2px, 2px);
	}
	.cn-picker__tag {
		font-size: 9px;
		color: var(--accent);
	}
	.cn-picker__empty {
		font-size: 12px;
		color: var(--dim);
		text-align: center;
		padding: var(--spacing-sm);
	}

	/* Reward tiers */
	.cn-tiers {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.cn-tier {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 11px;
		background: var(--bg2);
		border: var(--bw) solid var(--line);
	}
	.cn-tier__pct {
		flex: 0 0 auto;
		font-family: var(--font-data);
		font-size: 14px;
		color: var(--text);
		min-width: 44px;
	}
	.cn-tier__label {
		flex: 1;
		font-size: 12px;
		color: var(--muted);
	}
	.cn-tier__coins {
		flex: 0 0 auto;
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-family: var(--font-data);
		font-size: 14px;
		color: var(--gold);
	}

	.cn-error {
		padding: var(--spacing-sm);
		background: var(--bg2);
		border: var(--bw) solid var(--danger);
		color: var(--danger);
		font-size: var(--font-size-xs);
	}
</style>
