import { writable } from 'svelte/store';

export const token = writable<string | null>(null);
export const isAuthenticated = writable(false);
export const isLoading = writable(true);
