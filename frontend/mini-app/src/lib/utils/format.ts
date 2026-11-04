/**
 * Formatting utilities
 */
import { t } from '$lib/i18n/index.svelte';

/**
 * Format duration in seconds to MM:SS
 */
export function formatDuration(seconds: number): string {
	const minutes = Math.floor(seconds / 60);
	const secs = seconds % 60;
	return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format duration in seconds to human readable (e.g., "1h 30m")
 */
export function formatDurationLong(seconds: number): string {
	const hours = Math.floor(seconds / 3600);
	const minutes = Math.floor((seconds % 3600) / 60);

	if (hours > 0) {
		return `${hours}h ${minutes}m`;
	}
	return `${minutes}m`;
}

/**
 * Format date to locale string
 */
export function formatDate(date: string | Date, locale: string = 'ru-RU'): string {
	const d = typeof date === 'string' ? new Date(date) : date;
	return d.toLocaleDateString(locale, {
		day: 'numeric',
		month: 'short',
		year: 'numeric'
	});
}

/**
 * Format relative time (e.g., "2 days ago")
 */
export function formatRelativeTime(date: string | Date, locale: string = 'ru-RU'): string {
	const d = typeof date === 'string' ? new Date(date) : date;
	const now = new Date();
	const diffMs = now.getTime() - d.getTime();
	const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

	if (diffDays === 0) {
		return t('misc.relativeTime.today');
	} else if (diffDays === 1) {
		return t('misc.relativeTime.yesterday');
	} else if (diffDays < 7) {
		return t('misc.relativeTime.daysAgo', { count: diffDays });
	} else {
		return formatDate(d, locale);
	}
}

/**
 * Format number with thousands separator
 */
export function formatNumber(num: number, locale: string = 'ru-RU'): string {
	return num.toLocaleString(locale);
}

/**
 * Pluralize using three forms: [one, few, many].
 * The selector follows Russian grammar (one / few 2–4 / many);
 * English catalogs supply the same string for `few` and `many`, so the
 * singular/plural split still comes out correct.
 */
export function pluralize(count: number, forms: [string, string, string]): string {
	const n = Math.abs(count) % 100;
	const n1 = n % 10;

	if (n > 10 && n < 20) {
		return forms[2]; // много (genitive plural)
	}
	if (n1 > 1 && n1 < 5) {
		return forms[1]; // несколько (genitive singular)
	}
	if (n1 === 1) {
		return forms[0]; // один (nominative singular)
	}
	return forms[2]; // много (genitive plural)
}

/** Resolve the localized [one, few, many] forms for a plural word. */
function forms(word: string): [string, string, string] {
	return [
		t(`misc.plurals.${word}.one`),
		t(`misc.plurals.${word}.few`),
		t(`misc.plurals.${word}.many`)
	];
}

/**
 * Get the localized, correctly pluralized form of a common word.
 */
export const plurals = {
	day: (count: number) => pluralize(count, forms('day')),
	workout: (count: number) => pluralize(count, forms('workout')),
	rep: (count: number) => pluralize(count, forms('rep')),
	coin: (count: number) => pluralize(count, forms('coin')),
	friend: (count: number) => pluralize(count, forms('friend'))
};
