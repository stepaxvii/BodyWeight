/**
 * Strings for the settings screen. Namespace: `settings`.
 * Reference as t('settings.title'), t('settings.game.sound.title'), ...
 */
export default {
	ru: {
		title: 'Настройки',
		back: 'Назад',

		game: {
			heading: 'Игра',
			sound: {
				title: 'Звук',
				hint: '8-битные сигналы на тренировке',
			},
			leaderboard: {
				title: 'Виден друзьям',
				hint: 'Показывать тебя в недельном рейтинге друзей',
			},
			norm: {
				title: 'Дневная норма',
				hint: 'Цель XP в день — по ней раскрашивается календарь активности (4 уровня заливки).',
				unit: 'XP',
				invalid: 'Норма должна быть от 100 до 100000 XP',
				saved: '✅ Норма обновлена',
				saveError: 'Не удалось сохранить',
			},
		},

		notifications: {
			heading: 'Уведомления',
			push: {
				title: 'Напоминания в Telegram',
				hint: 'Пуш о тренировке и при простое 3+ дня',
			},
			time: {
				title: 'Время напоминания',
				hint: 'Придёт в выбранный час, если не тренировался в этот день',
				saved: '✅ Время сохранено',
				saveError: 'Не удалось сохранить',
			},
		},

		timezone: {
			heading: 'Часовой пояс',
			title: 'Твой часовой пояс',
			hint: 'По нему считаются дни квестов, стрики и время напоминаний',
			saved: '✅ Часовой пояс сохранён',
			saveError: 'Не удалось сохранить'
		},

		language: {
			heading: 'Язык',
			title: 'Язык интерфейса',
			hint: 'Выбери язык приложения',
			ru: 'Русский',
			en: 'English',
		},

		account: {
			heading: 'Аккаунт',
			telegram: 'Telegram',
			telegramId: 'ID: {id}',
		},

		toggle: {
			on: 'Вкл',
			off: 'Выкл',
		},

		common: {
			save: 'Сохранить',
			saving: '...',
		},
	},
	en: {
		title: 'Settings',
		back: 'Back',

		game: {
			heading: 'Game',
			sound: {
				title: 'Sound',
				hint: '8-bit cues during your workout',
			},
			leaderboard: {
				title: 'Visible to friends',
				hint: 'Show you on the weekly friends leaderboard',
			},
			norm: {
				title: 'Daily goal',
				hint: 'Daily XP goal — it colors the activity calendar (4 fill levels).',
				unit: 'XP',
				invalid: 'Goal must be between 100 and 100000 XP',
				saved: '✅ Goal updated',
				saveError: 'Could not save',
			},
		},

		notifications: {
			heading: 'Notifications',
			push: {
				title: 'Telegram reminders',
				hint: 'Workout push and a nudge after 3+ idle days',
			},
			time: {
				title: 'Reminder time',
				hint: "Arrives at the chosen hour if you haven't trained that day",
				saved: '✅ Time saved',
				saveError: 'Could not save',
			},
		},

		timezone: {
			heading: 'Timezone',
			title: 'Your timezone',
			hint: 'Used for quest days, streaks and reminder time',
			saved: '✅ Timezone saved',
			saveError: 'Could not save'
		},

		language: {
			heading: 'Language',
			title: 'Interface language',
			hint: 'Choose the app language',
			ru: 'Русский',
			en: 'English',
		},

		account: {
			heading: 'Account',
			telegram: 'Telegram',
			telegramId: 'ID: {id}',
		},

		toggle: {
			on: 'On',
			off: 'Off',
		},

		common: {
			save: 'Save',
			saving: '...',
		},
	},
};
