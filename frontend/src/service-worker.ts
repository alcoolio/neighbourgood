/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

declare const self: ServiceWorkerGlobalScope;

// One cache per build version — old caches are deleted on activate.
const STATIC_CACHE = `ng-static-${version}`;
// API cache is kept across versions (serves stale data when offline).
const API_CACHE = 'ng-api-v1';

// All SvelteKit build chunks + everything in /static
const PRECACHE_ASSETS = [...build, ...files];

// ── Install: precache all static + build assets ──────────────────────────────

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(STATIC_CACHE)
			.then((cache) => cache.addAll(PRECACHE_ASSETS))
			// Activate immediately — don't wait for existing tabs to close.
			.then(() => self.skipWaiting())
	);
});

// ── Activate: delete old static caches (previous build versions) ─────────────

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) =>
				Promise.all(
					keys
						// Remove old versioned static caches but keep the API cache.
						.filter((k) => k.startsWith('ng-static-') && k !== STATIC_CACHE)
						.map((k) => caches.delete(k))
				)
			)
			// Take control of all open tabs immediately.
			.then(() => self.clients.claim())
	);
});

// ── Fetch: route-based caching strategies ────────────────────────────────────

self.addEventListener('fetch', (event) => {
	const { request } = event;
	const url = new URL(request.url);

	// Only handle GET from the same origin.
	if (request.method !== 'GET') return;
	if (url.origin !== self.location.origin) return;

	// API requests: network-first, fall back to cached response when offline.
	if (url.pathname.startsWith('/api/')) {
		event.respondWith(apiNetworkFirst(request));
		return;
	}

	// Precached build/static assets: cache-first (they have hashed names).
	if (PRECACHE_ASSETS.includes(url.pathname)) {
		event.respondWith(cacheFirst(request, STATIC_CACHE));
		return;
	}

	// SvelteKit page navigations: network-first, branded offline fallback.
	if (request.mode === 'navigate') {
		event.respondWith(navigationNetworkFirst(request));
		return;
	}
});

// ── Strategy helpers ─────────────────────────────────────────────────────────

/** Cache-first: return cached version, fetch from network only on miss. */
async function cacheFirst(request: Request, cacheName: string): Promise<Response> {
	const cached = await caches.match(request, { cacheName });
	if (cached) return cached;
	const response = await fetch(request);
	const cache = await caches.open(cacheName);
	cache.put(request, response.clone());
	return response;
}

/**
 * Network-first for API: try the network, cache successful responses,
 * serve stale cache on failure. Returns a 503 if nothing is cached.
 */
async function apiNetworkFirst(request: Request): Promise<Response> {
	const cache = await caches.open(API_CACHE);
	try {
		const response = await fetch(request);
		if (response.ok) {
			cache.put(request, response.clone());
		}
		return response;
	} catch {
		const cached = await cache.match(request);
		if (cached) return cached;
		return new Response(JSON.stringify({ detail: 'You are offline' }), {
			status: 503,
			headers: { 'Content-Type': 'application/json' }
		});
	}
}

/**
 * Network-first for page navigations: try network, serve the offline
 * fallback page when the network is unavailable.
 */
async function navigationNetworkFirst(request: Request): Promise<Response> {
	try {
		return await fetch(request);
	} catch {
		const offline = await caches.match('/offline.html');
		return offline ?? new Response('Offline', { status: 503 });
	}
}
