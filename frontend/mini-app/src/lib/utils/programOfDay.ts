import type { Exercise, Routine, RoutineExercise } from '$lib/types';

/**
 * "Программа дня" (Program of the Day) — a date-seeded random workout built
 * from the live exercise catalogue.
 *
 * Product rules (do not weaken without asking):
 *  - NO additional equipment           → equipment === 'none'
 *  - medium difficulty                  → difficulty 2..3 (доступно и новичку, и опытному)
 *  - spans DIFFERENT directions         → one exercise per category, diversity-first
 *  - DETERMINISTIC per calendar day     → same date ⇒ identical program for everyone,
 *                                          changes when the local day rolls over.
 *
 * The result is a plain `Routine`, so it runs in the existing RoutinePlayer and
 * reuses the whole completion/submission flow unchanged.
 */

const MEDIUM_MIN = 2; // difficulty is 1..5; 2..3 is the "medium" band
const MEDIUM_MAX = 3;
const TARGET_COUNT = 6; // ~6 exercises across different directions (matches the design)
const DEFAULT_REPS = 12; // default goal for rep-based exercises
const DEFAULT_DURATION = 30; // default goal (seconds) for timed holds

/**
 * mulberry32 — a tiny, fast, fully deterministic PRNG. Same seed yields the same
 * sequence on every device (no `Math.random`, no `Date`/locale drift).
 */
function mulberry32(seed: number): () => number {
	let a = seed >>> 0;
	return () => {
		a = (a + 0x6d2b79f5) | 0;
		let t = Math.imul(a ^ (a >>> 15), 1 | a);
		t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
		return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
	};
}

/** Stable per-day seed from the LOCAL calendar date, encoded as YYYYMMDD. */
export function dateSeed(d: Date): number {
	return d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
}

/** Byte-stable slug comparison (locale-independent ⇒ deterministic ordering). */
function bySlug(a: { slug: string }, b: { slug: string }): number {
	return a.slug < b.slug ? -1 : a.slug > b.slug ? 1 : 0;
}

/** Fisher–Yates shuffle driven by the seeded PRNG (pure, returns a new array). */
function seededShuffle<T>(arr: T[], rng: () => number): T[] {
	const a = arr.slice();
	for (let i = a.length - 1; i > 0; i--) {
		const j = Math.floor(rng() * (i + 1));
		[a[i], a[j]] = [a[j], a[i]];
	}
	return a;
}

/** No-equipment + medium difficulty + a runnable catalogue exercise. */
export function isEligibleForProgram(e: Exercise): boolean {
	return (
		e.equipment === 'none' &&
		e.difficulty >= MEDIUM_MIN &&
		e.difficulty <= MEDIUM_MAX &&
		e.slug !== 'cycling' // cycling is an activity, not a routine exercise
	);
}

/**
 * Build the deterministic Program of the Day for `date` from the catalogue.
 * Returns `null` if no eligible exercises exist yet.
 */
export function buildProgramOfDay(exercises: Exercise[], date: Date = new Date()): Routine | null {
	// Stable input order first, so pagination/API order can't affect the result.
	const pool = exercises.filter(isEligibleForProgram).sort(bySlug);
	if (pool.length === 0) return null;

	const rng = mulberry32(dateSeed(date));

	// Group by category in a stable order.
	const byCat = new Map<string, Exercise[]>();
	for (const e of pool) {
		const list = byCat.get(e.category_slug);
		if (list) list.push(e);
		else byCat.set(e.category_slug, [e]);
	}

	// Diversity-first: shuffle the categories, take one exercise from each.
	const cats = seededShuffle(Array.from(byCat.keys()).sort(), rng);
	const picked: Exercise[] = [];
	const used = new Set<string>();
	for (const cat of cats) {
		if (picked.length >= TARGET_COUNT) break;
		const list = byCat.get(cat)!;
		const choice = list[Math.floor(rng() * list.length)];
		if (choice && !used.has(choice.slug)) {
			picked.push(choice);
			used.add(choice.slug);
		}
	}

	// Fewer distinct categories than the target → top up from the remaining pool.
	if (picked.length < TARGET_COUNT) {
		for (const e of seededShuffle(
			pool.filter((x) => !used.has(x.slug)),
			rng
		)) {
			if (picked.length >= TARGET_COUNT) break;
			picked.push(e);
			used.add(e.slug);
		}
	}

	const routineExercises: RoutineExercise[] = picked.map((e) =>
		e.is_timed ? { slug: e.slug, duration: DEFAULT_DURATION } : { slug: e.slug, reps: DEFAULT_REPS }
	);

	return {
		slug: `program-of-day-${dateSeed(date)}`,
		name: 'Программа дня',
		description: 'Подобрана на сегодня — разные группы мышц, без инвентаря.',
		category: 'home',
		duration_minutes: Math.max(5, picked.length * 3),
		difficulty: 2,
		exercises: routineExercises
	};
}
