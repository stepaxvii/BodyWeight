<script lang="ts">
	import { PixelModal, PixelIcon, PixelCard } from '$lib/components/ui';
	import ExercisePreview from '$lib/components/ui/ExercisePreview.svelte';
	import ExerciseFrameViewer from '$lib/components/ui/ExerciseFrameViewer.svelte';
	import type { Exercise } from '$lib/types';

	interface Props {
		exercise: Exercise | null;
		open: boolean;
		onclose: () => void;
	}

	let { exercise, open, onclose }: Props = $props();
	let showFrameViewer = $state(false);

	function getDifficultyStars(difficulty: number): string {
		return '\u2605'.repeat(difficulty) + '\u2606'.repeat(5 - difficulty);
	}

	function getEquipmentLabel(equipment: string): string {
		const labels: Record<string, string> = {
			'none': 'Без снаряжения',
			'pullup-bar': 'Турник',
			'dip-bars': 'Брусья',
			'bench': 'Скамья',
			'wall': 'Стена'
		};
		return labels[equipment] || equipment;
	}

	function getTagLabel(tag: string): string {
		const labels: Record<string, string> = {
			'chest': 'Грудь',
			'back': 'Спина',
			'shoulders': 'Плечи',
			'triceps': 'Трицепс',
			'biceps': 'Бицепс',
			'core': 'Кор',
			'abs': 'Пресс',
			'quads': 'Квадрицепс',
			'hamstrings': 'Бицепс бедра',
			'glutes': 'Ягодицы',
			'calves': 'Икры',
			'hip-flexors': 'Сгибатели бедра',
			'full-body': 'Всё тело',
			'upper-body': 'Верх тела',
			'lower-body': 'Низ тела',
			'flexibility': 'Гибкость',
			'balance': 'Баланс',
			'cardio': 'Кардио',
			'strength': 'Сила',
			'endurance': 'Выносливость'
		};
		return labels[tag] || tag;
	}
</script>

<PixelModal {open} title={exercise?.name_ru || 'Упражнение'} {onclose}>
	{#if exercise}
		<div class="exercise-info">
			<!-- Animation/Frame Viewer Toggle -->
			<div class="demo-section">
				{#if showFrameViewer}
					<ExerciseFrameViewer
						exercise={exercise.slug}
						currentFrame={1}
					/>
					<button class="view-toggle" on:click={() => showFrameViewer = false}>
						Показать превью
					</button>
				{:else}
					<ExercisePreview
						gifUrl={exercise.gif_url}
						exercise={exercise.slug}
						size="lg"
						version="v4"
					/>
					<button class="view-toggle" on:click={() => showFrameViewer = true}>
						Покадровый просмотр →
					</button>
				{/if}
			</div>

			<!-- Stats row -->
			<div class="stats-row">
				<div class="stat">
					<PixelIcon name="star" size="sm" color="var(--pixel-yellow)" />
					<span class="stat-value">{getDifficultyStars(exercise.difficulty)}</span>
				</div>
				<div class="stat">
					<PixelIcon name="trophy" size="sm" color="var(--pixel-green)" />
					<span class="stat-value">+{exercise.base_xp} XP</span>
				</div>
			</div>

			<!-- Equipment -->
			<div class="info-row">
				<span class="label">Снаряжение:</span>
				<span class="value">{getEquipmentLabel(exercise.equipment)}</span>
			</div>

			<!-- Type -->
			<div class="info-row">
				<span class="label">Тип:</span>
				<span class="value">{exercise.is_timed ? 'На время' : 'На повторения'}</span>
			</div>

			<!-- Required level -->
			{#if exercise.required_level > 1}
				<div class="info-row">
					<span class="label">Требуемый уровень:</span>
					<span class="value level">{exercise.required_level}</span>
				</div>
			{/if}

			<!-- Description -->
			{#if exercise.description_ru}
				<div class="description-section">
					<h4 class="section-title">Техника выполнения</h4>
					<p class="description">{exercise.description_ru}</p>
				</div>
			{/if}

			<!-- Tags/Muscle groups -->
			{#if exercise.tags && exercise.tags.length > 0}
				<div class="tags-section">
					<h4 class="section-title">Группы мышц</h4>
					<div class="tags">
						{#each exercise.tags as tag}
							<span class="tag">{getTagLabel(tag)}</span>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Progression -->
			{#if exercise.easier_exercise_slug || exercise.harder_exercise_slug}
				<div class="progression-section">
					<h4 class="section-title">Прогрессия</h4>
					<div class="progression">
						{#if exercise.easier_exercise_slug}
							<div class="progression-item easier">
								<PixelIcon name="arrow-left" size="sm" color="var(--pixel-green)" />
								<span>Легче: {exercise.easier_exercise_slug}</span>
							</div>
						{/if}
						{#if exercise.harder_exercise_slug}
							<div class="progression-item harder">
								<span>Сложнее: {exercise.harder_exercise_slug}</span>
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

	.demo-section {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
	}

	.view-toggle {
		padding: var(--spacing-xs) var(--spacing-md);
		background: var(--pixel-bg);
		border: 2px solid var(--border-color);
		color: var(--pixel-accent);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.view-toggle:hover {
		border-color: var(--pixel-accent);
		background: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	.view-toggle:active {
		transform: scale(0.98);
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
