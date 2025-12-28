<script lang="ts">
	interface Props {
		exercise: string;
		size?: 'sm' | 'md' | 'lg';
		autoplay?: boolean;
	}

	let { exercise, size = 'md', autoplay = true }: Props = $props();

	const sizeMap = {
		sm: 64,
		md: 128,
		lg: 192
	};

	const pixelSize = $derived(sizeMap[size]);

	// Animation frame (0-3 for 4-frame animation)
	let frame = $state(0);
	let direction = $state(1); // 1 = forward, -1 = backward

	$effect(() => {
		if (!autoplay) return;

		const interval = setInterval(() => {
			// Ping-pong animation: 0 -> 1 -> 2 -> 3 -> 2 -> 1 -> 0
			frame += direction;
			if (frame >= 3) {
				direction = -1;
			} else if (frame <= 0) {
				direction = 1;
			}
		}, 400); // 2.5 FPS for smooth pixel animation

		return () => clearInterval(interval);
	});
</script>

<div class="exercise-demo" style="--size: {pixelSize}px">
	{#if exercise === 'squat-regular' || exercise === 'squat'}
		<!-- Приседания: 4 кадра анимации -->
		<svg viewBox="0 0 64 80" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Стоя прямо (исходное положение) -->
				<!-- Голова -->
				<rect x="26" y="4" width="12" height="12" fill="var(--pixel-skin)"/>
				<!-- Глаза -->
				<rect x="28" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="34" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<!-- Волосы -->
				<rect x="26" y="2" width="12" height="4" fill="var(--pixel-hair)"/>
				<rect x="24" y="4" width="2" height="6" fill="var(--pixel-hair)"/>
				<rect x="38" y="4" width="2" height="6" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="29" y="16" width="6" height="2" fill="var(--pixel-skin)"/>

				<!-- Туловище (футболка) -->
				<rect x="22" y="18" width="20" height="16" fill="var(--pixel-shirt)"/>
				<!-- Рукава -->
				<rect x="18" y="18" width="4" height="8" fill="var(--pixel-shirt)"/>
				<rect x="42" y="18" width="4" height="8" fill="var(--pixel-shirt)"/>

				<!-- Руки (вперёд для баланса) -->
				<rect x="14" y="20" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="46" y="20" width="4" height="4" fill="var(--pixel-skin)"/>

				<!-- Шорты -->
				<rect x="24" y="34" width="16" height="8" fill="var(--pixel-shorts)"/>

				<!-- Ноги -->
				<rect x="24" y="42" width="6" height="18" fill="var(--pixel-skin)"/>
				<rect x="34" y="42" width="6" height="18" fill="var(--pixel-skin)"/>

				<!-- Кроссовки -->
				<rect x="22" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>
				<rect x="32" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>
				<rect x="22" y="62" width="2" height="2" fill="var(--pixel-shoes-light)"/>
				<rect x="40" y="62" width="2" height="2" fill="var(--pixel-shoes-light)"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало приседа (колени сгибаются) -->
				<!-- Голова (чуть ниже) -->
				<rect x="26" y="8" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="28" y="12" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="34" y="12" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="26" y="6" width="12" height="4" fill="var(--pixel-hair)"/>
				<rect x="24" y="8" width="2" height="6" fill="var(--pixel-hair)"/>
				<rect x="38" y="8" width="2" height="6" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="29" y="20" width="6" height="2" fill="var(--pixel-skin)"/>

				<!-- Туловище (наклон вперёд) -->
				<rect x="22" y="22" width="20" height="14" fill="var(--pixel-shirt)"/>
				<rect x="18" y="22" width="4" height="8" fill="var(--pixel-shirt)"/>
				<rect x="42" y="22" width="4" height="8" fill="var(--pixel-shirt)"/>

				<!-- Руки вперёд -->
				<rect x="12" y="24" width="6" height="4" fill="var(--pixel-skin)"/>
				<rect x="46" y="24" width="6" height="4" fill="var(--pixel-skin)"/>

				<!-- Шорты -->
				<rect x="24" y="36" width="16" height="8" fill="var(--pixel-shorts)"/>

				<!-- Ноги (начинают сгибаться) -->
				<rect x="22" y="44" width="6" height="8" fill="var(--pixel-skin)"/>
				<rect x="36" y="44" width="6" height="8" fill="var(--pixel-skin)"/>
				<!-- Голени -->
				<rect x="20" y="52" width="6" height="10" fill="var(--pixel-skin)"/>
				<rect x="38" y="52" width="6" height="10" fill="var(--pixel-skin)"/>

				<!-- Кроссовки -->
				<rect x="18" y="62" width="10" height="4" fill="var(--pixel-shoes)"/>
				<rect x="36" y="62" width="10" height="4" fill="var(--pixel-shoes)"/>

			{:else if frame === 2}
				<!-- Кадр 3: Полуприсед -->
				<!-- Голова (ещё ниже) -->
				<rect x="26" y="14" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="28" y="18" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="34" y="18" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="26" y="12" width="12" height="4" fill="var(--pixel-hair)"/>
				<rect x="24" y="14" width="2" height="6" fill="var(--pixel-hair)"/>
				<rect x="38" y="14" width="2" height="6" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="29" y="26" width="6" height="2" fill="var(--pixel-skin)"/>

				<!-- Туловище (больший наклон) -->
				<rect x="22" y="28" width="20" height="12" fill="var(--pixel-shirt)"/>
				<rect x="18" y="28" width="4" height="8" fill="var(--pixel-shirt)"/>
				<rect x="42" y="28" width="4" height="8" fill="var(--pixel-shirt)"/>

				<!-- Руки вытянуты вперёд -->
				<rect x="8" y="28" width="10" height="4" fill="var(--pixel-skin)"/>
				<rect x="46" y="28" width="10" height="4" fill="var(--pixel-skin)"/>

				<!-- Шорты -->
				<rect x="22" y="40" width="20" height="8" fill="var(--pixel-shorts)"/>

				<!-- Бёдра (согнуты) -->
				<rect x="18" y="48" width="10" height="6" fill="var(--pixel-skin)"/>
				<rect x="36" y="48" width="10" height="6" fill="var(--pixel-skin)"/>
				<!-- Голени -->
				<rect x="16" y="54" width="6" height="10" fill="var(--pixel-skin)"/>
				<rect x="42" y="54" width="6" height="10" fill="var(--pixel-skin)"/>

				<!-- Кроссовки -->
				<rect x="14" y="64" width="10" height="4" fill="var(--pixel-shoes)"/>
				<rect x="40" y="64" width="10" height="4" fill="var(--pixel-shoes)"/>

			{:else}
				<!-- Кадр 4: Полный присед (бёдра параллельно полу) -->
				<!-- Голова (самое низкое положение) -->
				<rect x="26" y="20" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="28" y="24" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="34" y="24" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="26" y="18" width="12" height="4" fill="var(--pixel-hair)"/>
				<rect x="24" y="20" width="2" height="6" fill="var(--pixel-hair)"/>
				<rect x="38" y="20" width="2" height="6" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="29" y="32" width="6" height="2" fill="var(--pixel-skin)"/>

				<!-- Туловище (вертикально, грудь вперёд) -->
				<rect x="24" y="34" width="16" height="12" fill="var(--pixel-shirt)"/>
				<rect x="20" y="34" width="4" height="8" fill="var(--pixel-shirt)"/>
				<rect x="40" y="34" width="4" height="8" fill="var(--pixel-shirt)"/>

				<!-- Руки вытянуты вперёд для баланса -->
				<rect x="4" y="34" width="16" height="4" fill="var(--pixel-skin)"/>
				<rect x="44" y="34" width="16" height="4" fill="var(--pixel-skin)"/>

				<!-- Шорты (растянуты) -->
				<rect x="20" y="46" width="24" height="6" fill="var(--pixel-shorts)"/>

				<!-- Бёдра (параллельно полу) -->
				<rect x="14" y="52" width="14" height="6" fill="var(--pixel-skin)"/>
				<rect x="36" y="52" width="14" height="6" fill="var(--pixel-skin)"/>
				<!-- Голени (вертикально) -->
				<rect x="12" y="58" width="6" height="8" fill="var(--pixel-skin)"/>
				<rect x="46" y="58" width="6" height="8" fill="var(--pixel-skin)"/>

				<!-- Кроссовки (шире для устойчивости) -->
				<rect x="8" y="66" width="12" height="4" fill="var(--pixel-shoes)"/>
				<rect x="44" y="66" width="12" height="4" fill="var(--pixel-shoes)"/>

				<!-- Индикатор: колени не выходят за носки -->
				<rect x="10" y="58" width="2" height="12" fill="var(--pixel-guide)" opacity="0.5"/>
				<rect x="52" y="58" width="2" height="12" fill="var(--pixel-guide)" opacity="0.5"/>
			{/if}
		</svg>

		<!-- Подсказки по технике -->
		<div class="tips">
			{#if frame === 0}
				<span class="tip">Ноги на ширине плеч</span>
			{:else if frame === 1}
				<span class="tip">Отводи таз назад</span>
			{:else if frame === 2}
				<span class="tip">Спина прямая</span>
			{:else}
				<span class="tip">Бёдра параллельны полу</span>
			{/if}
		</div>
	{:else}
		<!-- Заглушка для других упражнений -->
		<div class="placeholder">
			<span>?</span>
		</div>
	{/if}
</div>

<style>
	.exercise-demo {
		width: var(--size);
		height: calc(var(--size) * 1.3);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.pixel-figure {
		width: 100%;
		height: auto;
		image-rendering: pixelated;
		image-rendering: crisp-edges;

		/* Цвета персонажа */
		--pixel-skin: #ffdbac;
		--pixel-hair: #4a3728;
		--pixel-dark: #1a1a2e;
		--pixel-shirt: #e63946;
		--pixel-shorts: #2a2a4e;
		--pixel-shoes: #f8f8f8;
		--pixel-shoes-light: #cccccc;
		--pixel-guide: #00ff00;
	}

	.tips {
		text-align: center;
		min-height: 24px;
	}

	.tip {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
		text-transform: uppercase;
		animation: fadeIn 0.3s ease-out;
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	.placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
	}

	.placeholder span {
		font-size: var(--font-size-2xl);
		color: var(--text-muted);
	}
</style>
