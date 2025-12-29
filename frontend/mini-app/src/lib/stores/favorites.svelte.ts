import { api } from '$lib/api/client';
import { telegram } from './telegram.svelte';

/**
 * Store for managing user's favorite exercises
 */
class FavoritesStore {
	favoriteIds = $state<Set<number>>(new Set());
	isLoading = $state(false);
	isLoaded = $state(false);

	/**
	 * Load favorite exercise IDs from the API
	 */
	async loadFavorites(): Promise<void> {
		if (this.isLoaded) return; // Don't reload if already loaded

		this.isLoading = true;
		try {
			const ids = await api.getFavoriteIds();
			this.favoriteIds = new Set(ids);
			this.isLoaded = true;
		} catch (err) {
			console.error('Failed to load favorites:', err);
		} finally {
			this.isLoading = false;
		}
	}

	/**
	 * Toggle favorite status for an exercise
	 */
	async toggleFavorite(exerciseId: number): Promise<void> {
		telegram.hapticImpact('light');

		// Optimistic update
		const wasFavorite = this.favoriteIds.has(exerciseId);
		if (wasFavorite) {
			const newSet = new Set(this.favoriteIds);
			newSet.delete(exerciseId);
			this.favoriteIds = newSet;
		} else {
			this.favoriteIds = new Set([...this.favoriteIds, exerciseId]);
		}

		try {
			const result = await api.toggleFavorite(exerciseId);

			// Sync with server response
			if (result.is_favorite) {
				this.favoriteIds = new Set([...this.favoriteIds, exerciseId]);
			} else {
				const newSet = new Set(this.favoriteIds);
				newSet.delete(exerciseId);
				this.favoriteIds = newSet;
			}
		} catch (err) {
			// Revert on error
			console.error('Failed to toggle favorite:', err);
			if (wasFavorite) {
				this.favoriteIds = new Set([...this.favoriteIds, exerciseId]);
			} else {
				const newSet = new Set(this.favoriteIds);
				newSet.delete(exerciseId);
				this.favoriteIds = newSet;
			}
			telegram.hapticNotification('error');
		}
	}

	/**
	 * Check if an exercise is favorited
	 */
	isFavorite(exerciseId: number): boolean {
		return this.favoriteIds.has(exerciseId);
	}

	/**
	 * Get count of favorites
	 */
	get count(): number {
		return this.favoriteIds.size;
	}
}

export const favoritesStore = new FavoritesStore();
