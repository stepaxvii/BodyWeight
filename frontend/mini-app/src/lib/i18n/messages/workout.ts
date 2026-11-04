/**
 * Strings for the Workout screen. Namespace: `workout`.
 * Reference as t('workout.active.title'), t('workout.builder.exercisesCount', { count }), ...
 *
 * `ru` and `en` share an identical key tree; English is the fallback.
 * Placeholders use the {name} syntax and must match across both languages.
 */
export default {
	ru: {
		loading: 'Загрузка...',

		active: {
			title: 'Тренировка',
			stats: {
				sets: 'Подходов',
				reps: 'Повторов',
				xp: 'XP',
			},
			favorite: {
				add: 'Добавить в избранное',
				remove: 'Убрать из избранного',
			},
			exerciseInfo: 'Описание упражнения',
			addSet: 'Подход',
			prevReps: '{reps} повт.',
			prevSets: '{sets} подх.',
			prevXp: '+{xp} XP',
			noExercises: 'У вас есть активная тренировка без упражнений. Завершите или отмените её.',
			finish: 'Завершить тренировку',
			addSetHint: 'Добавьте хотя бы один подход',
			cancel: 'Отменить тренировку',
		},

		cancelConfirm: {
			title: 'Отменить тренировку?',
			text: 'Весь прогресс тренировки будет потерян.',
			confirm: 'Да, отменить',
			keep: 'Продолжить тренировку',
		},

		banner: {
			title: 'Тренировка',
			exercisesCount: '{count} упражнений',
			createSet: 'Создать сет',
		},

		share: {
			title: 'Похвастаться?',
			completed: 'Тренировка завершена:',
			xp: '+{xp} XP',
			toChat: 'Отправить в чат',
			toStory: 'В сторис',
		},

		program: {
			badge: '★ Программа дня',
			reward: '+{xp} XP',
			durationMin: '~{minutes}м',
			exercisesShort: '{count} упр.',
			start: 'Начать тренировку',
		},

		tabs: {
			myRoutines: 'Мои',
			routines: 'Сеты',
			favorites: 'Избранное',
			exercises: 'Упражнения',
		},

		routineCategories: {
			morning: 'Зарядка',
			home: 'Дома',
			pullupBar: 'Турник',
			dipBars: 'Брусья',
			dumbbell: 'Гантели',
			resistanceBand: 'Эспандер',
		},

		routines: {
			durationMin: '~{minutes}м',
			emptyCategory: 'Нет сетов в этой категории',
			loading: 'Сеты загружаются...',
		},

		favorites: {
			empty: 'Нет избранных упражнений',
			emptyHint: 'Нажми на сердечко, чтобы добавить',
		},

		exercises: {
			count: '{shown} / {total} упражнений',
			reset: 'Сбросить',
			filter: 'Фильтр',
			searchPlaceholder: 'Поиск упражнений...',
			notFound: 'Ничего не найдено',
			resetFilters: 'Сбросить фильтры',
			loading: 'Загрузка...',
			loadMore: 'Загрузить ещё',
		},

		selection: {
			selected: 'Выбрано: {count}',
			clear: 'Очистить',
			start: 'Начать тренировку',
		},

		deleteConfirm: {
			title: 'Удалить сет?',
			text: 'Вы уверены, что хотите удалить сет "{name}"?',
			cancel: 'Отмена',
			delete: 'Удалить',
		},

		exerciseInfo: {
			noDescription: 'Описание отсутствует',
			close: 'Закрыть',
		},
	},

	en: {
		loading: 'Loading...',

		active: {
			title: 'Workout',
			stats: {
				sets: 'Sets',
				reps: 'Reps',
				xp: 'XP',
			},
			favorite: {
				add: 'Add to favorites',
				remove: 'Remove from favorites',
			},
			exerciseInfo: 'Exercise details',
			addSet: 'Set',
			prevReps: '{reps} reps',
			prevSets: '{sets} sets',
			prevXp: '+{xp} XP',
			noExercises: 'You have an active workout with no exercises. Finish it or cancel it.',
			finish: 'Finish workout',
			addSetHint: 'Add at least one set',
			cancel: 'Cancel workout',
		},

		cancelConfirm: {
			title: 'Cancel workout?',
			text: 'All workout progress will be lost.',
			confirm: 'Yes, cancel',
			keep: 'Keep training',
		},

		banner: {
			title: 'Workout',
			exercisesCount: '{count} exercises',
			createSet: 'Create a set',
		},

		share: {
			title: 'Show it off?',
			completed: 'Workout complete:',
			xp: '+{xp} XP',
			toChat: 'Send to chat',
			toStory: 'To story',
		},

		program: {
			badge: '★ Workout of the Day',
			reward: '+{xp} XP',
			durationMin: '~{minutes}m',
			exercisesShort: '{count} exercises',
			start: 'Start workout',
		},

		tabs: {
			myRoutines: 'Mine',
			routines: 'Sets',
			favorites: 'Favorites',
			exercises: 'Exercises',
		},

		routineCategories: {
			morning: 'Warm-up',
			home: 'At home',
			pullupBar: 'Pull-up bar',
			dipBars: 'Dip bars',
			dumbbell: 'Dumbbells',
			resistanceBand: 'Resistance band',
		},

		routines: {
			durationMin: '~{minutes}m',
			emptyCategory: 'No sets in this category',
			loading: 'Loading sets...',
		},

		favorites: {
			empty: 'No favorite exercises yet',
			emptyHint: 'Tap the heart to add one',
		},

		exercises: {
			count: '{shown} / {total} exercises',
			reset: 'Reset',
			filter: 'Filter',
			searchPlaceholder: 'Search exercises...',
			notFound: 'Nothing found',
			resetFilters: 'Reset filters',
			loading: 'Loading...',
			loadMore: 'Load more',
		},

		selection: {
			selected: 'Selected: {count}',
			clear: 'Clear',
			start: 'Start workout',
		},

		deleteConfirm: {
			title: 'Delete set?',
			text: 'Are you sure you want to delete the set "{name}"?',
			cancel: 'Cancel',
			delete: 'Delete',
		},

		exerciseInfo: {
			noDescription: 'No description available',
			close: 'Close',
		},
	},
};
