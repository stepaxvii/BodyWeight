/**
 * Global store for caching all exercises
 * Reduces API calls and improves performance
 */

import { api } from '$lib/api/client';
import type { Exercise } from '$lib/types';

class ExercisesStore {
	private _exercises = $state<Exercise[]>([]);
	private _loading = $state(false);
	private _loaded = $state(false);
	private _error = $state<string | null>(null);
	private _pendingLoad: Promise<Exercise[]> | null = null;

	get exercises() {
		return this._exercises;
	}

	get loading() {
		return this._loading;
	}

	get loaded() {
		return this._loaded;
	}

	get error() {
		return this._error;
	}

	/**
	 * Load all exercises from API and cache them
	 * If already loaded, returns cached data immediately
	 */
	async loadAll(): Promise<Exercise[]> {
		// Return cached data if already loaded
		if (this._loaded && this._exercises.length > 0) {
			return this._exercises;
		}

		// If already loading, return the same Promise (dedup)
		if (this._pendingLoad) {
			return this._pendingLoad;
		}

		this._pendingLoad = this._doLoad();
		try {
			return await this._pendingLoad;
		} finally {
			this._pendingLoad = null;
		}
	}

	private async _doLoad(): Promise<Exercise[]> {
		this._loading = true;
		this._error = null;

		try {
			const exercises = await api.getAllExercises();
			this._exercises = exercises;
			this._loaded = true;

			// Cache to localStorage for even faster subsequent loads
			try {
				localStorage.setItem('exercises_cache', JSON.stringify({
					data: exercises,
					timestamp: Date.now()
				}));
			} catch (e) {
				console.warn('Failed to cache exercises to localStorage:', e);
			}

			return exercises;
		} catch (error) {
			console.error('Failed to load exercises:', error);
			this._error = error instanceof Error ? error.message : 'Unknown error';

			// Try to load from localStorage cache as fallback (any age when offline)
			try {
				const cached = localStorage.getItem('exercises_cache');
				if (cached) {
					const { data } = JSON.parse(cached);
					if (data && data.length > 0) {
						this._exercises = data;
						this._loaded = true;
						return data;
					}
				}
			} catch (e) {
				console.warn('Failed to load from localStorage cache:', e);
			}

			throw error;
		} finally {
			this._loading = false;
		}
	}

	/**
	 * Find exercise by slug
	 */
	findBySlug(slug: string): Exercise | undefined {
		return this._exercises.find(e => e.slug === slug);
	}

	/**
	 * Clear cache and force reload on next loadAll()
	 */
	clearCache() {
		this._exercises = [];
		this._loaded = false;
		this._error = null;
		try {
			localStorage.removeItem('exercises_cache');
		} catch (e) {
			console.warn('Failed to clear localStorage cache:', e);
		}
	}
}

export const exercisesStore = new ExercisesStore();
