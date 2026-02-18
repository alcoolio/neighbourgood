/**
 * Server hook to proxy /api requests to the backend.
 * In development, Vite handles this. In production (Docker),
 * this hook forwards requests to the backend service.
 */

import type { Handle } from '@sveltejs/kit';

const API_BACKEND = process.env.API_BACKEND || 'http://localhost:8300';

export const handle: Handle = async ({ event, resolve }) => {
	if (event.url.pathname.startsWith('/api/') || event.url.pathname === '/api') {
		const backendPath = event.url.pathname.replace(/^\/api/, '');
		const backendUrl = `${API_BACKEND}${backendPath}${event.url.search}`;

		const headers = new Headers(event.request.headers);
		headers.delete('host');

		const response = await fetch(backendUrl, {
			method: event.request.method,
			headers,
			body: event.request.method !== 'GET' && event.request.method !== 'HEAD'
				? await event.request.arrayBuffer()
				: undefined,
			// @ts-expect-error duplex needed for streaming bodies
			duplex: 'half'
		});

		return new Response(response.body, {
			status: response.status,
			statusText: response.statusText,
			headers: response.headers
		});
	}

	return resolve(event);
};
