/**
 * Lightweight runtime i18n for the mini-app (Svelte 5, no deps).
 *
 * - `locale` is reactive $state; calling `t()` in markup re-renders on change,
 *   so the profile language switcher updates the whole UI live.
 * - Message catalogs live in ./messages/<namespace>.ts, each a default export
 *   `{ ru: {...}, en: {...} }`. They are auto-aggregated via import.meta.glob,
 *   so adding a namespace needs no edit here (parallel-extraction friendly).
 * - `t('namespace.key', { name })` resolves in the current locale, falls back to
 *   English, then to the raw key. `{placeholders}` are interpolated from params.
 */
export type Lang = 'ru' | 'en';

const modules = import.meta.glob<{ default: { ru?: Record<string, unknown>; en?: Record<string, unknown> } }>(
	'./messages/*.ts',
	{ eager: true },
);

const CATALOG: Record<Lang, Record<string, unknown>> = { ru: {}, en: {} };
for (const [path, mod] of Object.entries(modules)) {
	const ns = path.split('/').pop()!.replace(/\.ts$/, '');
	const m = mod.default ?? {};
	CATALOG.ru[ns] = m.ru ?? {};
	CATALOG.en[ns] = m.en ?? {};
}

/** Map any value / Telegram language_code to a supported language (en fallback). */
export function normalizeLang(value: string | null | undefined): Lang {
	return value && value.toLowerCase().startsWith('ru') ? 'ru' : 'en';
}

let locale = $state<Lang>('en');

export function getLocale(): Lang {
	return locale;
}

export function setLocale(value: string | null | undefined): void {
	locale = normalizeLang(value);
}

function lookup(catalog: Record<string, unknown>, key: string): string | null {
	let node: unknown = catalog;
	for (const part of key.split('.')) {
		if (node == null || typeof node !== 'object' || !(part in (node as Record<string, unknown>))) {
			return null;
		}
		node = (node as Record<string, unknown>)[part];
	}
	return typeof node === 'string' ? node : null;
}

export function t(key: string, params?: Record<string, string | number>): string {
	// Reading `locale` here is what makes t() reactive to the switcher.
	const active = locale;
	let msg = lookup(CATALOG[active], key);
	if (msg == null && active !== 'en') msg = lookup(CATALOG.en, key);
	if (msg == null) return key;
	// Narrow to a definitely-string local so the params loop can't re-widen it
	// back to `string | null` (which would break the `string` return contract).
	let out = msg;
	if (params) {
		for (const [k, v] of Object.entries(params)) {
			out = out.split(`{${k}}`).join(String(v));
		}
	}
	return out;
}

/**
 * Pick a bilingual DB value by the current locale (English fallback).
 *
 * Content names/descriptions come from the API in both languages (e.g.
 * `name`/`name_ru`). Pass both raw fields: `ln(ex.name, ex.name_ru)`.
 * Reads `locale`, so call sites re-render on a language switch, like t().
 */
export function ln(en: string | null | undefined, ru: string | null | undefined): string {
	const active = locale;
	const chosen = active === 'ru' ? (ru ?? en) : (en ?? ru);
	return chosen ?? '';
}
