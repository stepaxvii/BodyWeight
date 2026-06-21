<script lang="ts">
	// Animated number that counts up to `value` on change.
	// Honours prefers-reduced-motion (shows the final value instantly).
	interface Props {
		value: number;
		duration?: number; // ms
		class?: string;
	}

	let { value, duration = 600, class: className = '' }: Props = $props();

	let display = $state(0);
	let prev = 0; // last settled value (non-reactive, avoids effect self-trigger)
	let raf = 0;

	const prefersReduced =
		typeof window !== 'undefined' &&
		typeof window.matchMedia === 'function' &&
		window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	$effect(() => {
		const target = Math.round(value ?? 0); // tracked dependency

		if (prefersReduced) {
			display = target;
			prev = target;
			return;
		}

		const from = prev;
		if (from === target) {
			display = target;
			return;
		}

		const start = performance.now();
		cancelAnimationFrame(raf);
		const tick = (now: number) => {
			const t = Math.min(1, (now - start) / duration);
			const eased = 1 - Math.pow(1 - t, 3); // ease-out cubic
			display = Math.round(from + (target - from) * eased);
			if (t < 1) {
				raf = requestAnimationFrame(tick);
			} else {
				prev = target;
			}
		};
		raf = requestAnimationFrame(tick);

		return () => cancelAnimationFrame(raf);
	});
</script>

<span class={className}>{display.toLocaleString('ru-RU')}</span>
