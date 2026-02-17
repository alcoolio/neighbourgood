/**
 * Thin wrapper around fetch for talking to the backend API.
 * All paths are prefixed with /api which the Vite dev proxy rewrites to the backend.
 */

import { get } from 'svelte/store';
import { token } from '$lib/stores/auth';

const BASE = '/api';

interface RequestOptions {
	method?: string;
	body?: unknown;
	auth?: boolean;
}

export async function api<T = unknown>(path: string, opts: RequestOptions = {}): Promise<T> {
	const { method = 'GET', body, auth = false } = opts;

	const headers: Record<string, string> = {};

	if (body) {
		headers['Content-Type'] = 'application/json';
	}
	if (auth) {
		const t = get(token);
		if (t) headers['Authorization'] = `Bearer ${t}`;
	}

	const res = await fetch(`${BASE}${path}`, {
		method,
		headers,
		body: body ? JSON.stringify(body) : undefined
	});

	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Request failed: ${res.status}`);
	}

	if (res.status === 204) return undefined as T;
	return res.json();
}

/**
 * Upload a file (multipart/form-data) to the backend.
 */
export async function apiUpload<T = unknown>(path: string, file: File): Promise<T> {
	const headers: Record<string, string> = {};
	const t = get(token);
	if (t) headers['Authorization'] = `Bearer ${t}`;

	const formData = new FormData();
	formData.append('file', file);

	const res = await fetch(`${BASE}${path}`, {
		method: 'POST',
		headers,
		body: formData
	});

	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Upload failed: ${res.status}`);
	}

	return res.json();
}
