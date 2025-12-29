<script lang="ts">
	import { PixelCard, PixelIcon } from '$lib/components/ui';
	import { favoritesStore } from '$lib/stores/favorites.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Exercise } from '$lib/types';

	interface Props {
		exercise: Exercise;
		isSelected?: boolean;
		showCheckbox?: boolean;
		showFavorite?: boolean;
		showInfo?: boolean;
		categoryColor?: string;
		onSelect?: () => void;
		onInfoClick?: () => void;
	}

	let {
		exercise,
		isSelected = false,
		showCheckbox = true,
		showFavorite = true,
		showInfo = true,
		categoryColor = 'var(--pixel-accent)',
		onSelect,
		onInfoClick
	}: Props = $props();

	const isFavorite = $derived(favoritesStore.isFavorite(exercise.id));

	function getDifficultyStars(difficulty: number): string {
		return '\u2605'.repeat(difficulty) + '\u2606'.repeat(5 - difficulty);
	}

	function handleCardClick() {
		if (onSelect) {
			onSelect();
		}
	}

	function handleFavoriteClick(e: Event) {
		e.stopPropagation();
		favoritesStore.toggleFavorite(exercise.id);
	}

	function handleInfoClick(e: Event) {
		e.stopPropagation();
		telegram.hapticImpact('light');
		onInfoClick?.();
	}
</script>

<PixelCard hoverable onclick={handleCardClick} padding="sm">
	<div class="exercise-row" class:selected={isSelected}>
		{#if showCheckbox}
			<div class="checkbox" class:checked={isSelected}>
				{#if isSelected}
					<PixelIcon name="check" size="sm" color="var(--pixel-bg)" />
				{/if}
			</div>
		{/if}
		<div class="exercise-info">
			<span class="exercise-name">{exercise.name_ru}</span>
			<span class="exercise-meta">
				<span style="color: {categoryColor}">
					{getDifficultyStars(exercise.difficulty)}
				</span>
				<span class="xp-badge">+{exercise.base_xp} XP</span>
			</span>
		</div>
		{#if showInfo}
			<button
				class="info-btn"
				onclick={handleInfoClick}
				title="Подробнее"
			>
				?
			</button>
		{/if}
		{#if showFavorite}
			<button
				class="favorite-btn"
				onclick={handleFavoriteClick}
				title={isFavorite ? 'Убрать из избранного' : 'Добавить в избранное'}
			>
				<PixelIcon
					name={isFavorite ? 'heart' : 'heart-empty'}
					size="sm"
					color={isFavorite ? 'var(--pixel-red)' : 'var(--text-secondary)'}
				/>
			</button>
		{/if}
	</div>
</PixelCard>

<style>
	.exercise-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
	}

	.exercise-row.selected {
		background: rgba(var(--pixel-accent-rgb), 0.1);
		margin: calc(-1 * var(--spacing-sm));
		padding: var(--spacing-sm);
	}

	.checkbox {
		width: 24px;
		height: 24px;
		border: 2px solid var(--border-color);
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.checkbox.checked {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
	}

	.exercise-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}

	.exercise-name {
		font-size: var(--font-size-sm);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.exercise-meta {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		font-size: var(--font-size-xs);
	}

	.xp-badge {
		color: var(--pixel-green);
	}

	.info-btn {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		cursor: pointer;
		flex-shrink: 0;
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		font-weight: bold;
		color: var(--text-secondary);
		transition: all var(--transition-fast);
	}

	.info-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--pixel-accent);
	}

	.info-btn:active {
		transform: scale(1.1);
	}

	.favorite-btn {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: none;
		cursor: pointer;
		flex-shrink: 0;
		transition: transform var(--transition-fast);
	}

	.favorite-btn:active {
		transform: scale(1.2);
	}
</style>
