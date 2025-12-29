import type { Avatar, AvatarId } from '$lib/types';

export const AVATARS: Avatar[] = [
	// === БЕСПЛАТНЫЕ ЖИВОТНЫЕ (Уровень 1) ===
	{ id: 'shadow-wolf', name: 'Shadow Wolf', name_ru: 'Теневой Волк', requiredLevel: 1, price: 0 },
	{ id: 'iron-bear', name: 'Iron Bear', name_ru: 'Железный Медведь', requiredLevel: 1, price: 0 },
	{ id: 'fire-fox', name: 'Fire Fox', name_ru: 'Огненный Лис', requiredLevel: 1, price: 0 },
	{ id: 'night-panther', name: 'Night Panther', name_ru: 'Ночная Пантера', requiredLevel: 1, price: 0 },

	// === МИФИЧЕСКИЕ СУЩЕСТВА (Платные) ===
	{ id: 'phoenix', name: 'Phoenix', name_ru: 'Феникс', requiredLevel: 3, price: 100 },
	{ id: 'griffin', name: 'Griffin', name_ru: 'Грифон', requiredLevel: 5, price: 200 },
	{ id: 'cerberus', name: 'Cerberus', name_ru: 'Цербер', requiredLevel: 7, price: 300 },
	{ id: 'hydra', name: 'Hydra', name_ru: 'Гидра', requiredLevel: 10, price: 400 },
	{ id: 'minotaur', name: 'Minotaur', name_ru: 'Минотавр', requiredLevel: 12, price: 500 },
	{ id: 'kraken', name: 'Kraken', name_ru: 'Кракен', requiredLevel: 15, price: 750 },
	{ id: 'leviathan', name: 'Leviathan', name_ru: 'Левиафан', requiredLevel: 20, price: 1000 },
	{ id: 'titan', name: 'Titan', name_ru: 'Титан', requiredLevel: 25, price: 1500 }
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
