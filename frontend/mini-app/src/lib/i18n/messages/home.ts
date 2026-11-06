/**
 * Strings for the home screen, root layout and bottom navigation.
 * Namespace: `home`. Reference as t('home.greeting.morning'), etc.
 *
 * Fitness / 8-bit gamification wording: XP, coins, streak, bosses, challenges.
 */
export default {
	ru: {
		greeting: {
			night: 'Доброй ночи',
			morning: 'Доброе утро',
			day: 'Добрый день',
			evening: 'Добрый вечер',
		},
		header: {
			hello: '{greeting}, {name}!',
			levelBadge: 'Ур.{level}',
		},
		notifications: {
			title: 'Уведомления',
			loading: 'Загрузка...',
			empty: 'Нет уведомлений',
			goToFriends: 'Перейти к друзьям',
		},
		mainAction: {
			title: 'Начать тренировку',
			subtitle: 'Выбери программу или упражнения',
			quickRecord: 'Быстрая запись',
			rewardXp: '+{xp} XP',
			rewardCoins: '+{coins} монет',
		},
		progress: {
			levelLabel: 'Уровень',
			xpToNext: '{current}/{needed} XP до следующего',
		},
		stats: {
			xp: 'XP',
			streak: 'Серия',
			coins: 'Монеты',
		},
		weekly: {
			title: 'Эта неделя',
			workouts: 'тренировок',
			xp: 'XP',
		},
		day: {
			workouts: 'Тренировки',
			xpEarned: 'XP заработано',
			noActivity: 'Нет тренировок в этот день',
		},
		layout: {
			appTitle: 'PixelFit - Pixel Fitness',
			appDescription: '8-bit фитнес трекер с геймификацией',
			unauthorizedTitle: 'Не авторизован',
			unauthorizedText: 'Откройте приложение через Telegram',
		},
		nav: {
			home: 'Главная',
			workout: 'Тренировка',
			challenges: 'Челленджи',
			city: 'Город',
			leaderboard: 'Рейтинг',
			profile: 'Профиль',
		},
		exitDialog: {
			title: 'Тренировка активна',
			text: 'Что сделать с текущей тренировкой?',
			finish: 'Завершить',
			continue: 'Продолжить',
			cancel: 'Отменить',
		},
	},
	en: {
		greeting: {
			night: 'Good night',
			morning: 'Good morning',
			day: 'Good afternoon',
			evening: 'Good evening',
		},
		header: {
			hello: '{greeting}, {name}!',
			levelBadge: 'Lv.{level}',
		},
		notifications: {
			title: 'Notifications',
			loading: 'Loading...',
			empty: 'No notifications',
			goToFriends: 'Go to friends',
		},
		mainAction: {
			title: 'Start workout',
			subtitle: 'Pick a program or exercises',
			quickRecord: 'Quick log',
			rewardXp: '+{xp} XP',
			rewardCoins: '+{coins} coins',
		},
		progress: {
			levelLabel: 'Level',
			xpToNext: '{current}/{needed} XP to next level',
		},
		stats: {
			xp: 'XP',
			streak: 'Streak',
			coins: 'Coins',
		},
		weekly: {
			title: 'This week',
			workouts: 'workouts',
			xp: 'XP',
		},
		day: {
			workouts: 'Workouts',
			xpEarned: 'XP earned',
			noActivity: 'No workouts on this day',
		},
		layout: {
			appTitle: 'PixelFit - Pixel Fitness',
			appDescription: '8-bit fitness tracker with gamification',
			unauthorizedTitle: 'Not authorized',
			unauthorizedText: 'Open the app through Telegram',
		},
		nav: {
			home: 'Home',
			workout: 'Workout',
			challenges: 'Challenges',
			city: 'City',
			leaderboard: 'Leaderboard',
			profile: 'Profile',
		},
		exitDialog: {
			title: 'Workout in progress',
			text: 'What do you want to do with the current workout?',
			finish: 'Finish',
			continue: 'Continue',
			cancel: 'Cancel',
		},
	},
};
