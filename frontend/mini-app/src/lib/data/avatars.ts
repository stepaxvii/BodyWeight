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
	{ id: 'thunder-fang', name: 'Thunder Fang', name_ru: 'Громовой Клык', requiredLevel: 7, price: 350 },
	{ id: 'cyber-ape', name: 'Cyber Ape', name_ru: 'Кибер-Примат', requiredLevel: 7, price: 375 },
	{ id: 'hydra', name: 'Hydra', name_ru: 'Гидра', requiredLevel: 10, price: 400 },
	{ id: 'minotaur', name: 'Minotaur', name_ru: 'Минотавр', requiredLevel: 12, price: 500 },
	{ id: 'kraken', name: 'Kraken', name_ru: 'Кракен', requiredLevel: 15, price: 750 },
	{ id: 'leviathan', name: 'Leviathan', name_ru: 'Левиафан', requiredLevel: 20, price: 1000 },
	{ id: 'titan', name: 'Titan', name_ru: 'Титан', requiredLevel: 25, price: 1500 },

	// === НОВЫЕ ГЕРОИ (Stardew-редизайн) ===
	{ id: 'solar-lion', name: 'Solar Lion', name_ru: 'Солнечный Лев', requiredLevel: 8, price: 350 },
	{ id: 'crystal-stag', name: 'Crystal Stag', name_ru: 'Хрустальный Олень', requiredLevel: 10, price: 450 },
	{ id: 'storm-eagle', name: 'Storm Eagle', name_ru: 'Штормовой Орёл', requiredLevel: 14, price: 600 },
	{ id: 'void-serpent', name: 'Void Serpent', name_ru: 'Бездонный Змей', requiredLevel: 18, price: 900 },
	{ id: 'magma-golem', name: 'Magma Golem', name_ru: 'Магма-Голем', requiredLevel: 22, price: 1200 }
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
