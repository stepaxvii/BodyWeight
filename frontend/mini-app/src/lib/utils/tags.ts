/**
 * Маппинг английских тегов упражнений на русские названия
 */

export const TAG_TRANSLATIONS: Record<string, string> = {
	// Группы мышц
	'chest': 'грудь',
	'triceps': 'трицепс',
	'biceps': 'бицепс',
	'shoulders': 'плечи',
	'back': 'спина',
	'lats': 'широчайшие',
	'core': 'кор',
	'abs': 'пресс',
	'obliques': 'косые',
	'legs': 'ноги',
	'quads': 'квадрицепс',
	'hamstrings': 'бицепс бедра',
	'glutes': 'ягодицы',
	'calves': 'икры',
	'hip-flexors': 'сгибатели бедра',
	'lower-back': 'поясница',
	'upper-back': 'верх спины',
	'forearms': 'предплечья',
	'traps': 'трапеции',
	'neck': 'шея',
	'full-body': 'всё тело',

	// Уровень сложности
	'beginner': 'новичок',
	'intermediate': 'средний',
	'advanced': 'продвинутый',
	'expert': 'эксперт',

	// Место/оборудование
	'home': 'дома',
	'outdoor': 'на улице',
	'gym': 'зал',
	'pullup-bar': 'турник',
	'dip-bars': 'брусья',
	'bench': 'скамья',
	'wall': 'стена',
	'floor': 'пол',
	'no-equipment': 'без инвентаря',

	// Тип упражнения
	'push': 'жим',
	'pull': 'тяга',
	'hold': 'удержание',
	'static': 'статика',
	'dynamic': 'динамика',
	'explosive': 'взрывное',
	'plyometric': 'плиометрика',
	'balance': 'баланс',
	'flexibility': 'гибкость',
	'mobility': 'мобильность',
	'stretch': 'растяжка',
	'warmup': 'разминка',
	'cooldown': 'заминка',

	// Кардио
	'cardio': 'кардио',
	'hiit': 'ВИИТ',
	'endurance': 'выносливость',

	// Части тела для растяжки
	'spine': 'позвоночник',
	'hips': 'бёдра',
	'groin': 'пах',
	'ankles': 'голеностоп',
	'wrists': 'запястья',
	'chest-stretch': 'грудь',
	'back-stretch': 'спина',
	'leg-stretch': 'ноги',
	'arm-stretch': 'руки',
};

/**
 * Получить русское название тега
 */
export function getTagName(tag: string): string {
	return TAG_TRANSLATIONS[tag] || tag;
}

/**
 * Получить русские названия для массива тегов
 */
export function getTagNames(tags: string[]): string[] {
	return tags.map(getTagName);
}
