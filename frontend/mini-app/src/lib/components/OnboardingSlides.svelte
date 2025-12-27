<script lang="ts">
	import { PixelButton, PixelIcon } from '$lib/components/ui';
	import { telegram } from '$lib/stores/telegram.svelte';

	interface Props {
		onComplete: () => void;
	}

	let { onComplete }: Props = $props();

	const slides = [
		{
			icon: 'dumbbell',
			title: 'Тренируйся',
			description: 'Выполняй упражнения без оборудования где угодно. Отжимания, приседания, планка и другие.',
			color: 'var(--pixel-red)'
		},
		{
			icon: 'xp',
			title: 'Получай XP',
			description: 'За каждое повторение ты получаешь опыт. Прокачивай уровень и открывай новые упражнения.',
			color: 'var(--pixel-blue)'
		},
		{
			icon: 'streak',
			title: 'Держи серию',
			description: 'Тренируйся каждый день и получай бонусы к XP. Не пропускай ни одного дня!',
			color: 'var(--pixel-yellow)'
		},
		{
			icon: 'trophy',
			title: 'Получай награды',
			description: 'Разблокируй достижения и соревнуйся с друзьями в таблице лидеров.',
			color: 'var(--pixel-green)'
		}
	];

	let currentSlide = $state(0);

	function nextSlide() {
		telegram.hapticImpact('light');
		if (currentSlide < slides.length - 1) {
			currentSlide++;
		} else {
			onComplete();
		}
	}

	function prevSlide() {
		telegram.hapticImpact('light');
		if (currentSlide > 0) {
			currentSlide--;
		}
	}

	function goToSlide(index: number) {
		telegram.hapticImpact('light');
		currentSlide = index;
	}

	function skip() {
		telegram.hapticImpact('medium');
		onComplete();
	}

	const isLastSlide = $derived(currentSlide === slides.length - 1);
</script>

