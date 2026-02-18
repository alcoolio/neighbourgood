/**
 * Theme store – manages dark/light mode preference.
 * Persists to localStorage and syncs with the <html> data-theme attribute.
 */

import { writable } from 'svelte/store';

function getInitialTheme(): 'light' | 'dark' {
	if (typeof localStorage === 'undefined') return 'light';
	const stored = localStorage.getItem('ng_theme');
	if (stored === 'dark' || stored === 'light') return stored;
	if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
		return 'dark';
	}
	return 'light';
}

export const theme = writable<'light' | 'dark'>(getInitialTheme());

theme.subscribe((val) => {
	if (typeof document !== 'undefined') {
		document.documentElement.setAttribute('data-theme', val);
	}
	if (typeof localStorage !== 'undefined') {
		localStorage.setItem('ng_theme', val);
	}
});

export function toggleTheme() {
	theme.update((t) => (t === 'light' ? 'dark' : 'light'));
}
