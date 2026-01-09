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

		// Don't start a new request if already loading
		if (this._loading) {
			// Wait for the current request to finish
			return new Promise((resolve) => {
				const checkLoaded = setInterval(() => {
					if (!this._loading) {
						clearInterval(checkLoaded);
						resolve(this._exercises);
					}
				}, 100);
			});
		}

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

			// Try to load from localStorage cache as fallback
			try {
				const cached = localStorage.getItem('exercises_cache');
				if (cached) {
					const { data, timestamp } = JSON.parse(cached);
					// Use cache if less than 24 hours old
					if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
						console.log('Using cached exercises from localStorage');
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
