<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { exercisesStore } from '$lib/stores/exercises.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Exercise, ChallengeExerciseInput } from '$lib/types';

	let title = $state('');
	let description = $state('');
	let startDate = $state(todayIso());
	let endDate = $state(addDaysIso(7));
	let pickedExercises = $state<{ exercise: Exercise; daily_target: number }[]>([]);
	let showPicker = $state(false);
	let pickerSearch = $state('');
	let exercises = $state<Exercise[]>([]);
	let submitting = $state(false);
	let error = $state<string | null>(null);

	function todayIso(): string {
		return new Date().toISOString().split('T')[0];
	}
	function addDaysIso(days: number): string {
		const d = new Date();
		d.setDate(d.getDate() + days);
		return d.toISOString().split('T')[0];
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
				// Cycling/walking work but their semantics are weird for daily-target
				e.slug !== 'cycling'
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

	function targetUnit(ex: Exercise): string {
		if (ex.is_timed) return 'сек';
		if (ex.slug === 'walking') return 'шагов';
		return 'повт.';
	}

	const durationDays = $derived.by(() => {
		const s = new Date(startDate);
		const e = new Date(endDate);
		const diff = Math.round((e.getTime() - s.getTime()) / 86400000) + 1;
		return diff > 0 ? diff : 0;
	});

	async function submit() {
		error = null;

		if (!title.trim()) {
			error = 'Введи название';
			return;
		}
		if (pickedExercises.length === 0) {
			error = 'Добавь хотя бы одно упражнение';
			return;
		}
		if (durationDays < 3) {
			error = 'Минимальная длительность — 3 дня';
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
			error = e instanceof Error ? e.message : 'Не удалось создать челлендж';
			telegram.hapticNotification('error');
		} finally {
			submitting = false;
		}
	}
</script>

<div class="new-page">
	<header class="page-header">
		<a href="{base}/challenges" class="back-link">
			<PixelIcon name="arrow-left" size="sm" />
		</a>
		<h1>Новый челлендж</h1>
	</header>

	<PixelCard padding="md">
		<div class="form-field">
			<label for="title">Название</label>
			<input
				id="title"
				type="text"
				maxlength="120"
				bind:value={title}
				placeholder="Например: 100 отжиманий за 30 дней"
				class="input"
			/>
		</div>

		<div class="form-field">
			<label for="desc">Описание (необязательно)</label>
			<textarea
				id="desc"
				bind:value={description}
				placeholder="Расскажи в двух предложениях, в чём суть"
				class="input textarea"
				rows="3"
			></textarea>
		</div>

		<div class="form-row">
			<div class="form-field">
				<label for="start">Старт</label>
				<input id="start" type="date" min={todayIso()} bind:value={startDate} class="input" />
			</div>
			<div class="form-field">
				<label for="end">Финиш</label>
				<input id="end" type="date" min={startDate} bind:value={endDate} class="input" />
			</div>
		</div>

		<div class="duration-hint">
			Длительность: <strong>{durationDays}</strong> дн.
		</div>
	</PixelCard>

	<PixelCard padding="md">
		<h3 class="section-title">Упражнения</h3>
		<p class="section-hint">
			Челлендж зачитывает <b>ровно</b> столько повторений за день, сколько ты указал. Лишние не считаются. Минимум 1, максимум 5 упражнений.
		</p>

		{#if pickedExercises.length === 0}
			<p class="empty-msg">Пока ничего не выбрано</p>
		{:else}
			<div class="picked-list">
				{#each pickedExercises as p, i (p.exercise.id)}
					<div class="picked-row">
						<div class="picked-name">{p.exercise.name_ru}</div>
						<div class="target-input">
							<input
								type="number"
								min="1"
								bind:value={p.daily_target}
								class="input small"
							/>
							<span class="unit">{targetUnit(p.exercise)} / день</span>
						</div>
						<button class="remove-btn" onclick={() => removeExercise(i)}>
							<PixelIcon name="close" size="sm" />
						</button>
					</div>
				{/each}
			</div>
		{/if}

		{#if pickedExercises.length < 5}
			<button class="add-btn" onclick={() => (showPicker = !showPicker)}>
				<PixelIcon name="plus" size="sm" />
				<span>{showPicker ? 'Закрыть' : 'Добавить упражнение'}</span>
			</button>

			{#if showPicker}
				<div class="picker">
					<input
						type="text"
						class="input"
						placeholder="Поиск упражнения..."
						bind:value={pickerSearch}
					/>
					<div class="picker-list">
						{#each filteredExercises as ex (ex.id)}
							<button class="picker-item" onclick={() => addExercise(ex)}>
								<span>{ex.name_ru}</span>
								{#if ex.is_timed}
									<span class="picker-tag">время</span>
								{:else if ex.slug === 'walking'}
									<span class="picker-tag">шаги</span>
								{/if}
							</button>
						{/each}
						{#if filteredExercises.length === 0}
							<div class="picker-empty">Ничего не найдено</div>
						{/if}
					</div>
				</div>
			{/if}
		{/if}
	</PixelCard>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	<PixelButton
		variant="success"
		size="lg"
		fullWidth
		loading={submitting}
		onclick={submit}
	>
		Создать челлендж
	</PixelButton>
</div>

<style>
	.new-page {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
	}

	.page-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.page-header h1 {
		font-size: var(--font-size-md);
		color: var(--text-primary);
		margin: 0;
		flex: 1;
	}

	.back-link {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		padding: var(--spacing-xs);
		display: flex;
		align-items: center;
		justify-content: center;
		text-decoration: none;
		color: var(--text-primary);
	}

	.form-field {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-bottom: var(--spacing-sm);
	}

	.form-field label {
		font-size: 11px;
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.form-row {
		display: flex;
		gap: var(--spacing-sm);
	}

	.form-row .form-field {
		flex: 1;
	}

	.input {
		width: 100%;
		padding: var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--border-color);
		color: var(--text-primary);
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
	}

	.input:focus {
		outline: none;
		border-color: var(--pixel-accent);
	}

	.input.small {
		width: 80px;
	}

	.textarea {
		font-family: inherit;
		resize: vertical;
	}

	.duration-hint {
		font-size: 11px;
		color: var(--text-muted);
	}

	.section-title {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
		margin: 0 0 var(--spacing-xs) 0;
	}

	.section-hint {
		font-size: 11px;
		color: var(--text-muted);
		line-height: 1.5;
		margin: 0 0 var(--spacing-sm) 0;
	}

	.empty-msg {
		font-size: 11px;
		color: var(--text-muted);
		font-style: italic;
		margin: 0 0 var(--spacing-sm) 0;
	}

	.picked-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-sm);
	}

	.picked-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-xs);
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
	}

	.picked-name {
		flex: 1;
		font-size: var(--font-size-xs);
	}

	.target-input {
		display: flex;
		align-items: center;
		gap: 4px;
	}

	.unit {
		font-size: 9px;
		color: var(--text-muted);
		text-transform: uppercase;
	}

	.remove-btn {
		background: none;
		border: 1px solid var(--border-color);
		padding: 4px;
		cursor: pointer;
		color: var(--text-muted);
		display: flex;
	}

	.remove-btn:hover {
		color: var(--pixel-red);
		border-color: var(--pixel-red);
	}

	.add-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-card);
		border: var(--border-width) dashed var(--border-color);
		color: var(--text-secondary);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		cursor: pointer;
		width: 100%;
		justify-content: center;
	}

	.add-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.picker {
		margin-top: var(--spacing-sm);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.picker-list {
		max-height: 240px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.picker-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
		color: var(--text-primary);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		cursor: pointer;
		text-align: left;
	}

	.picker-item:hover {
		border-color: var(--pixel-accent);
	}

	.picker-tag {
		font-size: 9px;
		color: var(--pixel-accent);
		text-transform: uppercase;
	}

	.picker-empty {
		font-size: 11px;
		color: var(--text-muted);
		text-align: center;
		padding: var(--spacing-sm);
	}

	.error {
		padding: var(--spacing-sm);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--pixel-red);
		color: var(--pixel-red);
		font-size: var(--font-size-xs);
	}
</style>
