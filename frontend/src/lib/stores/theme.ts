/**
 * Theme store – manages dark/light mode preference.
 * Persists to localStorage and syncs with the <html> data-theme attribute.
 */

import { writable } from 'svelte/store';

function getInitialTheme(): 'light' | 'dark' {
	if (typeof localStorage === 'undefined') return 'light';
	const stored = localStorage.getItem('ng_theme');
	if (stored === 'dark' || stored === 'light') return stored;
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

// ── Low-bandwidth mode ────────────────────────────────────────────────────────
// Eliminates transitions, shadows, and decorative images to reduce data usage
// and rendering cost on slow or metered connections.

function getInitialBandwidth(): 'normal' | 'low' {
	if (typeof localStorage === 'undefined') return 'normal';
	const stored = localStorage.getItem('ng_bandwidth');
	if (stored === 'low' || stored === 'normal') return stored;
	return 'normal';
}

export const bandwidth = writable<'normal' | 'low'>(getInitialBandwidth());

bandwidth.subscribe((val) => {
	if (typeof document !== 'undefined') {
		document.documentElement.setAttribute('data-bandwidth', val);
	}
	if (typeof localStorage !== 'undefined') {
		localStorage.setItem('ng_bandwidth', val);
	}
});

export function toggleBandwidth() {
	bandwidth.update((b) => (b === 'normal' ? 'low' : 'normal'));
}
