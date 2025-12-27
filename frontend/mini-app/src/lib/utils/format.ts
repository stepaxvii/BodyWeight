/**
 * Formatting utilities
 */

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
		return 'Сегодня';
	} else if (diffDays === 1) {
		return 'Вчера';
	} else if (diffDays < 7) {
		return `${diffDays} дн. назад`;
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
 * Pluralize Russian words
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

/**
 * Get Russian pluralized text for common words
 */
export const plurals = {
	day: (count: number) => pluralize(count, ['день', 'дня', 'дней']),
	workout: (count: number) => pluralize(count, ['тренировка', 'тренировки', 'тренировок']),
	rep: (count: number) => pluralize(count, ['повторение', 'повторения', 'повторений']),
	coin: (count: number) => pluralize(count, ['монета', 'монеты', 'монет']),
	friend: (count: number) => pluralize(count, ['друг', 'друга', 'друзей'])
};
