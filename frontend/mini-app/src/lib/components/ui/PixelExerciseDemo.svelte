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

		<!-- Подсказка по технике -->
		<div class="tips">
			<span class="tip">Спина прямая, колени не выходят за носки</span>
		</div>
	{:else if exercise === 'pushup-regular' || exercise === 'pushup'}
		<!-- Отжимания: 4 кадра анимации (вид сбоку) -->
		<svg viewBox="0 0 80 50" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Верхнее положение (руки выпрямлены) -->
				<!-- Голова -->
				<rect x="8" y="10" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="13" width="2" height="2" fill="var(--pixel-dark)"/>
				<!-- Волосы -->
				<rect x="8" y="8" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="16" y="14" width="4" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище (горизонтально, прямая линия) -->
				<rect x="18" y="12" width="30" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз/шорты -->
				<rect x="48" y="12" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Руки (выпрямлены, держат тело) -->
				<rect x="22" y="22" width="4" height="14" fill="var(--pixel-skin)"/>
				<rect x="36" y="22" width="4" height="14" fill="var(--pixel-skin)"/>

				<!-- Ладони на полу -->
				<rect x="20" y="36" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="34" y="36" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Ноги (прямые, на носках) -->
				<rect x="58" y="14" width="16" height="6" fill="var(--pixel-skin)"/>

				<!-- Носки на полу -->
				<rect x="72" y="20" width="6" height="4" fill="var(--pixel-shoes)"/>
				<rect x="72" y="36" width="6" height="4" fill="var(--pixel-shoes)"/>
				<rect x="72" y="20" width="6" height="20" fill="var(--pixel-skin)"/>

				<!-- Пол -->
				<rect x="0" y="40" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало опускания -->
				<!-- Голова (чуть ниже) -->
				<rect x="8" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="17" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="8" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="16" y="18" width="4" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище (немного наклонено) -->
				<rect x="18" y="16" width="30" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="48" y="14" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Руки (слегка согнуты) -->
				<rect x="22" y="26" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="36" y="26" width="4" height="10" fill="var(--pixel-skin)"/>

				<!-- Ладони -->
				<rect x="20" y="36" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="34" y="36" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Ноги -->
				<rect x="58" y="16" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="22" width="6" height="18" fill="var(--pixel-skin)"/>
				<rect x="72" y="36" width="6" height="4" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="40" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Полуопускание -->
				<!-- Голова (ещё ниже) -->
				<rect x="8" y="20" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="23" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="8" y="18" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="16" y="24" width="4" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище -->
				<rect x="18" y="22" width="30" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="48" y="18" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Руки (сильнее согнуты) -->
				<rect x="22" y="32" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="36" y="32" width="4" height="4" fill="var(--pixel-skin)"/>
				<!-- Предплечья -->
				<rect x="20" y="28" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="34" y="28" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Ладони -->
				<rect x="20" y="36" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="34" y="36" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Ноги -->
				<rect x="58" y="20" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="26" width="6" height="14" fill="var(--pixel-skin)"/>
				<rect x="72" y="36" width="6" height="4" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="40" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Нижнее положение (грудь у пола) -->
				<!-- Голова (самое низкое) -->
				<rect x="6" y="26" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="29" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="24" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="14" y="30" width="4" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище (почти касается пола) -->
				<rect x="16" y="28" width="32" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз (чуть выше для правильной формы) -->
				<rect x="48" y="24" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Локти разведены в стороны -->
				<rect x="18" y="32" width="6" height="4" fill="var(--pixel-skin)"/>
				<rect x="38" y="32" width="6" height="4" fill="var(--pixel-skin)"/>

				<!-- Предплечья вертикально -->
				<rect x="20" y="36" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="38" y="36" width="4" height="4" fill="var(--pixel-skin)"/>

				<!-- Ладони -->
				<rect x="18" y="36" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="36" y="36" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Ноги -->
				<rect x="58" y="24" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="30" width="6" height="10" fill="var(--pixel-skin)"/>
				<rect x="72" y="36" width="6" height="4" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="40" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Тело прямое, локти под 45°</span>
		</div>

	{:else if exercise === 'pushup-knee'}
		<!-- Отжимания с колен: 4 кадра анимации (вид сбоку) -->
		<svg viewBox="0 0 70 50" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Верхнее положение -->
				<!-- Голова -->
				<rect x="6" y="8" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="11" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="6" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="14" y="12" width="4" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище (наклон от плеч к коленям) -->
				<rect x="16" y="10" width="24" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="40" y="12" width="8" height="10" fill="var(--pixel-shorts)"/>

				<!-- Руки (выпрямлены) -->
				<rect x="18" y="20" width="4" height="14" fill="var(--pixel-skin)"/>
				<rect x="30" y="20" width="4" height="14" fill="var(--pixel-skin)"/>

				<!-- Ладони -->
				<rect x="16" y="34" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="28" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Бёдра (вверх от колен) -->
				<rect x="46" y="18" width="6" height="10" fill="var(--pixel-skin)"/>

				<!-- Колени на полу -->
				<rect x="50" y="28" width="8" height="8" fill="var(--pixel-skin)"/>
				<rect x="50" y="34" width="10" height="4" fill="var(--pixel-shorts)"/>

				<!-- Голени (согнуты назад) -->
				<rect x="56" y="24" width="10" height="6" fill="var(--pixel-skin)"/>
				<rect x="64" y="20" width="4" height="8" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="38" width="70" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало опускания -->
				<rect x="6" y="12" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="15" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="10" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="14" y="16" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="14" width="24" height="10" fill="var(--pixel-shirt)"/>
				<rect x="40" y="14" width="8" height="10" fill="var(--pixel-shorts)"/>

				<rect x="18" y="24" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="30" y="24" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="16" y="34" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="28" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<rect x="46" y="20" width="6" height="8" fill="var(--pixel-skin)"/>
				<rect x="50" y="28" width="8" height="8" fill="var(--pixel-skin)"/>
				<rect x="50" y="34" width="10" height="4" fill="var(--pixel-shorts)"/>
				<rect x="56" y="24" width="10" height="6" fill="var(--pixel-skin)"/>
				<rect x="64" y="20" width="4" height="8" fill="var(--pixel-shoes)"/>

				<rect x="0" y="38" width="70" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Полуопускание -->
				<rect x="6" y="18" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="21" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="16" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="14" y="22" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="20" width="24" height="10" fill="var(--pixel-shirt)"/>
				<rect x="40" y="18" width="8" height="10" fill="var(--pixel-shorts)"/>

				<rect x="16" y="26" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="28" y="26" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="18" y="30" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="30" y="30" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="34" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="28" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<rect x="46" y="22" width="6" height="6" fill="var(--pixel-skin)"/>
				<rect x="50" y="28" width="8" height="8" fill="var(--pixel-skin)"/>
				<rect x="50" y="34" width="10" height="4" fill="var(--pixel-shorts)"/>
				<rect x="56" y="24" width="10" height="6" fill="var(--pixel-skin)"/>
				<rect x="64" y="20" width="4" height="8" fill="var(--pixel-shoes)"/>

				<rect x="0" y="38" width="70" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Нижнее положение -->
				<rect x="4" y="24" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="27" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="22" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="12" y="28" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="14" y="26" width="26" height="10" fill="var(--pixel-shirt)"/>
				<rect x="40" y="22" width="8" height="10" fill="var(--pixel-shorts)"/>

				<!-- Локти согнуты -->
				<rect x="14" y="30" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="30" y="30" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="34" width="6" height="4" fill="var(--pixel-skin)"/>
				<rect x="30" y="34" width="6" height="4" fill="var(--pixel-skin)"/>

				<rect x="46" y="24" width="6" height="4" fill="var(--pixel-skin)"/>
				<rect x="50" y="28" width="8" height="8" fill="var(--pixel-skin)"/>
				<rect x="50" y="34" width="10" height="4" fill="var(--pixel-shorts)"/>
				<rect x="56" y="24" width="10" height="6" fill="var(--pixel-skin)"/>
				<rect x="64" y="20" width="4" height="8" fill="var(--pixel-shoes)"/>

				<rect x="0" y="38" width="70" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Облегчённый вариант для начинающих</span>
		</div>

	{:else if exercise === 'pushup-diamond'}
		<!-- Отжимания узким хватом: 4 кадра анимации (вид сбоку) -->
		<svg viewBox="0 0 80 50" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Верхнее положение -->
				<!-- Голова -->
				<rect x="8" y="10" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="13" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="8" y="8" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="16" y="14" width="4" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище -->
				<rect x="18" y="12" width="30" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="48" y="12" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Руки УЗКИМ ХВАТОМ (близко друг к другу по центру) -->
				<rect x="28" y="22" width="4" height="14" fill="var(--pixel-skin)"/>
				<rect x="32" y="22" width="4" height="14" fill="var(--pixel-skin)"/>

				<!-- Ладони формируют "ромб" -->
				<rect x="26" y="36" width="12" height="4" fill="var(--pixel-skin)"/>
				<!-- Указатели на ромб -->
				<rect x="30" y="34" width="4" height="2" fill="var(--pixel-guide)" opacity="0.6"/>

				<!-- Ноги -->
				<rect x="58" y="14" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="20" width="6" height="20" fill="var(--pixel-skin)"/>
				<rect x="72" y="36" width="6" height="4" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="40" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало опускания -->
				<rect x="8" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="17" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="8" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="16" y="18" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="18" y="16" width="30" height="10" fill="var(--pixel-shirt)"/>
				<rect x="48" y="14" width="10" height="10" fill="var(--pixel-shorts)"/>

				<rect x="28" y="26" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="32" y="26" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="26" y="36" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="30" y="34" width="4" height="2" fill="var(--pixel-guide)" opacity="0.6"/>

				<rect x="58" y="16" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="22" width="6" height="18" fill="var(--pixel-skin)"/>
				<rect x="72" y="36" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="40" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Полуопускание -->
				<rect x="8" y="20" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="23" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="8" y="18" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="16" y="24" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="18" y="22" width="30" height="10" fill="var(--pixel-shirt)"/>
				<rect x="48" y="18" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Локти прижаты к телу -->
				<rect x="26" y="28" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="28" y="32" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="26" y="36" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="30" y="34" width="4" height="2" fill="var(--pixel-guide)" opacity="0.6"/>

				<rect x="58" y="20" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="26" width="6" height="14" fill="var(--pixel-skin)"/>
				<rect x="72" y="36" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="40" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Нижнее положение -->
				<rect x="6" y="26" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="29" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="24" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="14" y="30" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="28" width="32" height="10" fill="var(--pixel-shirt)"/>
				<rect x="48" y="24" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Локти прижаты к туловищу, руки вместе -->
				<rect x="24" y="32" width="16" height="4" fill="var(--pixel-skin)"/>
				<rect x="26" y="36" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="30" y="34" width="4" height="2" fill="var(--pixel-guide)" opacity="0.6"/>

				<rect x="58" y="24" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="30" width="6" height="10" fill="var(--pixel-skin)"/>
				<rect x="72" y="36" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="40" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Руки вместе, локти прижаты к телу</span>
		</div>

	{:else if exercise === 'superman'}
		<!-- Супермен: 4 кадра анимации (вид сбоку) -->
		<svg viewBox="0 0 80 45" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Лёжа на животе, руки и ноги на полу -->
				<!-- Голова (повёрнута в сторону) -->
				<rect x="4" y="22" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="26" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="20" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Руки вытянуты вперёд (на полу) -->
				<rect x="0" y="30" width="14" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище (лежит на полу) -->
				<rect x="14" y="26" width="30" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="44" y="26" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Ноги вытянуты назад (на полу) -->
				<rect x="54" y="28" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="28" width="6" height="6" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало подъёма -->
				<!-- Голова поднимается -->
				<rect x="4" y="18" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="22" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="16" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Руки начинают подниматься -->
				<rect x="0" y="24" width="14" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище слегка прогибается -->
				<rect x="14" y="26" width="30" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="44" y="28" width="10" height="8" fill="var(--pixel-shorts)"/>

				<!-- Ноги начинают подниматься -->
				<rect x="54" y="26" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="24" width="6" height="6" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Средний подъём -->
				<!-- Голова выше -->
				<rect x="4" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="18" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Руки подняты -->
				<rect x="0" y="18" width="14" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище прогнуто -->
				<rect x="14" y="24" width="30" height="12" fill="var(--pixel-shirt)"/>

				<!-- Таз на полу -->
				<rect x="44" y="30" width="10" height="6" fill="var(--pixel-shorts)"/>

				<!-- Ноги подняты -->
				<rect x="54" y="22" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="18" width="6" height="6" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Максимальный подъём (поза супермена) -->
				<!-- Голова максимально поднята -->
				<rect x="2" y="10" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="4" y="14" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="2" y="8" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Руки максимально подняты -->
				<rect x="0" y="12" width="12" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище сильно прогнуто -->
				<rect x="12" y="20" width="32" height="14" fill="var(--pixel-shirt)"/>

				<!-- Таз на полу (точка опоры) -->
				<rect x="44" y="32" width="10" height="4" fill="var(--pixel-shorts)"/>

				<!-- Ноги максимально подняты -->
				<rect x="54" y="16" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="12" width="6" height="6" fill="var(--pixel-shoes)"/>

				<!-- Пол -->
				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Одновременно поднимай руки и ноги</span>
		</div>

	{:else if exercise === 'superman-twist'}
		<!-- Супермен с поворотом: 4 кадра анимации -->
		<svg viewBox="0 0 80 45" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Исходная позиция супермена (поднят) -->
				<rect x="2" y="10" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="4" y="14" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="2" y="8" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Руки вперёд -->
				<rect x="0" y="12" width="12" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище прогнуто -->
				<rect x="12" y="20" width="32" height="14" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="44" y="32" width="10" height="4" fill="var(--pixel-shorts)"/>

				<!-- Ноги подняты -->
				<rect x="54" y="16" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="12" width="6" height="6" fill="var(--pixel-shoes)"/>

				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало поворота влево -->
				<rect x="4" y="8" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="12" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="6" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Левая рука вверх, правая вниз -->
				<rect x="0" y="8" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="12" y="16" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище с поворотом -->
				<rect x="16" y="18" width="28" height="14" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="44" y="30" width="10" height="6" fill="var(--pixel-shorts)"/>

				<!-- Ноги -->
				<rect x="54" y="18" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="14" width="6" height="6" fill="var(--pixel-shoes)"/>

				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Максимальный поворот влево -->
				<rect x="6" y="6" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="10" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="4" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Рука тянется к потолку -->
				<rect x="2" y="4" width="6" height="10" fill="var(--pixel-skin)"/>
				<!-- Другая рука к полу -->
				<rect x="14" y="18" width="6" height="8" fill="var(--pixel-skin)"/>

				<!-- Туловище повёрнуто -->
				<rect x="18" y="16" width="26" height="16" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="44" y="28" width="10" height="8" fill="var(--pixel-shorts)"/>

				<!-- Ноги -->
				<rect x="54" y="20" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="16" width="6" height="6" fill="var(--pixel-shoes)"/>

				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Возврат к центру (другая сторона) -->
				<rect x="4" y="10" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="14" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="8" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Руки симметрично -->
				<rect x="0" y="14" width="12" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище -->
				<rect x="12" y="20" width="32" height="14" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="44" y="32" width="10" height="4" fill="var(--pixel-shorts)"/>

				<!-- Ноги -->
				<rect x="54" y="18" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="14" width="6" height="6" fill="var(--pixel-shoes)"/>

				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Поворачивай корпус в стороны</span>
		</div>

	{:else if exercise === 'squat-sumo'}
		<!-- Приседания сумо: широкая стойка, носки наружу -->
		<svg viewBox="0 0 72 80" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Широкая стойка -->
				<!-- Голова -->
				<rect x="30" y="4" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="32" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="38" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="30" y="2" width="12" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="33" y="16" width="6" height="2" fill="var(--pixel-skin)"/>

				<!-- Туловище -->
				<rect x="26" y="18" width="20" height="16" fill="var(--pixel-shirt)"/>
				<rect x="22" y="18" width="4" height="8" fill="var(--pixel-shirt)"/>
				<rect x="46" y="18" width="4" height="8" fill="var(--pixel-shirt)"/>

				<!-- Руки на бёдрах -->
				<rect x="18" y="26" width="4" height="8" fill="var(--pixel-skin)"/>
				<rect x="50" y="26" width="4" height="8" fill="var(--pixel-skin)"/>

				<!-- Шорты -->
				<rect x="26" y="34" width="20" height="8" fill="var(--pixel-shorts)"/>

				<!-- Ноги широко расставлены -->
				<rect x="18" y="42" width="8" height="18" fill="var(--pixel-skin)"/>
				<rect x="46" y="42" width="8" height="18" fill="var(--pixel-skin)"/>

				<!-- Кроссовки (носки наружу) -->
				<rect x="12" y="60" width="14" height="4" fill="var(--pixel-shoes)"/>
				<rect x="46" y="60" width="14" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="64" width="72" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало приседа -->
				<rect x="30" y="10" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="32" y="14" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="38" y="14" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="30" y="8" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="33" y="22" width="6" height="2" fill="var(--pixel-skin)"/>
				<rect x="26" y="24" width="20" height="14" fill="var(--pixel-shirt)"/>
				<rect x="22" y="24" width="4" height="8" fill="var(--pixel-shirt)"/>
				<rect x="46" y="24" width="4" height="8" fill="var(--pixel-shirt)"/>

				<rect x="16" y="30" width="6" height="8" fill="var(--pixel-skin)"/>
				<rect x="50" y="30" width="6" height="8" fill="var(--pixel-skin)"/>

				<rect x="24" y="38" width="24" height="8" fill="var(--pixel-shorts)"/>

				<!-- Бёдра сгибаются наружу -->
				<rect x="14" y="46" width="10" height="8" fill="var(--pixel-skin)"/>
				<rect x="48" y="46" width="10" height="8" fill="var(--pixel-skin)"/>
				<rect x="12" y="54" width="8" height="8" fill="var(--pixel-skin)"/>
				<rect x="52" y="54" width="8" height="8" fill="var(--pixel-skin)"/>

				<rect x="8" y="62" width="14" height="4" fill="var(--pixel-shoes)"/>
				<rect x="50" y="62" width="14" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="66" width="72" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Полуприсед -->
				<rect x="30" y="18" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="32" y="22" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="38" y="22" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="30" y="16" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="33" y="30" width="6" height="2" fill="var(--pixel-skin)"/>
				<rect x="26" y="32" width="20" height="12" fill="var(--pixel-shirt)"/>
				<rect x="22" y="32" width="4" height="8" fill="var(--pixel-shirt)"/>
				<rect x="46" y="32" width="4" height="8" fill="var(--pixel-shirt)"/>

				<rect x="14" y="36" width="8" height="6" fill="var(--pixel-skin)"/>
				<rect x="50" y="36" width="8" height="6" fill="var(--pixel-skin)"/>

				<rect x="22" y="44" width="28" height="8" fill="var(--pixel-shorts)"/>

				<!-- Колени широко разведены -->
				<rect x="10" y="52" width="12" height="6" fill="var(--pixel-skin)"/>
				<rect x="50" y="52" width="12" height="6" fill="var(--pixel-skin)"/>
				<rect x="6" y="58" width="10" height="8" fill="var(--pixel-skin)"/>
				<rect x="56" y="58" width="10" height="8" fill="var(--pixel-skin)"/>

				<rect x="2" y="66" width="16" height="4" fill="var(--pixel-shoes)"/>
				<rect x="54" y="66" width="16" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="70" width="72" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Глубокий присед сумо -->
				<rect x="30" y="26" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="32" y="30" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="38" y="30" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="30" y="24" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="33" y="38" width="6" height="2" fill="var(--pixel-skin)"/>
				<rect x="26" y="40" width="20" height="10" fill="var(--pixel-shirt)"/>
				<rect x="22" y="40" width="4" height="6" fill="var(--pixel-shirt)"/>
				<rect x="46" y="40" width="4" height="6" fill="var(--pixel-shirt)"/>

				<!-- Руки на коленях -->
				<rect x="12" y="44" width="10" height="4" fill="var(--pixel-skin)"/>
				<rect x="50" y="44" width="10" height="4" fill="var(--pixel-skin)"/>

				<rect x="20" y="50" width="32" height="6" fill="var(--pixel-shorts)"/>

				<!-- Бёдра параллельны полу, колени широко -->
				<rect x="6" y="56" width="14" height="6" fill="var(--pixel-skin)"/>
				<rect x="52" y="56" width="14" height="6" fill="var(--pixel-skin)"/>
				<rect x="2" y="62" width="10" height="8" fill="var(--pixel-skin)"/>
				<rect x="60" y="62" width="10" height="8" fill="var(--pixel-skin)"/>

				<rect x="0" y="70" width="14" height="4" fill="var(--pixel-shoes)"/>
				<rect x="58" y="70" width="14" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="74" width="72" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Широкая стойка, колени по направлению носков</span>
		</div>

	{:else if exercise === 'lunge-stationary'}
		<!-- Выпады на месте: 4 кадра анимации (вид сбоку) -->
		<svg viewBox="0 0 64 70" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Исходная позиция - шаг вперёд -->
				<!-- Голова -->
				<rect x="24" y="2" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="26" y="5" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="0" width="10" height="3" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="27" y="12" width="4" height="2" fill="var(--pixel-skin)"/>

				<!-- Туловище вертикально -->
				<rect x="22" y="14" width="14" height="14" fill="var(--pixel-shirt)"/>

				<!-- Руки на поясе -->
				<rect x="18" y="16" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="36" y="16" width="4" height="10" fill="var(--pixel-skin)"/>

				<!-- Шорты -->
				<rect x="22" y="28" width="14" height="6" fill="var(--pixel-shorts)"/>

				<!-- Передняя нога (шаг вперёд, прямая) -->
				<rect x="8" y="34" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="4" y="40" width="8" height="18" fill="var(--pixel-skin)"/>
				<rect x="2" y="58" width="12" height="4" fill="var(--pixel-shoes)"/>

				<!-- Задняя нога (назад, прямая) -->
				<rect x="34" y="34" width="14" height="6" fill="var(--pixel-skin)"/>
				<rect x="44" y="40" width="8" height="18" fill="var(--pixel-skin)"/>
				<rect x="46" y="58" width="12" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="62" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало опускания -->
				<rect x="24" y="6" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="26" y="9" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="4" width="10" height="3" fill="var(--pixel-hair)"/>

				<rect x="27" y="16" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="18" width="14" height="14" fill="var(--pixel-shirt)"/>

				<rect x="18" y="20" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="36" y="20" width="4" height="10" fill="var(--pixel-skin)"/>

				<rect x="22" y="32" width="14" height="6" fill="var(--pixel-shorts)"/>

				<!-- Передняя нога сгибается -->
				<rect x="10" y="38" width="14" height="6" fill="var(--pixel-skin)"/>
				<rect x="4" y="44" width="8" height="14" fill="var(--pixel-skin)"/>
				<rect x="2" y="58" width="12" height="4" fill="var(--pixel-shoes)"/>

				<!-- Задняя нога сгибается, колено опускается -->
				<rect x="34" y="38" width="12" height="6" fill="var(--pixel-skin)"/>
				<rect x="42" y="44" width="8" height="8" fill="var(--pixel-skin)"/>
				<rect x="44" y="52" width="8" height="6" fill="var(--pixel-skin)"/>
				<rect x="48" y="58" width="10" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="62" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Глубже -->
				<rect x="24" y="12" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="26" y="15" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="10" width="10" height="3" fill="var(--pixel-hair)"/>

				<rect x="27" y="22" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="24" width="14" height="12" fill="var(--pixel-shirt)"/>

				<rect x="18" y="26" width="4" height="8" fill="var(--pixel-skin)"/>
				<rect x="36" y="26" width="4" height="8" fill="var(--pixel-skin)"/>

				<rect x="20" y="36" width="18" height="6" fill="var(--pixel-shorts)"/>

				<!-- Передняя нога - бедро почти параллельно -->
				<rect x="10" y="42" width="12" height="8" fill="var(--pixel-skin)"/>
				<rect x="4" y="50" width="8" height="8" fill="var(--pixel-skin)"/>
				<rect x="2" y="58" width="12" height="4" fill="var(--pixel-shoes)"/>

				<!-- Заднее колено низко -->
				<rect x="36" y="42" width="10" height="6" fill="var(--pixel-skin)"/>
				<rect x="42" y="48" width="8" height="6" fill="var(--pixel-skin)"/>
				<rect x="46" y="54" width="6" height="4" fill="var(--pixel-skin)"/>
				<rect x="48" y="58" width="10" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="62" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Нижняя точка - колено у пола -->
				<rect x="24" y="18" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="26" y="21" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="16" width="10" height="3" fill="var(--pixel-hair)"/>

				<rect x="27" y="28" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="30" width="14" height="10" fill="var(--pixel-shirt)"/>

				<rect x="18" y="32" width="4" height="6" fill="var(--pixel-skin)"/>
				<rect x="36" y="32" width="4" height="6" fill="var(--pixel-skin)"/>

				<rect x="18" y="40" width="22" height="6" fill="var(--pixel-shorts)"/>

				<!-- Передняя нога - бедро параллельно полу, голень вертикально -->
				<rect x="8" y="46" width="12" height="6" fill="var(--pixel-skin)"/>
				<rect x="4" y="52" width="6" height="6" fill="var(--pixel-skin)"/>
				<rect x="2" y="58" width="10" height="4" fill="var(--pixel-shoes)"/>

				<!-- Заднее колено касается пола -->
				<rect x="38" y="46" width="8" height="6" fill="var(--pixel-skin)"/>
				<rect x="44" y="52" width="6" height="6" fill="var(--pixel-skin)"/>
				<rect x="48" y="56" width="8" height="6" fill="var(--pixel-shoes)"/>

				<!-- Индикатор угла 90° -->
				<rect x="6" y="46" width="2" height="12" fill="var(--pixel-guide)" opacity="0.5"/>

				<rect x="0" y="62" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Колено под 90°, спина прямая</span>
		</div>

	{:else if exercise === 'plank'}
		<!-- Планка: статичная поза с анимацией таймера -->
		<svg viewBox="0 0 80 45" class="pixel-figure">
			<!-- Статичная поза планки -->
			<!-- Голова -->
			<rect x="6" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
			<rect x="8" y="17" width="2" height="2" fill="var(--pixel-dark)"/>
			<rect x="6" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

			<!-- Шея -->
			<rect x="14" y="18" width="4" height="4" fill="var(--pixel-skin)"/>

			<!-- Туловище (прямая линия) -->
			<rect x="16" y="16" width="34" height="10" fill="var(--pixel-shirt)"/>

			<!-- Таз -->
			<rect x="50" y="16" width="10" height="10" fill="var(--pixel-shorts)"/>

			<!-- Предплечья на полу (локтевая планка) -->
			<rect x="16" y="26" width="12" height="4" fill="var(--pixel-skin)"/>
			<rect x="16" y="30" width="4" height="6" fill="var(--pixel-skin)"/>
			<rect x="24" y="30" width="4" height="6" fill="var(--pixel-skin)"/>

			<!-- Кисти сжаты -->
			<rect x="14" y="32" width="6" height="4" fill="var(--pixel-skin)"/>
			<rect x="24" y="32" width="6" height="4" fill="var(--pixel-skin)"/>

			<!-- Ноги прямые -->
			<rect x="60" y="18" width="14" height="6" fill="var(--pixel-skin)"/>
			<rect x="72" y="24" width="6" height="12" fill="var(--pixel-skin)"/>
			<rect x="72" y="32" width="6" height="4" fill="var(--pixel-shoes)"/>

			<!-- Пол -->
			<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			<!-- Анимированный таймер/пульс -->
			{#if frame === 0 || frame === 2}
				<circle cx="40" cy="6" r="4" fill="var(--pixel-accent)" opacity="0.8"/>
			{:else}
				<circle cx="40" cy="6" r="3" fill="var(--pixel-accent)" opacity="0.5"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Тело прямое, напряги пресс</span>
		</div>

	{:else if exercise === 'plank-side'}
		<!-- Боковая планка: статичная поза (вид сбоку) -->
		<svg viewBox="0 0 70 45" class="pixel-figure">
			<!-- Голова (смотрит вперёд) -->
			<rect x="4" y="8" width="10" height="10" fill="var(--pixel-skin)"/>
			<rect x="6" y="11" width="2" height="2" fill="var(--pixel-dark)"/>
			<rect x="4" y="6" width="10" height="4" fill="var(--pixel-hair)"/>

			<!-- Шея -->
			<rect x="12" y="12" width="4" height="4" fill="var(--pixel-skin)"/>

			<!-- Туловище (диагональ от плеча к бедру) -->
			<rect x="14" y="14" width="26" height="10" fill="var(--pixel-shirt)"/>

			<!-- Верхняя рука вытянута вверх -->
			<rect x="20" y="4" width="4" height="12" fill="var(--pixel-skin)"/>

			<!-- Опорная рука (локоть на полу) -->
			<rect x="14" y="24" width="4" height="12" fill="var(--pixel-skin)"/>
			<rect x="12" y="36" width="8" height="4" fill="var(--pixel-skin)"/>

			<!-- Шорты/таз -->
			<rect x="40" y="18" width="10" height="8" fill="var(--pixel-shorts)"/>

			<!-- Ноги прямые (одна на другой) -->
			<rect x="50" y="20" width="16" height="6" fill="var(--pixel-skin)"/>
			<rect x="64" y="20" width="4" height="6" fill="var(--pixel-shoes)"/>

			<!-- Пол -->
			<rect x="0" y="40" width="70" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			<!-- Анимированный таймер -->
			{#if frame === 0 || frame === 2}
				<circle cx="22" cy="2" r="3" fill="var(--pixel-accent)" opacity="0.8"/>
			{:else}
				<circle cx="22" cy="2" r="2" fill="var(--pixel-accent)" opacity="0.5"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Тело прямое, таз не провисает</span>
		</div>

	{:else if exercise === 'bird-dog'}
		<!-- Птичий пёс: 4 кадра попеременного подъёма -->
		<svg viewBox="0 0 80 45" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: На четвереньках -->
				<!-- Голова -->
				<rect x="8" y="10" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="14" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="8" y="8" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Туловище горизонтально -->
				<rect x="18" y="14" width="30" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="48" y="14" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Руки (на полу) -->
				<rect x="20" y="24" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="32" y="24" width="4" height="10" fill="var(--pixel-skin)"/>
				<rect x="18" y="34" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="30" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Колени на полу -->
				<rect x="52" y="24" width="8" height="10" fill="var(--pixel-skin)"/>
				<rect x="64" y="24" width="8" height="10" fill="var(--pixel-skin)"/>
				<rect x="52" y="34" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="64" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<rect x="0" y="38" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало подъёма (правая рука + левая нога) -->
				<rect x="8" y="8" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="12" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="8" y="6" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="18" y="12" width="30" height="10" fill="var(--pixel-shirt)"/>
				<rect x="48" y="14" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Левая рука на полу -->
				<rect x="20" y="22" width="4" height="12" fill="var(--pixel-skin)"/>
				<rect x="18" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Правая рука поднимается -->
				<rect x="30" y="16" width="10" height="4" fill="var(--pixel-skin)"/>

				<!-- Правое колено на полу -->
				<rect x="64" y="24" width="8" height="10" fill="var(--pixel-skin)"/>
				<rect x="64" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Левая нога поднимается -->
				<rect x="52" y="20" width="14" height="4" fill="var(--pixel-skin)"/>

				<rect x="0" y="38" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Полный подъём (правая рука + левая нога вытянуты) -->
				<rect x="6" y="6" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="10" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="4" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="16" y="10" width="32" height="10" fill="var(--pixel-shirt)"/>
				<rect x="48" y="14" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Левая рука на полу -->
				<rect x="20" y="20" width="4" height="14" fill="var(--pixel-skin)"/>
				<rect x="18" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Правая рука вытянута вперёд -->
				<rect x="0" y="10" width="16" height="4" fill="var(--pixel-skin)"/>

				<!-- Правое колено на полу -->
				<rect x="64" y="24" width="8" height="10" fill="var(--pixel-skin)"/>
				<rect x="64" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Левая нога вытянута назад -->
				<rect x="52" y="14" width="20" height="4" fill="var(--pixel-skin)"/>
				<rect x="70" y="12" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="38" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Возврат / подготовка к другой стороне -->
				<rect x="8" y="8" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="10" y="12" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="8" y="6" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="18" y="12" width="30" height="10" fill="var(--pixel-shirt)"/>
				<rect x="48" y="14" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Правая рука на полу -->
				<rect x="32" y="22" width="4" height="12" fill="var(--pixel-skin)"/>
				<rect x="30" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Левая рука поднимается -->
				<rect x="8" y="16" width="12" height="4" fill="var(--pixel-skin)"/>

				<!-- Левое колено на полу -->
				<rect x="52" y="24" width="8" height="10" fill="var(--pixel-skin)"/>
				<rect x="52" y="34" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Правая нога поднимается -->
				<rect x="64" y="18" width="14" height="4" fill="var(--pixel-skin)"/>

				<rect x="0" y="38" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Противоположные рука и нога, спина ровная</span>
		</div>

	{:else if exercise === 'child-pose'}
		<!-- Поза ребёнка: статичная расслабляющая поза -->
		<svg viewBox="0 0 70 40" class="pixel-figure">
			<!-- Руки вытянуты вперёд -->
			<rect x="2" y="18" width="20" height="4" fill="var(--pixel-skin)"/>

			<!-- Голова опущена -->
			<rect x="20" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
			<rect x="20" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

			<!-- Туловище согнуто -->
			<rect x="28" y="16" width="16" height="12" fill="var(--pixel-shirt)"/>

			<!-- Таз на пятках -->
			<rect x="44" y="18" width="12" height="10" fill="var(--pixel-shorts)"/>

			<!-- Ноги согнуты под себя -->
			<rect x="50" y="28" width="14" height="6" fill="var(--pixel-skin)"/>
			<rect x="62" y="26" width="6" height="8" fill="var(--pixel-shoes)"/>

			<!-- Пол -->
			<rect x="0" y="34" width="70" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			<!-- Анимированный символ расслабления -->
			{#if frame === 0}
				<text x="35" y="8" font-size="6" fill="var(--pixel-accent)" opacity="0.8">~</text>
			{:else if frame === 1}
				<text x="35" y="8" font-size="6" fill="var(--pixel-accent)" opacity="0.6">~</text>
			{:else if frame === 2}
				<text x="35" y="8" font-size="6" fill="var(--pixel-accent)" opacity="0.4">~</text>
			{:else}
				<text x="35" y="8" font-size="6" fill="var(--pixel-accent)" opacity="0.6">~</text>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Расслабься, дыши глубоко</span>
		</div>

	{:else if exercise === 'reverse-hyperextension' || exercise === 'hyperextension-reverse'}
		<!-- Обратная гиперэкстензия: лёжа на животе, подъём ног -->
		<svg viewBox="0 0 80 40" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Лёжа на животе, ноги на полу -->
				<!-- Голова -->
				<rect x="4" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="18" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<!-- Руки под подбородком -->
				<rect x="2" y="22" width="12" height="4" fill="var(--pixel-skin)"/>

				<!-- Туловище -->
				<rect x="14" y="20" width="28" height="10" fill="var(--pixel-shirt)"/>

				<!-- Таз -->
				<rect x="42" y="22" width="10" height="8" fill="var(--pixel-shorts)"/>

				<!-- Ноги на полу -->
				<rect x="52" y="24" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="70" y="24" width="6" height="6" fill="var(--pixel-shoes)"/>

				<rect x="0" y="30" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Начало подъёма ног -->
				<rect x="4" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="18" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="2" y="22" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="14" y="20" width="28" height="10" fill="var(--pixel-shirt)"/>
				<rect x="42" y="24" width="10" height="6" fill="var(--pixel-shorts)"/>

				<!-- Ноги начинают подниматься -->
				<rect x="52" y="20" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="70" y="18" width="6" height="6" fill="var(--pixel-shoes)"/>

				<rect x="0" y="30" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Ноги выше -->
				<rect x="4" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="18" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="2" y="22" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="14" y="20" width="28" height="10" fill="var(--pixel-shirt)"/>
				<rect x="42" y="26" width="10" height="4" fill="var(--pixel-shorts)"/>

				<!-- Ноги высоко -->
				<rect x="52" y="14" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="70" y="10" width="6" height="6" fill="var(--pixel-shoes)"/>

				<rect x="0" y="30" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Максимальный подъём -->
				<rect x="4" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="6" y="18" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="4" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="2" y="22" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="14" y="20" width="28" height="10" fill="var(--pixel-shirt)"/>
				<rect x="42" y="26" width="10" height="4" fill="var(--pixel-shorts)"/>

				<!-- Ноги максимально подняты -->
				<rect x="52" y="8" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="70" y="4" width="6" height="6" fill="var(--pixel-shoes)"/>

				<rect x="0" y="30" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Поднимай ноги, напрягая ягодицы</span>
		</div>

	{:else if exercise === 'plank-leg-raise' || exercise === 'plank-leg-lift'}
		<!-- Планка с подъёмом ноги -->
		<svg viewBox="0 0 80 45" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Планка, обе ноги на полу -->
				<rect x="6" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="17" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="14" y="18" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="16" width="34" height="10" fill="var(--pixel-shirt)"/>
				<rect x="50" y="16" width="10" height="10" fill="var(--pixel-shorts)"/>

				<!-- Предплечья -->
				<rect x="16" y="26" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="14" y="30" width="8" height="6" fill="var(--pixel-skin)"/>

				<!-- Обе ноги на полу -->
				<rect x="60" y="18" width="14" height="6" fill="var(--pixel-skin)"/>
				<rect x="72" y="24" width="6" height="12" fill="var(--pixel-skin)"/>
				<rect x="72" y="32" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Одна нога начинает подниматься -->
				<rect x="6" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="17" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="14" y="18" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="16" width="34" height="10" fill="var(--pixel-shirt)"/>
				<rect x="50" y="16" width="10" height="10" fill="var(--pixel-shorts)"/>

				<rect x="16" y="26" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="14" y="30" width="8" height="6" fill="var(--pixel-skin)"/>

				<!-- Нога поднимается -->
				<rect x="60" y="14" width="16" height="5" fill="var(--pixel-skin)"/>
				<rect x="74" y="12" width="4" height="5" fill="var(--pixel-shoes)"/>

				<!-- Опорная нога -->
				<rect x="60" y="22" width="6" height="4" fill="var(--pixel-skin)"/>
				<rect x="64" y="26" width="6" height="10" fill="var(--pixel-skin)"/>
				<rect x="64" y="32" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Нога максимально поднята -->
				<rect x="6" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="17" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="14" y="18" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="16" width="34" height="10" fill="var(--pixel-shirt)"/>
				<rect x="50" y="16" width="10" height="10" fill="var(--pixel-shorts)"/>

				<rect x="16" y="26" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="14" y="30" width="8" height="6" fill="var(--pixel-skin)"/>

				<!-- Нога максимально поднята -->
				<rect x="60" y="8" width="16" height="5" fill="var(--pixel-skin)"/>
				<rect x="74" y="6" width="4" height="5" fill="var(--pixel-shoes)"/>

				<!-- Опорная нога -->
				<rect x="60" y="22" width="6" height="4" fill="var(--pixel-skin)"/>
				<rect x="64" y="26" width="6" height="10" fill="var(--pixel-skin)"/>
				<rect x="64" y="32" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Смена ноги -->
				<rect x="6" y="14" width="10" height="10" fill="var(--pixel-skin)"/>
				<rect x="8" y="17" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="6" y="12" width="10" height="4" fill="var(--pixel-hair)"/>

				<rect x="14" y="18" width="4" height="4" fill="var(--pixel-skin)"/>
				<rect x="16" y="16" width="34" height="10" fill="var(--pixel-shirt)"/>
				<rect x="50" y="16" width="10" height="10" fill="var(--pixel-shorts)"/>

				<rect x="16" y="26" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="14" y="30" width="8" height="6" fill="var(--pixel-skin)"/>

				<!-- Обе ноги в среднем положении -->
				<rect x="60" y="16" width="16" height="5" fill="var(--pixel-skin)"/>
				<rect x="74" y="14" width="4" height="5" fill="var(--pixel-shoes)"/>

				<rect x="60" y="20" width="6" height="4" fill="var(--pixel-skin)"/>
				<rect x="64" y="24" width="6" height="12" fill="var(--pixel-skin)"/>
				<rect x="64" y="32" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="36" width="80" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Держи корпус стабильно, поднимай ногу</span>
		</div>

	{:else if exercise === 'butterfly' || exercise === 'butterfly-stretch'}
		<!-- Бабочка: сидя, колени разведены -->
		<svg viewBox="0 0 64 55" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Исходное положение -->
				<!-- Голова -->
				<rect x="24" y="2" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="26" y="6" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="32" y="6" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="0" width="12" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="28" y="14" width="4" height="2" fill="var(--pixel-skin)"/>

				<!-- Туловище (сидит прямо) -->
				<rect x="22" y="16" width="16" height="14" fill="var(--pixel-shirt)"/>

				<!-- Руки держат стопы -->
				<rect x="18" y="30" width="8" height="4" fill="var(--pixel-skin)"/>
				<rect x="34" y="30" width="8" height="4" fill="var(--pixel-skin)"/>

				<!-- Шорты -->
				<rect x="22" y="30" width="16" height="6" fill="var(--pixel-shorts)"/>

				<!-- Бёдра разведены (бабочка) -->
				<rect x="8" y="36" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="36" y="36" width="16" height="6" fill="var(--pixel-skin)"/>

				<!-- Голени -->
				<rect x="16" y="42" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="32" y="42" width="12" height="4" fill="var(--pixel-skin)"/>

				<!-- Стопы вместе -->
				<rect x="24" y="46" width="6" height="4" fill="var(--pixel-shoes)"/>
				<rect x="30" y="46" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="50" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Колени опускаются -->
				<rect x="24" y="2" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="26" y="6" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="32" y="6" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="0" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="28" y="14" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="16" width="16" height="14" fill="var(--pixel-shirt)"/>

				<rect x="16" y="32" width="10" height="4" fill="var(--pixel-skin)"/>
				<rect x="34" y="32" width="10" height="4" fill="var(--pixel-skin)"/>

				<rect x="22" y="30" width="16" height="6" fill="var(--pixel-shorts)"/>

				<!-- Бёдра ещё шире -->
				<rect x="4" y="38" width="18" height="6" fill="var(--pixel-skin)"/>
				<rect x="38" y="38" width="18" height="6" fill="var(--pixel-skin)"/>

				<rect x="14" y="44" width="14" height="4" fill="var(--pixel-skin)"/>
				<rect x="32" y="44" width="14" height="4" fill="var(--pixel-skin)"/>

				<rect x="24" y="46" width="6" height="4" fill="var(--pixel-shoes)"/>
				<rect x="30" y="46" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="50" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Максимальное раскрытие -->
				<rect x="24" y="2" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="26" y="6" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="32" y="6" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="0" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="28" y="14" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="16" width="16" height="14" fill="var(--pixel-shirt)"/>

				<rect x="14" y="34" width="12" height="4" fill="var(--pixel-skin)"/>
				<rect x="34" y="34" width="12" height="4" fill="var(--pixel-skin)"/>

				<rect x="22" y="30" width="16" height="6" fill="var(--pixel-shorts)"/>

				<!-- Колени максимально к полу -->
				<rect x="2" y="40" width="20" height="6" fill="var(--pixel-skin)"/>
				<rect x="38" y="40" width="20" height="6" fill="var(--pixel-skin)"/>

				<rect x="12" y="44" width="16" height="4" fill="var(--pixel-skin)"/>
				<rect x="32" y="44" width="16" height="4" fill="var(--pixel-skin)"/>

				<rect x="24" y="46" width="6" height="4" fill="var(--pixel-shoes)"/>
				<rect x="30" y="46" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="50" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Возврат -->
				<rect x="24" y="2" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="26" y="6" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="32" y="6" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="0" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="28" y="14" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="16" width="16" height="14" fill="var(--pixel-shirt)"/>

				<rect x="16" y="32" width="10" height="4" fill="var(--pixel-skin)"/>
				<rect x="34" y="32" width="10" height="4" fill="var(--pixel-skin)"/>

				<rect x="22" y="30" width="16" height="6" fill="var(--pixel-shorts)"/>

				<rect x="6" y="38" width="16" height="6" fill="var(--pixel-skin)"/>
				<rect x="38" y="38" width="16" height="6" fill="var(--pixel-skin)"/>

				<rect x="14" y="44" width="14" height="4" fill="var(--pixel-skin)"/>
				<rect x="32" y="44" width="14" height="4" fill="var(--pixel-skin)"/>

				<rect x="24" y="46" width="6" height="4" fill="var(--pixel-shoes)"/>
				<rect x="30" y="46" width="6" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="50" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Стопы вместе, колени к полу</span>
		</div>

	{:else if exercise === 'arm-circles' || exercise === 'arm-circle'}
		<!-- Круговые махи руками: вид спереди -->
		<svg viewBox="0 0 64 70" class="pixel-figure">
			{#if frame === 0}
				<!-- Кадр 1: Руки внизу -->
				<!-- Голова -->
				<rect x="24" y="4" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="26" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="32" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="2" width="12" height="4" fill="var(--pixel-hair)"/>

				<!-- Шея -->
				<rect x="28" y="16" width="4" height="2" fill="var(--pixel-skin)"/>

				<!-- Туловище -->
				<rect x="22" y="18" width="16" height="18" fill="var(--pixel-shirt)"/>

				<!-- Руки внизу, по бокам -->
				<rect x="14" y="20" width="8" height="4" fill="var(--pixel-shirt)"/>
				<rect x="38" y="20" width="8" height="4" fill="var(--pixel-shirt)"/>
				<rect x="10" y="24" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="44" y="24" width="6" height="16" fill="var(--pixel-skin)"/>

				<!-- Шорты -->
				<rect x="22" y="36" width="16" height="8" fill="var(--pixel-shorts)"/>

				<!-- Ноги -->
				<rect x="22" y="44" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="32" y="44" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="20" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>
				<rect x="30" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="64" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 1}
				<!-- Кадр 2: Руки вперёд/в стороны -->
				<rect x="24" y="4" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="26" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="32" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="2" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="28" y="16" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="18" width="16" height="18" fill="var(--pixel-shirt)"/>

				<!-- Руки в стороны -->
				<rect x="14" y="20" width="8" height="4" fill="var(--pixel-shirt)"/>
				<rect x="38" y="20" width="8" height="4" fill="var(--pixel-shirt)"/>
				<rect x="2" y="20" width="14" height="4" fill="var(--pixel-skin)"/>
				<rect x="44" y="20" width="14" height="4" fill="var(--pixel-skin)"/>

				<rect x="22" y="36" width="16" height="8" fill="var(--pixel-shorts)"/>
				<rect x="22" y="44" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="32" y="44" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="20" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>
				<rect x="30" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="64" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else if frame === 2}
				<!-- Кадр 3: Руки вверху -->
				<rect x="24" y="4" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="26" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="32" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="2" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="28" y="16" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="18" width="16" height="18" fill="var(--pixel-shirt)"/>

				<!-- Руки вверху -->
				<rect x="18" y="18" width="4" height="4" fill="var(--pixel-shirt)"/>
				<rect x="38" y="18" width="4" height="4" fill="var(--pixel-shirt)"/>
				<rect x="16" y="2" width="4" height="18" fill="var(--pixel-skin)"/>
				<rect x="40" y="2" width="4" height="18" fill="var(--pixel-skin)"/>

				<rect x="22" y="36" width="16" height="8" fill="var(--pixel-shorts)"/>
				<rect x="22" y="44" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="32" y="44" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="20" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>
				<rect x="30" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="64" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>

			{:else}
				<!-- Кадр 4: Руки в стороны (обратно) -->
				<rect x="24" y="4" width="12" height="12" fill="var(--pixel-skin)"/>
				<rect x="26" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="32" y="8" width="2" height="2" fill="var(--pixel-dark)"/>
				<rect x="24" y="2" width="12" height="4" fill="var(--pixel-hair)"/>

				<rect x="28" y="16" width="4" height="2" fill="var(--pixel-skin)"/>
				<rect x="22" y="18" width="16" height="18" fill="var(--pixel-shirt)"/>

				<!-- Руки в стороны -->
				<rect x="14" y="20" width="8" height="4" fill="var(--pixel-shirt)"/>
				<rect x="38" y="20" width="8" height="4" fill="var(--pixel-shirt)"/>
				<rect x="2" y="20" width="14" height="4" fill="var(--pixel-skin)"/>
				<rect x="44" y="20" width="14" height="4" fill="var(--pixel-skin)"/>

				<rect x="22" y="36" width="16" height="8" fill="var(--pixel-shorts)"/>
				<rect x="22" y="44" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="32" y="44" width="6" height="16" fill="var(--pixel-skin)"/>
				<rect x="20" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>
				<rect x="30" y="60" width="10" height="4" fill="var(--pixel-shoes)"/>

				<rect x="0" y="64" width="64" height="2" fill="var(--pixel-dark)" opacity="0.3"/>
			{/if}
		</svg>

		<div class="tips">
			<span class="tip">Круговые движения прямыми руками</span>
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
		--pixel-accent: #fcc800;
	}

	.tips {
		text-align: center;
		min-height: 24px;
	}

	.tip {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
		text-transform: uppercase;
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
