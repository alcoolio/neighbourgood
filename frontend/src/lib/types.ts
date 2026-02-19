/**
 * Shared TypeScript interfaces matching backend schemas.
 * Import these instead of redefining locally in each page.
 */

export interface UserInfo {
	id: number;
	display_name: string;
	email: string;
	neighbourhood?: string | null;
	role?: string;
	created_at?: string;
}

export interface Resource {
	id: number;
	title: string;
	description: string | null;
	category: string;
	condition: string | null;
	image_url: string | null;
	is_available: boolean;
	owner_id: number;
	owner: UserInfo;
	created_at: string;
	updated_at?: string;
}

export interface Booking {
	id: number;
	resource_id: number;
	resource_title: string | null;
	borrower_id: number;
	borrower: UserInfo;
	start_date: string;
	end_date: string;
	message: string | null;
	status: string;
	created_at: string;
}

export interface CommunityOut {
	id: number;
	name: string;
	description: string | null;
	postal_code: string;
	city: string;
	country_code: string;
	mode: string;
	latitude: number | null;
	longitude: number | null;
	member_count: number;
	is_active: boolean;
	merged_into_id: number | null;
	created_by?: UserInfo;
	created_at?: string;
}

export interface CommunityMember {
	id: number;
	user: UserInfo;
	role: string;
	joined_at: string;
}

export interface MergeSuggestion {
	source: CommunityOut;
	target: CommunityOut;
	reason: string;
}

export interface Conversation {
	partner: UserInfo;
	last_message_body: string;
	last_message_at: string;
	unread_count: number;
}

export interface MessageOut {
	id: number;
	sender_id: number;
	sender: UserInfo;
	recipient_id: number;
	recipient: UserInfo;
	booking_id: number | null;
	body: string;
	is_read: boolean;
	created_at: string;
}

/**
 * Status color utility – maps booking/resource status to CSS variable names.
 */
export function statusColor(status: string): string {
	switch (status) {
		case 'approved':
			return 'var(--color-success)';
		case 'pending':
			return 'var(--color-warning)';
		case 'rejected':
		case 'cancelled':
			return 'var(--color-error)';
		case 'completed':
		default:
			return 'var(--color-text-muted)';
	}
}
