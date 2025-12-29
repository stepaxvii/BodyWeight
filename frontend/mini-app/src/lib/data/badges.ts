import type { Badge, BadgeId } from '$lib/types';

export const BADGES: Badge[] = [
	// === COMMON (Обычные) ===
	{
		id: 'first-blood',
		name: 'First Blood',
		name_ru: 'Первая кровь',
		description: 'Complete your first workout',
		description_ru: 'Завершите первую тренировку',
		rarity: 'common'
	},
	{
		id: 'early-bird',
		name: 'Early Bird',
		name_ru: 'Ранняя пташка',
		description: 'Complete a workout before 7 AM',
		description_ru: 'Завершите тренировку до 7 утра',
		rarity: 'common'
	},
	{
		id: 'night-owl',
		name: 'Night Owl',
		name_ru: 'Ночная сова',
		description: 'Complete a workout after 10 PM',
		description_ru: 'Завершите тренировку после 10 вечера',
		rarity: 'common'
	},

	// === RARE (Редкие) ===
	{
		id: 'week-warrior',
		name: 'Week Warrior',
		name_ru: 'Недельный воин',
		description: 'Maintain a 7-day workout streak',
		description_ru: 'Сохраняйте серию тренировок 7 дней',
		rarity: 'rare'
	},
	{
		id: 'iron-will',
		name: 'Iron Will',
		name_ru: 'Железная воля',
		description: 'Complete 1000 total reps',
		description_ru: 'Выполните 1000 повторений всего',
		rarity: 'rare'
	},
	{
		id: 'perfectionist',
		name: 'Perfectionist',
		name_ru: 'Перфекционист',
		description: 'Complete 10 workouts in a row without skipping a day',
		description_ru: 'Выполните 10 тренировок подряд без пропусков',
		rarity: 'rare'
	},

	// === EPIC (Эпические) ===
	{
		id: 'centurion',
		name: 'Centurion',
		name_ru: 'Центурион',
		description: 'Complete 100 workouts total',
		description_ru: 'Завершите 100 тренировок всего',
		rarity: 'epic'
	},
	{
		id: 'month-master',
		name: 'Month Master',
		name_ru: 'Мастер месяца',
		description: 'Maintain a 30-day workout streak',
		description_ru: 'Сохраняйте серию тренировок 30 дней',
		rarity: 'epic'
	},

	// === LEGENDARY (Легендарные) ===
	{
		id: 'legend',
		name: 'Legend',
		name_ru: 'Легенда',
		description: 'Reach level 25',
		description_ru: 'Достигните 25 уровня',
		rarity: 'legendary'
	},
	{
		id: 'unstoppable',
		name: 'Unstoppable',
		name_ru: 'Неудержимый',
		description: 'Maintain a 100-day workout streak',
		description_ru: 'Сохраняйте серию тренировок 100 дней',
		rarity: 'legendary'
	}
];

export function getBadge(id: BadgeId): Badge | undefined {
	return BADGES.find((b) => b.id === id);
}

export function getBadgesByRarity(rarity: Badge['rarity']): Badge[] {
	return BADGES.filter((b) => b.rarity === rarity);
}

export function getRarityColor(rarity: Badge['rarity']): string {
	switch (rarity) {
		case 'common':
			return '#9CA3AF'; // gray
		case 'rare':
			return '#3B82F6'; // blue
		case 'epic':
			return '#8B5CF6'; // purple
		case 'legendary':
			return '#F59E0B'; // gold
	}
}
