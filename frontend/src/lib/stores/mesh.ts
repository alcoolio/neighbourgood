/**
 * Mesh networking store — manages BLE connection state and message routing
 * for offline crisis communication via BitChat gateway.
 */

import { writable, derived, get } from 'svelte/store';
import {
	isBluetoothSupported,
	scanForBitchatNode,
	connectToNode,
	disconnect as bleDisconnect,
	sendMessage,
	onMessage,
	onDisconnect,
	getDeviceName
} from '$lib/bluetooth/connection';
import {
	encodeNGMessage,
	decodeNGMessage,
	createNGMessage,
	type NGMeshMessage,
	type NGMeshMessageType,
	type MeshTicketData,
	type MeshVoteData
} from '$lib/bluetooth/protocol';

export type MeshStatus = 'disconnected' | 'scanning' | 'connecting' | 'connected';

// ── Stores ────────────────────────────────────────────────────────────────────

export const meshStatus = writable<MeshStatus>('disconnected');
export const meshDeviceName = writable<string | null>(null);
export const meshMessages = writable<NGMeshMessage[]>([]);
export const meshPeers = writable<Set<string>>(new Set());

export const meshIsSupported = derived(meshStatus, () => isBluetoothSupported());
export const meshPeerCount = derived(meshPeers, (peers) => peers.size);

// Deduplication: track seen message IDs (sliding window of last 500)
const seenIds = new Set<string>();
const MAX_SEEN = 500;

let unsubMessage: (() => void) | null = null;
let unsubDisconnect: (() => void) | null = null;

// ── Actions ───────────────────────────────────────────────────────────────────

/** Connect to a nearby BitChat node. Prompts the user with Chrome device picker. */
export async function connectToMesh(): Promise<void> {
	if (!isBluetoothSupported()) {
		throw new Error('Web Bluetooth not supported');
	}

	try {
		meshStatus.set('scanning');
		const device = await scanForBitchatNode();

		meshStatus.set('connecting');
		await connectToNode(device);

		meshDeviceName.set(getDeviceName());
		meshStatus.set('connected');

		// Subscribe to incoming BLE messages
		unsubMessage = onMessage((data: DataView) => {
			const msg = decodeNGMessage(data);
			if (!msg) return; // Not an NG message, ignore

			// Deduplicate
			if (seenIds.has(msg.id)) return;
			addSeenId(msg.id);

			if (msg.type === 'heartbeat') {
				meshPeers.update((peers) => {
					const next = new Set(peers);
					next.add(msg.sender_name);
					return next;
				});
			} else {
				meshMessages.update((msgs) => [...msgs, msg]);
			}
		});

		// Handle unexpected disconnection
		unsubDisconnect = onDisconnect(() => {
			meshStatus.set('disconnected');
			meshDeviceName.set(null);
			cleanup();
		});
	} catch (err) {
		meshStatus.set('disconnected');
		meshDeviceName.set(null);
		cleanup();
		throw err;
	}
}

/** Disconnect from the current BitChat node. */
export function disconnectFromMesh(): void {
	bleDisconnect();
	meshStatus.set('disconnected');
	meshDeviceName.set(null);
	cleanup();
}

/** Send an NG message through the BLE mesh. */
export async function sendViaMesh(msg: NGMeshMessage): Promise<void> {
	const packet = encodeNGMessage(msg);
	await sendMessage(packet);
	// Track our own message to avoid processing it as incoming
	addSeenId(msg.id);
}

/** Broadcast an emergency ticket through the mesh. */
export async function broadcastEmergencyTicket(
	communityId: number,
	senderName: string,
	ticket: MeshTicketData
): Promise<NGMeshMessage> {
	const msg = createNGMessage('emergency_ticket', communityId, senderName, ticket as unknown as Record<string, unknown>);
	await sendViaMesh(msg);
	return msg;
}

/** Broadcast a crisis vote through the mesh. */
export async function broadcastCrisisVote(
	communityId: number,
	senderName: string,
	vote: MeshVoteData
): Promise<NGMeshMessage> {
	const msg = createNGMessage('crisis_vote', communityId, senderName, vote as unknown as Record<string, unknown>);
	await sendViaMesh(msg);
	return msg;
}

/** Broadcast a heartbeat to announce presence. */
export async function broadcastHeartbeat(
	communityId: number,
	senderName: string
): Promise<void> {
	const msg = createNGMessage('heartbeat', communityId, senderName, {});
	await sendViaMesh(msg);
}

/** Clear all stored mesh messages (e.g. after syncing to server). */
export function clearMeshMessages(): void {
	meshMessages.set([]);
}

/** Get current mesh messages snapshot. */
export function getMeshMessages(): NGMeshMessage[] {
	return get(meshMessages);
}

// ── Internals ─────────────────────────────────────────────────────────────────

function addSeenId(id: string): void {
	if (seenIds.size >= MAX_SEEN) {
		// Remove oldest entries (Set iterates in insertion order)
		const iter = seenIds.values();
		const toRemove = seenIds.size - MAX_SEEN + 1;
		for (let i = 0; i < toRemove; i++) {
			seenIds.delete(iter.next().value!);
		}
	}
	seenIds.add(id);
}

function cleanup(): void {
	if (unsubMessage) {
		unsubMessage();
		unsubMessage = null;
	}
	if (unsubDisconnect) {
		unsubDisconnect();
		unsubDisconnect = null;
	}
}
