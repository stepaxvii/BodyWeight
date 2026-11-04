/**
 * Game data strings: localized names/descriptions of badges and avatars that
 * live in the static data arrays (src/lib/data/badges.ts, avatars.ts).
 * Namespace: `gamedata`.
 *
 * Keyed by entity id (slug). Reference as
 * t('gamedata.first-blood.name'), t('gamedata.shadow-wolf.name'), ...
 */
export default {
	ru: {
		// === Badges ===
		'first-blood': { name: 'Первая кровь', description: 'Завершите первую тренировку' },
		'early-bird': { name: 'Ранняя пташка', description: 'Завершите тренировку до 7 утра' },
		'night-owl': { name: 'Ночная сова', description: 'Завершите тренировку после 10 вечера' },
		'week-warrior': { name: 'Недельный воин', description: 'Сохраняйте серию тренировок 7 дней' },
		'iron-will': { name: 'Железная воля', description: 'Выполните 1000 повторений всего' },
		'perfectionist': {
			name: 'Перфекционист',
			description: 'Выполните 10 тренировок подряд без пропусков',
		},
		'centurion': { name: 'Центурион', description: 'Завершите 100 тренировок всего' },
		'month-master': { name: 'Мастер месяца', description: 'Сохраняйте серию тренировок 30 дней' },
		'legend': { name: 'Легенда', description: 'Достигните 25 уровня' },
		'unstoppable': { name: 'Неудержимый', description: 'Сохраняйте серию тренировок 100 дней' },

		// === Avatars ===
		'shadow-wolf': { name: 'Теневой Волк' },
		'iron-bear': { name: 'Железный Медведь' },
		'fire-fox': { name: 'Огненный Лис' },
		'night-panther': { name: 'Ночная Пантера' },
		'phoenix': { name: 'Феникс' },
		'griffin': { name: 'Грифон' },
		'cerberus': { name: 'Цербер' },
		'thunder-fang': { name: 'Громовой Клык' },
		'cyber-ape': { name: 'Кибер-Примат' },
		'hydra': { name: 'Гидра' },
		'minotaur': { name: 'Минотавр' },
		'kraken': { name: 'Кракен' },
		'leviathan': { name: 'Левиафан' },
		'titan': { name: 'Титан' },
		'solar-lion': { name: 'Солнечный Лев' },
		'crystal-stag': { name: 'Хрустальный Олень' },
		'storm-eagle': { name: 'Штормовой Орёл' },
		'void-serpent': { name: 'Бездонный Змей' },
		'magma-golem': { name: 'Магма-Голем' },
	},
	en: {
		// === Badges ===
		'first-blood': { name: 'First Blood', description: 'Complete your first workout' },
		'early-bird': { name: 'Early Bird', description: 'Complete a workout before 7 AM' },
		'night-owl': { name: 'Night Owl', description: 'Complete a workout after 10 PM' },
		'week-warrior': { name: 'Week Warrior', description: 'Maintain a 7-day workout streak' },
		'iron-will': { name: 'Iron Will', description: 'Complete 1000 total reps' },
		'perfectionist': {
			name: 'Perfectionist',
			description: 'Complete 10 workouts in a row without skipping a day',
		},
		'centurion': { name: 'Centurion', description: 'Complete 100 workouts total' },
		'month-master': { name: 'Month Master', description: 'Maintain a 30-day workout streak' },
		'legend': { name: 'Legend', description: 'Reach level 25' },
		'unstoppable': { name: 'Unstoppable', description: 'Maintain a 100-day workout streak' },

		// === Avatars ===
		'shadow-wolf': { name: 'Shadow Wolf' },
		'iron-bear': { name: 'Iron Bear' },
		'fire-fox': { name: 'Fire Fox' },
		'night-panther': { name: 'Night Panther' },
		'phoenix': { name: 'Phoenix' },
		'griffin': { name: 'Griffin' },
		'cerberus': { name: 'Cerberus' },
		'thunder-fang': { name: 'Thunder Fang' },
		'cyber-ape': { name: 'Cyber Ape' },
		'hydra': { name: 'Hydra' },
		'minotaur': { name: 'Minotaur' },
		'kraken': { name: 'Kraken' },
		'leviathan': { name: 'Leviathan' },
		'titan': { name: 'Titan' },
		'solar-lion': { name: 'Solar Lion' },
		'crystal-stag': { name: 'Crystal Stag' },
		'storm-eagle': { name: 'Storm Eagle' },
		'void-serpent': { name: 'Void Serpent' },
		'magma-golem': { name: 'Magma Golem' },
	},
};
