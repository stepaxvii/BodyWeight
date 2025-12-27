import type { Avatar, AvatarId } from '$lib/types';

export const AVATARS: Avatar[] = [
	{ id: 'wolf', name: 'Wolf', name_ru: 'Волк', requiredLevel: 1, price: 0 },
	{ id: 'bear', name: 'Bear', name_ru: 'Медведь', requiredLevel: 1, price: 0 },
	{ id: 'fox', name: 'Fox', name_ru: 'Лиса', requiredLevel: 1, price: 0 },
	{ id: 'cat', name: 'Cat', name_ru: 'Кот', requiredLevel: 1, price: 0 },
	{ id: 'dog', name: 'Dog', name_ru: 'Пёс', requiredLevel: 3, price: 50 },
	{ id: 'rabbit', name: 'Rabbit', name_ru: 'Кролик', requiredLevel: 3, price: 50 },
	{ id: 'panda', name: 'Panda', name_ru: 'Панда', requiredLevel: 5, price: 100 },
	{ id: 'owl', name: 'Owl', name_ru: 'Сова', requiredLevel: 5, price: 100 },
	{ id: 'tiger', name: 'Tiger', name_ru: 'Тигр', requiredLevel: 7, price: 150 },
	{ id: 'lion', name: 'Lion', name_ru: 'Лев', requiredLevel: 10, price: 200 },
	{ id: 'monkey', name: 'Monkey', name_ru: 'Обезьяна', requiredLevel: 10, price: 200 },
	{ id: 'dragon', name: 'Dragon', name_ru: 'Дракон', requiredLevel: 15, price: 500 }
];

export function getAvatar(id: AvatarId): Avatar | undefined {
	return AVATARS.find(a => a.id === id);
}

export function getAvailableAvatars(level: number): Avatar[] {
	return AVATARS.filter(a => a.requiredLevel <= level);
}

export function canUnlockAvatar(avatar: Avatar, level: number, coins: number): boolean {
	return level >= avatar.requiredLevel && coins >= avatar.price;
}
