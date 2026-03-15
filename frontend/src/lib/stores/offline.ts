/**
 * Offline detection and request queuing store.
 *
 * Tracks connectivity via navigator.onLine + browser events.
 * Persists a queue of failed POST/PATCH requests to localStorage so they
 * can be replayed automatically when the device comes back online.
 */

import { writable, derived, get } from 'svelte/store';

export interface QueuedRequest {
	id: string;
	method: string;
	path: string;
	body: unknown;
	authToken: string | null;
	createdAt: string;
	/** Human-readable description shown in the UI. */
	label: string;
	/** Whether this request was also broadcast via BLE mesh. */
	meshSent?: boolean;
	/** Number of times this request has been retried on server/network errors. */
	retryCount?: number;
}

const MAX_RETRIES = 5;
const TOKEN_KEY = 'ng_token';

const QUEUE_KEY = 'ng_offline_queue';

function loadQueue(): QueuedRequest[] {
	if (typeof localStorage === 'undefined') return [];
	try {
		return JSON.parse(localStorage.getItem(QUEUE_KEY) ?? '[]');
	} catch {
		return [];
	}
}

// ── Stores ────────────────────────────────────────────────────────────────────

export const isOnline = writable(
	typeof navigator !== 'undefined' ? navigator.onLine : true
);

export const offlineQueue = writable<QueuedRequest[]>(loadQueue());

const QUEUE_CACHE = 'ng-offline-queue';
const QUEUE_CACHE_KEY = '/_internal/offline-queue';

// Keep localStorage and Cache API in sync whenever the queue changes.
offlineQueue.subscribe((q) => {
	if (typeof localStorage !== 'undefined') {
		localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
	}
	// Mirror to Cache API so the service worker can access the queue for Background Sync.
	if (typeof caches !== 'undefined') {
		caches.open(QUEUE_CACHE).then((cache) => {
			if (q.length > 0) {
				cache.put(
					QUEUE_CACHE_KEY,
					new Response(JSON.stringify(q), {
						headers: { 'Content-Type': 'application/json' }
					})
				);
			} else {
				cache.delete(QUEUE_CACHE_KEY);
			}
		}).catch(() => { /* Cache API unavailable — ignore */ });
	}
});

export const queueCount = derived(offlineQueue, (q) => q.length);

// ── Actions ───────────────────────────────────────────────────────────────────

/** Add a request to the offline queue. Returns the generated id. */
export function enqueueRequest(
	req: Omit<QueuedRequest, 'id' | 'createdAt'>,
	options?: { meshSent?: boolean }
): string {
	const id = crypto.randomUUID();
	offlineQueue.update((q) => [
		...q,
		{ ...req, id, createdAt: new Date().toISOString(), meshSent: options?.meshSent ?? false }
	]);
	return id;
}

/** Remove a specific request from the queue (e.g. user cancels it). */
export function removeFromQueue(id: string) {
	offlineQueue.update((q) => q.filter((r) => r.id !== id));
}

/**
 * Attempt to replay all queued requests against the live API.
 * Successfully sent requests are removed from the queue.
 * Classifies failures: 401 retries with fresh token, other 4xx are dropped,
 * 5xx/network errors retry up to MAX_RETRIES times before being dropped.
 */
export async function flushQueue(): Promise<{ succeeded: number; failed: number; dropped: number }> {
	const queue = get(offlineQueue);
	if (queue.length === 0) return { succeeded: 0, failed: 0, dropped: 0 };

	let succeeded = 0;
	let failed = 0;
	let dropped = 0;
	const remaining: QueuedRequest[] = [];

	for (const req of queue) {
		try {
			const headers: Record<string, string> = {};
			if (req.method !== 'DELETE') {
				headers['Content-Type'] = 'application/json';
			}
			if (req.authToken) {
				headers['Authorization'] = `Bearer ${req.authToken}`;
			}
			const res = await fetch(`/api${req.path}`, {
				method: req.method,
				headers,
				body: req.method !== 'DELETE' ? JSON.stringify(req.body) : undefined
			});

			if (res.ok) {
				succeeded++;
			} else if (res.status === 401) {
				// Token expired — try with the current live token
				const liveToken = typeof localStorage !== 'undefined'
					? localStorage.getItem(TOKEN_KEY)
					: null;
				if (liveToken && liveToken !== req.authToken) {
					const retryHeaders: Record<string, string> = {
						'Authorization': `Bearer ${liveToken}`
					};
					if (req.method !== 'DELETE') {
						retryHeaders['Content-Type'] = 'application/json';
					}
					const retryRes = await fetch(`/api${req.path}`, {
						method: req.method,
						headers: retryHeaders,
						body: req.method !== 'DELETE' ? JSON.stringify(req.body) : undefined
					});
					if (retryRes.ok) {
						succeeded++;
					} else {
						// Fresh token also failed — drop the request
						dropped++;
					}
				} else {
					// No fresh token available — drop
					dropped++;
				}
			} else if (res.status >= 400 && res.status < 500) {
				// Other client errors (422, 404, etc.) — retrying won't help
				dropped++;
			} else {
				// 5xx server error — retry with a limit
				const retries = (req.retryCount ?? 0) + 1;
				if (retries >= MAX_RETRIES) {
					dropped++;
				} else {
					remaining.push({ ...req, retryCount: retries });
					failed++;
				}
			}
		} catch {
			// Network error — retry with a limit
			const retries = (req.retryCount ?? 0) + 1;
			if (retries >= MAX_RETRIES) {
				dropped++;
			} else {
				remaining.push({ ...req, retryCount: retries });
				failed++;
			}
		}
	}

	offlineQueue.set(remaining);
	return { succeeded, failed, dropped };
}

/**
 * Register window online/offline listeners.
 * Call once from the root layout's onMount (browser-only).
 */
export function initOfflineTracking() {
	if (typeof window === 'undefined') return;
	window.addEventListener('online', () => isOnline.set(true));
	window.addEventListener('offline', () => isOnline.set(false));
}
