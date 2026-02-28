/**
 * Simple auth store – keeps the JWT token and user profile in memory.
 * In a real app this would sync to localStorage for persistence.
 */

import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

export interface UserProfile {
	id: number;
	email: string;
	display_name: string;
	neighbourhood: string | null;
	role: string;
	language_code: string;
	created_at: string;
}

export const token = writable<string | null>(
	browser ? localStorage.getItem('ng_token') : null
);
export const user = writable<UserProfile | null>(null);
export const isLoggedIn = derived(token, ($token) => $token !== null);

token.subscribe((val) => {
	if (typeof localStorage !== 'undefined') {
		if (val) localStorage.setItem('ng_token', val);
		else localStorage.removeItem('ng_token');
	}
});

export function logout() {
	token.set(null);
	user.set(null);
}

/**
 * Synchronize token from localStorage on client-side hydration.
 * Call this from onMount to ensure token is loaded after server-side rendering.
 */
export function syncTokenFromStorage() {
	if (browser) {
		const storedToken = localStorage.getItem('ng_token');
		if (storedToken) {
			token.set(storedToken);
		}
	}
}