<div class="slides-container">
	<button class="skip-btn" onclick={skip}>
		Пропустить
	</button>

	<div class="slide" style="--slide-color: {slides[currentSlide].color}">
		<div class="slide-icon">
			{#if slides[currentSlide].icon === 'dumbbell'}
				<svg viewBox="0 0 64 64" class="pixel-art-icon">
					<!-- Dumbbell pixel art -->
					<rect x="8" y="24" width="8" height="16" fill="currentColor"/>
					<rect x="16" y="20" width="4" height="24" fill="currentColor"/>
					<rect x="20" y="28" width="24" height="8" fill="currentColor"/>
					<rect x="44" y="20" width="4" height="24" fill="currentColor"/>
					<rect x="48" y="24" width="8" height="16" fill="currentColor"/>
				</svg>
			{:else if slides[currentSlide].icon === 'xp'}
				<svg viewBox="0 0 64 64" class="pixel-art-icon">
					<!-- XP star pixel art -->
					<polygon points="32,4 38,24 58,24 42,38 48,58 32,46 16,58 22,38 6,24 26,24" fill="currentColor"/>
					<rect x="26" y="28" width="12" height="4" fill="var(--pixel-bg)"/>
					<rect x="28" y="32" width="8" height="4" fill="var(--pixel-bg)"/>
				</svg>
			{:else if slides[currentSlide].icon === 'streak'}
				<svg viewBox="0 0 64 64" class="pixel-art-icon">
					<!-- Fire/streak pixel art -->
					<rect x="28" y="8" width="8" height="4" fill="currentColor"/>
					<rect x="24" y="12" width="16" height="4" fill="currentColor"/>
					<rect x="20" y="16" width="24" height="4" fill="currentColor"/>
					<rect x="16" y="20" width="32" height="8" fill="currentColor"/>
					<rect x="16" y="28" width="32" height="8" fill="currentColor"/>
					<rect x="20" y="36" width="24" height="8" fill="currentColor"/>
					<rect x="24" y="44" width="16" height="8" fill="currentColor"/>
					<rect x="28" y="52" width="8" height="4" fill="currentColor"/>
					<!-- Inner flame -->
					<rect x="28" y="28" width="8" height="4" fill="var(--pixel-red)"/>
					<rect x="26" y="32" width="12" height="8" fill="var(--pixel-red)"/>
					<rect x="28" y="40" width="8" height="4" fill="var(--pixel-red)"/>
				</svg>
			{:else if slides[currentSlide].icon === 'trophy'}
				<svg viewBox="0 0 64 64" class="pixel-art-icon">
					<!-- Trophy pixel art -->
					<rect x="20" y="8" width="24" height="4" fill="currentColor"/>
					<rect x="16" y="12" width="32" height="4" fill="currentColor"/>
					<rect x="8" y="16" width="12" height="12" fill="currentColor"/>
					<rect x="16" y="16" width="32" height="16" fill="currentColor"/>
					<rect x="44" y="16" width="12" height="12" fill="currentColor"/>
					<rect x="20" y="32" width="24" height="4" fill="currentColor"/>
					<rect x="24" y="36" width="16" height="4" fill="currentColor"/>
					<rect x="28" y="40" width="8" height="8" fill="currentColor"/>
					<rect x="20" y="48" width="24" height="4" fill="currentColor"/>
					<rect x="16" y="52" width="32" height="4" fill="currentColor"/>
					<!-- Star on trophy -->
					<polygon points="32,18 34,22 38,22 35,25 36,29 32,27 28,29 29,25 26,22 30,22" fill="var(--pixel-bg)"/>
				</svg>
			{/if}
		</div>

		<h1 class="slide-title">{slides[currentSlide].title}</h1>
		<p class="slide-description">{slides[currentSlide].description}</p>
	</div>

	<div class="dots">
		{#each slides as _, index}
			<button
				class="dot"
				class:active={index === currentSlide}
				onclick={() => goToSlide(index)}
				aria-label="Слайд {index + 1}"
			></button>
		{/each}
	</div>

	<div class="navigation">
		{#if currentSlide > 0}
			<PixelButton variant="ghost" onclick={prevSlide}>
				<PixelIcon name="back" size="sm" />
				Назад
			</PixelButton>
		{:else}
			<div></div>
		{/if}

		<PixelButton
			variant={isLastSlide ? 'success' : 'primary'}
			onclick={nextSlide}
		>
			{isLastSlide ? 'Выбрать персонажа' : 'Далее'}
			{#if !isLastSlide}
				<PixelIcon name="arrow-right" size="sm" />
			{/if}
		</PixelButton>
	</div>
</div>

<style>
	.slides-container {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-lg);
		background: var(--pixel-bg);
		position: relative;
	}

	.skip-btn {
		position: absolute;
		top: var(--spacing-lg);
		right: var(--spacing-lg);
		background: none;
		border: none;
		color: var(--text-muted);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		cursor: pointer;
		padding: var(--spacing-sm);
		transition: color var(--transition-fast);
	}

	.skip-btn:hover {
		color: var(--text-secondary);
	}

	.slide {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		max-width: 320px;
		animation: slideIn 0.3s ease-out;
	}

	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateX(20px);
		}
		to {
			opacity: 1;
			transform: translateX(0);
		}
	}

	.slide-icon {
		width: 120px;
		height: 120px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: var(--spacing-xl);
		color: var(--slide-color);
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.05); }
	}

	.pixel-art-icon {
		width: 100%;
		height: 100%;
		image-rendering: pixelated;
	}

	.slide-title {
		font-size: var(--font-size-xl);
		color: var(--slide-color);
		margin: 0 0 var(--spacing-md) 0;
		text-transform: uppercase;
		letter-spacing: 2px;
	}

	.slide-description {
		font-size: var(--font-size-md);
		color: var(--text-secondary);
		margin: 0;
		line-height: 1.6;
	}

	.dots {
		display: flex;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-xl);
		margin-bottom: var(--spacing-xl);
	}

	.dot {
		width: 12px;
		height: 12px;
		background: var(--border-color);
		border: 2px solid var(--border-color);
		cursor: pointer;
		transition: all var(--transition-fast);
		padding: 0;
	}

	.dot:hover {
		background: var(--text-muted);
	}

	.dot.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent);
		transform: scale(1.2);
	}

	.navigation {
		display: flex;
		justify-content: space-between;
		align-items: center;
		width: 100%;
		max-width: 320px;
		gap: var(--spacing-md);
	}
</style>
