/**
 * Strings for the Friends screen. Namespace: `friends`.
 * Reference as t('friends.title'), t('friends.tabs.search'), ...
 *
 * Default export with matching `ru` and `en` key trees. English is the
 * fallback, so no key may exist in `ru` without an `en` counterpart.
 * Placeholders like {count}, {name}, {coins} are preserved in both languages.
 */
export default {
	ru: {
		title: 'Друзья',
		band: {
			friends: 'Друзей',
			requests: 'Заявки',
		},
		tabs: {
			friends: 'Друзья ({count})',
			requests: 'Заявки',
			search: 'Поиск',
		},
		errors: {
			loadFriends: 'Не удалось загрузить друзей',
			search: 'Ошибка поиска',
			sendRequest: 'Не удалось отправить заявку',
			acceptRequest: 'Не удалось принять заявку',
			remove: 'Не удалось удалить',
		},
		toasts: {
			requestSent: 'Заявка отправлена',
			linkCopied: 'Ссылка скопирована в буфер обмена',
		},
		invite: {
			text: 'Тренируйся со мной в PixelFit — фитнес с 8-битной душой прямо в Telegram',
			title: 'Пригласить друга',
			reward: '+{coins} монет за первую тренировку друга',
			progress: 'Награждено приглашений: {rewarded}/{cap}',
			share: 'Поделиться приглашением',
		},
		search: {
			placeholder: 'Введите username...',
			searching: 'Поиск...',
			minChars: 'Минимум 2 символа для поиска',
			found: 'Найдено: {count}',
			prompt: 'Введите минимум 2 символа для поиска',
			notFound: 'Пользователи не найдены',
		},
		user: {
			level: 'Ур.{level}',
			statusFriend: 'Друг',
			statusPending: 'Отправлено',
			add: 'Добавить',
		},
		loading: 'Загрузка...',
		empty: {
			friendsMessage: 'У вас пока нет друзей',
			friendsHint: 'Найдите друзей по username',
			friendsButton: 'Найти друзей',
			requestsMessage: 'Нет входящих заявок',
		},
		requests: {
			accept: 'Принять',
		},
		fallbackName: {
			friend: 'друга',
			user: 'пользователя',
		},
		confirm: {
			titleReject: 'Отклонить заявку?',
			titleRemove: 'Удалить из друзей?',
			textReject: 'Вы уверены, что хотите отклонить заявку от {name}?',
			textRemove: 'Вы уверены, что хотите удалить {name} из друзей?',
			cancel: 'Отмена',
			reject: 'Отклонить',
			remove: 'Удалить',
		},
	},
	en: {
		title: 'Friends',
		band: {
			friends: 'Friends',
			requests: 'Requests',
		},
		tabs: {
			friends: 'Friends ({count})',
			requests: 'Requests',
			search: 'Search',
		},
		errors: {
			loadFriends: 'Failed to load friends',
			search: 'Search error',
			sendRequest: 'Failed to send request',
			acceptRequest: 'Failed to accept request',
			remove: 'Failed to remove',
		},
		toasts: {
			requestSent: 'Request sent',
			linkCopied: 'Link copied to clipboard',
		},
		invite: {
			text: 'Train with me on PixelFit — fitness with an 8-bit soul, right inside Telegram',
			title: 'Invite a friend',
			reward: '+{coins} coins for your friend’s first workout',
			progress: 'Rewarded invites: {rewarded}/{cap}',
			share: 'Share invite',
		},
		search: {
			placeholder: 'Enter a username...',
			searching: 'Searching...',
			minChars: 'At least 2 characters to search',
			found: 'Found: {count}',
			prompt: 'Enter at least 2 characters to search',
			notFound: 'No users found',
		},
		user: {
			level: 'Lv.{level}',
			statusFriend: 'Friend',
			statusPending: 'Sent',
			add: 'Add',
		},
		loading: 'Loading...',
		empty: {
			friendsMessage: 'You have no friends yet',
			friendsHint: 'Find friends by username',
			friendsButton: 'Find friends',
			requestsMessage: 'No incoming requests',
		},
		requests: {
			accept: 'Accept',
		},
		fallbackName: {
			friend: 'this friend',
			user: 'this user',
		},
		confirm: {
			titleReject: 'Reject request?',
			titleRemove: 'Remove friend?',
			textReject: 'Are you sure you want to reject the request from {name}?',
			textRemove: 'Are you sure you want to remove {name} from your friends?',
			cancel: 'Cancel',
			reject: 'Reject',
			remove: 'Remove',
		},
	},
};
