import type { DistrictResponse } from '$lib/types';
import { api } from '$lib/api/client';

/**
 * City / districts state (Svelte 5 runes singleton).
 *
 * Holds the list of districts for the RPG `/city` route. `load()` fetches the
 * list once (idempotent unless `force`), `reloadDistrict()` refreshes a single
 * district in place after a quest action so the route can swap offer ⇄ HUD
 * without a full reload.
 */
class CityStore {
	districts = $state<DistrictResponse[]>([]);
	loaded = $state(false);
	loading = $state(false);
	error = $state<string | null>(null);

	async load(force = false): Promise<void> {
		if (this.loaded && !force) return;
		this.loading = true;
		this.error = null;
		try {
			const res = await api.getDistricts();
			this.districts = res.districts ?? [];
			this.loaded = true;
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to load districts';
		} finally {
			this.loading = false;
		}
	}

	/** Fetch one district's full detail (with quest_progress.exercises) and splice it in. */
	async reloadDistrict(id: string): Promise<DistrictResponse | null> {
		try {
			const fresh = await api.getDistrict(id);
			const i = this.districts.findIndex((d) => d.id === id);
			if (i >= 0) this.districts[i] = fresh;
			else this.districts.push(fresh);
			return fresh;
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to load district';
			return null;
		}
	}

	get(id: string | null | undefined): DistrictResponse | undefined {
		if (!id) return undefined;
		return this.districts.find((d) => d.id === id);
	}
}

export const cityStore = new CityStore();
