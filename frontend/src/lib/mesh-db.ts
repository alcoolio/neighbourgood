/**
 * Minimal IndexedDB persistence for mesh messages.
 * No external dependencies — uses raw IndexedDB API.
 */

import type { NGMeshMessage } from '$lib/bluetooth/protocol';

const DB_NAME = 'ng-mesh';
const STORE_NAME = 'messages';
const DB_VERSION = 1;

function openDB(): Promise<IDBDatabase> {
	return new Promise((resolve, reject) => {
		const request = indexedDB.open(DB_NAME, DB_VERSION);
		request.onupgradeneeded = () => {
			const db = request.result;
			if (!db.objectStoreNames.contains(STORE_NAME)) {
				db.createObjectStore(STORE_NAME, { keyPath: 'id' });
			}
		};
		request.onsuccess = () => resolve(request.result);
		request.onerror = () => reject(request.error);
	});
}

/** Persist mesh messages to IndexedDB (replaces all existing). */
export async function persistMessages(msgs: NGMeshMessage[]): Promise<void> {
	const db = await openDB();
	const tx = db.transaction(STORE_NAME, 'readwrite');
	const store = tx.objectStore(STORE_NAME);
	store.clear();
	for (const msg of msgs) {
		store.put(msg);
	}
	return new Promise((resolve, reject) => {
		tx.oncomplete = () => {
			db.close();
			resolve();
		};
		tx.onerror = () => {
			db.close();
			reject(tx.error);
		};
	});
}

/** Load all persisted mesh messages from IndexedDB. */
export async function loadMessages(): Promise<NGMeshMessage[]> {
	const db = await openDB();
	const tx = db.transaction(STORE_NAME, 'readonly');
	const store = tx.objectStore(STORE_NAME);
	const request = store.getAll();
	return new Promise((resolve, reject) => {
		request.onsuccess = () => {
			db.close();
			resolve(request.result as NGMeshMessage[]);
		};
		request.onerror = () => {
			db.close();
			reject(request.error);
		};
	});
}

/** Clear all persisted mesh messages. */
export async function clearMessages(): Promise<void> {
	const db = await openDB();
	const tx = db.transaction(STORE_NAME, 'readwrite');
	tx.objectStore(STORE_NAME).clear();
	return new Promise((resolve, reject) => {
		tx.oncomplete = () => {
			db.close();
			resolve();
		};
		tx.onerror = () => {
			db.close();
			reject(tx.error);
		};
	});
}
