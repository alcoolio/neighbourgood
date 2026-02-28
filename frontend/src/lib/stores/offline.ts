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
}

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

// Keep localStorage in sync whenever the queue changes.
offlineQueue.subscribe((q) => {
	if (typeof localStorage !== 'undefined') {
		localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
	}
});

export const queueCount = derived(offlineQueue, (q) => q.length);

// ── Actions ───────────────────────────────────────────────────────────────────

/** Add a request to the offline queue. Returns the generated id. */
export function enqueueRequest(req: Omit<QueuedRequest, 'id' | 'createdAt'>): string {
	const id = crypto.randomUUID();
	offlineQueue.update((q) => [
		...q,
		{ ...req, id, createdAt: new Date().toISOString() }
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
 * Failed requests stay in the queue for the next retry.
 */
export async function flushQueue(): Promise<{ succeeded: number; failed: number }> {
	const queue = get(offlineQueue);
	if (queue.length === 0) return { succeeded: 0, failed: 0 };

	let succeeded = 0;
	let failed = 0;
	const remaining: QueuedRequest[] = [];

	for (const req of queue) {
		try {
			const headers: Record<string, string> = {
				'Content-Type': 'application/json'
			};
			if (req.authToken) {
				headers['Authorization'] = `Bearer ${req.authToken}`;
			}
			const res = await fetch(`/api${req.path}`, {
				method: req.method,
				headers,
				body: JSON.stringify(req.body)
			});
			if (res.ok) {
				succeeded++;
			} else {
				remaining.push(req);
				failed++;
			}
		} catch {
			remaining.push(req);
			failed++;
		}
	}

	offlineQueue.set(remaining);
	return { succeeded, failed };
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
