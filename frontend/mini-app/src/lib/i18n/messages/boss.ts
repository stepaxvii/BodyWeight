/**
 * Strings for the Boss area. Namespace: `boss`.
 * Reference as t('boss.title'), t('boss.claim.toastSuccess', { coins }), ...
 */
export default {
	ru: {
		title: 'Босс месяца',
		loading: 'Загрузка...',
		tabs: {
			current: 'Текущий',
			history: 'История',
		},
		status: {
			defeated: 'Повержен',
			expired: 'Не побеждён',
			active: 'В битве',
		},
		hp: 'HP',
		contribution: {
			title: 'Твой вклад',
			damage: 'урон',
			rank: 'место',
			attacks: 'ударов',
			empty: 'Ты ещё не нанёс ни одного удара. Сделай тренировку — XP станет уроном по боссу.',
		},
		claim: {
			coinsWaiting: 'монет ждут тебя',
			top10: 'Топ-10',
			button: 'Забрать',
			claimed: 'Награда уже получена ({coins} монет)',
			toastSuccess: 'Получено: +{coins} монет!',
			toastError: 'Не удалось забрать награду',
		},
		leaderboard: {
			title: 'Топ-10 по урону',
			defaultPlayer: 'Игрок',
			you: 'Ты',
			emptyTitle: 'Никто ещё не атаковал',
			emptyMessage: 'Стань первым, кто ударит босса',
		},
		history: {
			damage: 'урон',
			rank: 'место',
			rewardUnit: 'м',
			notParticipated: 'Не участвовал',
			emptyTitle: 'История пуста',
			emptyMessage: 'Здесь будут появляться прошлые боссы',
		},
	},
	en: {
		title: 'Boss of the Month',
		loading: 'Loading...',
		tabs: {
			current: 'Current',
			history: 'History',
		},
		status: {
			defeated: 'Defeated',
			expired: 'Not defeated',
			active: 'In Battle',
		},
		hp: 'HP',
		contribution: {
			title: 'Your Contribution',
			damage: 'damage',
			rank: 'rank',
			attacks: 'hits',
			empty: "You haven't landed a single hit yet. Finish a workout — your XP turns into damage against the boss.",
		},
		claim: {
			coinsWaiting: 'coins are waiting for you',
			top10: 'Top 10',
			button: 'Claim',
			claimed: 'Reward already claimed ({coins} coins)',
			toastSuccess: 'Received: +{coins} coins!',
			toastError: "Couldn't claim the reward",
		},
		leaderboard: {
			title: 'Top 10 by Damage',
			defaultPlayer: 'Player',
			you: 'You',
			emptyTitle: 'No one has attacked yet',
			emptyMessage: 'Be the first to strike the boss',
		},
		history: {
			damage: 'damage',
			rank: 'rank',
			rewardUnit: 'coins',
			notParticipated: "Didn't participate",
			emptyTitle: 'No history yet',
			emptyMessage: 'Past bosses will show up here',
		},
	},
};
