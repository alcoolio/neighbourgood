/**
 * Simple auth store – keeps the JWT token and user profile in memory.
 * In a real app this would sync to localStorage for persistence.
 */

import { writable, derived } from 'svelte/store';

export interface UserProfile {
	id: number;
	email: string;
	display_name: string;
	neighbourhood: string | null;
	role: string;
	created_at: string;
}

export const token = writable<string | null>(
	typeof localStorage !== 'undefined' ? localStorage.getItem('ng_token') : null
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
