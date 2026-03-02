/**
 * BitChat message protocol codec for NeighbourGood.
 *
 * Encodes NG-specific data (emergency tickets, crisis votes, etc.) as
 * JSON payloads inside standard BitChat broadcast messages so native
 * BitChat nodes relay them without modification.
 *
 * Packet format (simplified for gateway leaf-node usage):
 *   [1 byte type] [1 byte TTL] [4 bytes message ID] [2 bytes payload length] [N bytes payload]
 *
 * We use type 0x01 = broadcast message.
 * Payload is UTF-8 encoded JSON prefixed with "ng:" to identify NeighbourGood messages.
 */

const PACKET_TYPE_BROADCAST = 0x01;
const DEFAULT_TTL = 7;
const NG_PREFIX = 'ng:';

export type NGMeshMessageType =
	| 'emergency_ticket'
	| 'ticket_comment'
	| 'crisis_vote'
	| 'crisis_status'
	| 'direct_message'
	| 'heartbeat';

export interface NGMeshMessage {
	ng: 1;
	type: NGMeshMessageType;
	community_id: number;
	sender_name: string;
	ts: number;
	id: string;
	data: Record<string, unknown>;
}

export interface MeshTicketData {
	title: string;
	description: string;
	ticket_type: 'request' | 'offer' | 'emergency_ping';
	urgency: 'low' | 'medium' | 'high' | 'critical';
}

export interface MeshCommentData {
	ticket_mesh_id: string;
	body: string;
}

export interface MeshVoteData {
	vote_type: 'activate' | 'deactivate';
}

export interface MeshCrisisStatusData {
	new_mode: 'blue' | 'red';
}

const encoder = new TextEncoder();
const decoder = new TextDecoder();

/** Create a new NG mesh message with auto-generated ID and timestamp. */
export function createNGMessage(
	type: NGMeshMessageType,
	communityId: number,
	senderName: string,
	data: Record<string, unknown>
): NGMeshMessage {
	return {
		ng: 1,
		type,
		community_id: communityId,
		sender_name: senderName,
		ts: Date.now(),
		id: crypto.randomUUID(),
		data
	};
}

/** Encode an NG message into a BitChat-compatible binary packet. */
export function encodeNGMessage(msg: NGMeshMessage): Uint8Array {
	const json = NG_PREFIX + JSON.stringify(msg);
	const payloadBytes = encoder.encode(json);
	return createBitchatPacket(payloadBytes, DEFAULT_TTL);
}

/** Decode incoming BLE data into an NG message, or null if not NG format. */
export function decodeNGMessage(raw: DataView): NGMeshMessage | null {
	const parsed = parseBitchatPacket(raw);
	if (!parsed) return null;

	const text = decoder.decode(parsed.payload);
	if (!text.startsWith(NG_PREFIX)) return null;

	try {
		const obj = JSON.parse(text.slice(NG_PREFIX.length));
		if (obj.ng !== 1 || !obj.type || !obj.id) return null;
		return obj as NGMeshMessage;
	} catch {
		return null;
	}
}

/** Build a BitChat-compatible binary packet from a payload. */
export function createBitchatPacket(payload: Uint8Array, ttl: number = DEFAULT_TTL): Uint8Array {
	// Generate a random 4-byte message ID
	const msgId = new Uint8Array(4);
	crypto.getRandomValues(msgId);

	// Header: type(1) + TTL(1) + msgId(4) + length(2) = 8 bytes
	const header = new Uint8Array(8);
	header[0] = PACKET_TYPE_BROADCAST;
	header[1] = Math.min(ttl, 7);
	header.set(msgId, 2);
	// Payload length as big-endian uint16
	header[6] = (payload.length >> 8) & 0xff;
	header[7] = payload.length & 0xff;

	// Combine header + payload
	const packet = new Uint8Array(header.length + payload.length);
	packet.set(header, 0);
	packet.set(payload, header.length);
	return packet;
}

/** Parse a BitChat binary packet, extracting type, TTL, and payload. */
export function parseBitchatPacket(
	raw: DataView
): { type: number; ttl: number; payload: Uint8Array } | null {
	if (raw.byteLength < 8) return null;

	const type = raw.getUint8(0);
	const ttl = raw.getUint8(1);
	const payloadLength = raw.getUint16(6, false); // big-endian

	if (raw.byteLength < 8 + payloadLength) return null;

	const payload = new Uint8Array(raw.buffer, raw.byteOffset + 8, payloadLength);
	return { type, ttl, payload };
}
