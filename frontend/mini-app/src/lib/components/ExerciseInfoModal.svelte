<script lang="ts">
	import { PixelModal, PixelIcon, PixelCard } from '$lib/components/ui';
	import { getTagName } from '$lib/utils';
	import { api } from '$lib/api/client';
	import { t, ln } from '$lib/i18n/index.svelte';
	import type { Exercise, ExerciseProgress } from '$lib/types';

	interface Props {
		exercise: Exercise | null;
		open: boolean;
		onclose: () => void;
	}

	let { exercise, open, onclose }: Props = $props();

	// Personal stats for this exercise (roadmap 2.4), loaded when the modal opens.
	let progress = $state<ExerciseProgress | null>(null);

	$effect(() => {
		if (open && exercise) {
			const slug = exercise.slug;
			progress = null;
			api
				.getExerciseProgress(slug)
				.then((p) => {
					// Guard against a stale response if the user switched exercises.
					if (exercise && exercise.slug === slug) progress = p;
				})
				.catch(() => {
					progress = null;
				});
		}
	});

	function fmtDate(iso?: string | null): string {
		if (!iso) return '—';
		return new Date(iso).toLocaleDateString('ru-RU', {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});
	}

	function getDifficultyStars(difficulty: number): string {
		return '\u2605'.repeat(difficulty) + '\u2606'.repeat(5 - difficulty);
	}

	function getEquipmentLabel(equipment: string): string {
		const labels: Record<string, string> = {
			'none': t('modals2.equipmentNone'),
			'pullup-bar': t('modals2.equipmentPullupBar'),
			'dip-bars': t('modals2.equipmentDipBars'),
			'bench': t('modals2.equipmentBench'),
			'wall': t('modals2.equipmentWall'),
			'bike': t('modals2.equipmentBike'),
			'dumbbell': t('modals2.equipmentDumbbell')
		};
		return labels[equipment] || equipment;
	}
</script>

<PixelModal {open} title={ln(exercise?.name, exercise?.name_ru) || t('modals2.exerciseTitle')} {onclose}>
	{#if exercise}
		<div class="exercise-info">
			<!-- Stats row -->
			<div class="stats-row">
				<div class="stat">
					<PixelIcon name="star" size="sm" color="var(--pixel-yellow)" />
					<span class="stat-value">{getDifficultyStars(exercise.difficulty)}</span>
				</div>
				<div class="stat">
					<PixelIcon name="bolt" size="sm" color="var(--pixel-green)" />
					<span class="stat-value">+{exercise.base_xp} XP</span>
				</div>
			</div>

			<!-- Personal stats (roadmap 2.4) -->
			{#if progress && progress.times_performed > 0}
				<div class="mystats-section">
					<h4 class="section-title">{t('modals2.myStats')}</h4>
					<div class="info-row">
						<span class="label">{t('modals2.totalReps')}</span>
						<span class="value">{progress.total_reps_ever}</span>
					</div>
					<div class="info-row">
						<span class="label">{t('modals2.timesPerformed')}</span>
						<span class="value">{progress.times_performed}</span>
					</div>
					{#if progress.best_single_set > 0}
						<div class="info-row">
							<span class="label">{t('modals2.bestSet')}</span>
							<span class="value">{progress.best_single_set}</span>
						</div>
					{/if}
					{#if progress.best_single_day > 0}
						<div class="info-row">
							<span class="label">{t('modals2.bestDay')}</span>
							<span class="value">{progress.best_single_day}</span>
						</div>
					{/if}
					<div class="info-row">
						<span class="label">{t('modals2.lastPerformed')}</span>
						<span class="value">{fmtDate(progress.last_performed_at)}</span>
					</div>
				</div>
			{/if}

			<!-- Equipment -->
			<div class="info-row">
				<span class="label">{t('modals2.equipmentLabel')}</span>
				<span class="value">{getEquipmentLabel(exercise.equipment)}</span>
			</div>

			<!-- Type -->
			<div class="info-row">
				<span class="label">{t('modals2.typeLabel')}</span>
				<span class="value">{exercise.is_timed ? t('modals2.typeTimed') : t('modals2.typeReps')}</span>
			</div>

			<!-- Required level -->
			{#if exercise.required_level > 1}
				<div class="info-row">
					<span class="label">{t('modals2.requiredLevelLabel')}</span>
					<span class="value level">{exercise.required_level}</span>
				</div>
			{/if}

			<!-- Description -->
			{#if exercise.description_ru}
				<div class="description-section">
					<h4 class="section-title">{t('modals2.technique')}</h4>
					<p class="description">{ln(exercise.description, exercise.description_ru)}</p>
				</div>
			{/if}

			<!-- Tags/Muscle groups -->
			{#if exercise.tags && exercise.tags.length > 0}
				<div class="tags-section">
					<h4 class="section-title">{t('modals2.muscleGroups')}</h4>
					<div class="tags">
						{#each exercise.tags as tag}
							<span class="tag">{getTagName(tag)}</span>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Progression -->
			{#if exercise.easier_exercise_slug || exercise.harder_exercise_slug}
				<div class="progression-section">
					<h4 class="section-title">{t('modals2.progression')}</h4>
					<div class="progression">
						{#if exercise.easier_exercise_slug}
							<div class="progression-item easier">
								<PixelIcon name="arrow-left" size="sm" color="var(--pixel-green)" />
								<span>{t('modals2.easier', { slug: exercise.easier_exercise_slug })}</span>
							</div>
						{/if}
						{#if exercise.harder_exercise_slug}
							<div class="progression-item harder">
								<span>{t('modals2.harder', { slug: exercise.harder_exercise_slug })}</span>
								<PixelIcon name="arrow-right" size="sm" color="var(--pixel-red)" />
							</div>
						{/if}
					</div>
				</div>
			{/if}
		</div>
	{/if}
</PixelModal>

<style>
	.exercise-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.stats-row {
		display: flex;
		justify-content: center;
		gap: var(--spacing-xl);
	}

	.stat {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.stat-value {
		font-size: var(--font-size-sm);
	}

	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-xs) 0;
		border-bottom: 1px solid var(--border-color);
	}

	.label {
		color: var(--text-secondary);
		font-size: var(--font-size-xs);
	}

	.value {
		font-size: var(--font-size-sm);
	}

	.value.level {
		color: var(--pixel-accent);
		font-weight: bold;
	}

	.section-title {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
		text-transform: uppercase;
		margin: 0 0 var(--spacing-xs) 0;
	}

	.mystats-section {
		padding-top: var(--spacing-sm);
	}

	.description-section {
		padding-top: var(--spacing-sm);
	}

	.description {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		line-height: 1.5;
		margin: 0;
	}

	.tags-section {
		padding-top: var(--spacing-sm);
	}

	.tags {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}

	.tag {
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
		padding: 2px 8px;
		font-size: 10px;
		color: var(--text-secondary);
	}

	.progression-section {
		padding-top: var(--spacing-sm);
	}

	.progression {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.progression-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.progression-item.easier {
		color: var(--pixel-green);
	}

	.progression-item.harder {
		color: var(--pixel-red);
		justify-content: flex-end;
	}
</style>
