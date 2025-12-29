<script lang="ts">
	import { PixelButton, PixelModal } from '$lib/components/ui';
	import { telegram } from '$lib/stores/telegram.svelte';

	export interface FilterState {
		equipment: string[];
		difficulties: number[];
		tags: string[];
	}

	interface Props {
		open: boolean;
		initialFilters?: FilterState;
		onClose: () => void;
		onApply: (filters: FilterState) => void;
	}

	let { open, initialFilters, onClose, onApply }: Props = $props();

	// Local filter state
	let selectedEquipment = $state<string[]>(initialFilters?.equipment ?? []);
	let selectedDifficulties = $state<number[]>(initialFilters?.difficulties ?? []);
	let selectedTags = $state<string[]>(initialFilters?.tags ?? []);

	// Sync with initial filters when modal opens
	$effect(() => {
		if (open && initialFilters) {
			selectedEquipment = [...initialFilters.equipment];
			selectedDifficulties = [...initialFilters.difficulties];
			selectedTags = [...initialFilters.tags];
		}
	});

	// Filter options
	const EQUIPMENT_OPTIONS = [
		{ id: 'none', label: 'Без снаряжения' },
		{ id: 'pullup-bar', label: 'Турник' },
		{ id: 'dip-bars', label: 'Брусья' },
		{ id: 'bench', label: 'Скамья' },
		{ id: 'wall', label: 'Стена' }
	];

	const MUSCLE_TAGS = [
		{ id: 'chest', label: 'Грудь' },
		{ id: 'back', label: 'Спина' },
		{ id: 'shoulders', label: 'Плечи' },
		{ id: 'triceps', label: 'Трицепс' },
		{ id: 'core', label: 'Кор' },
		{ id: 'quads', label: 'Ноги' },
		{ id: 'glutes', label: 'Ягодицы' },
		{ id: 'calves', label: 'Икры' },
		{ id: 'full-body', label: 'Всё тело' }
	];

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

	function handleReset() {
		telegram.hapticImpact('medium');
		selectedEquipment = [];
		selectedDifficulties = [];
		selectedTags = [];
	}

	function handleApply() {
		telegram.hapticImpact('medium');
		onApply({
			equipment: selectedEquipment,
			difficulties: selectedDifficulties,
			tags: selectedTags
		});
		onClose();
	}

	const activeCount = $derived(
		selectedEquipment.length + selectedDifficulties.length + selectedTags.length
	);
</script>

<PixelModal {open} title="Фильтры" onclose={onClose}>
	<div class="filter-sections">
		<!-- Equipment -->
		<div class="filter-section">
			<h4 class="section-label">Снаряжение</h4>
			<div class="filter-chips">
				{#each EQUIPMENT_OPTIONS as option}
					<button
						class="filter-chip"
						class:active={selectedEquipment.includes(option.id)}
						onclick={() => toggleEquipment(option.id)}
					>
						{option.label}
					</button>
				{/each}
			</div>
		</div>

		<!-- Difficulty -->
		<div class="filter-section">
			<h4 class="section-label">Сложность</h4>
			<div class="filter-chips difficulty-chips">
				{#each [1, 2, 3, 4, 5] as level}
					<button
						class="filter-chip difficulty-chip"
						class:active={selectedDifficulties.includes(level)}
						onclick={() => toggleDifficulty(level)}
					>
						{'\u2605'.repeat(level)}
					</button>
				{/each}
			</div>
		</div>

		<!-- Muscle tags -->
		<div class="filter-section">
			<h4 class="section-label">Группы мышц</h4>
			<div class="filter-chips">
				{#each MUSCLE_TAGS as tag}
					<button
						class="filter-chip"
						class:active={selectedTags.includes(tag.id)}
						onclick={() => toggleTag(tag.id)}
					>
						{tag.label}
					</button>
				{/each}
			</div>
		</div>
	</div>

	<div class="filter-actions">
		<PixelButton variant="ghost" onclick={handleReset} disabled={activeCount === 0}>
			Сбросить
		</PixelButton>
		<PixelButton variant="primary" onclick={handleApply}>
			Применить {#if activeCount > 0}({activeCount}){/if}
		</PixelButton>
	</div>
</PixelModal>

<style>
	.filter-sections {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-lg);
	}

	.filter-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.section-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
		margin: 0;
	}

	.filter-chips {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
	}

	.filter-chip {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.filter-chip:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.filter-chip.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		color: var(--pixel-bg);
	}

	.difficulty-chips {
		gap: var(--spacing-xs);
	}

	.difficulty-chip {
		font-size: 10px;
		letter-spacing: -1px;
		padding: var(--spacing-xs) var(--spacing-xs);
	}

	.filter-actions {
		display: flex;
		justify-content: space-between;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-lg);
		padding-top: var(--spacing-md);
		border-top: 2px solid var(--border-color);
	}
</style>
