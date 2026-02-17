<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { isLoggedIn, user } from '$lib/stores/auth';

	interface Booking {
		id: number;
		resource_id: number;
		resource_title: string | null;
		borrower_id: number;
		borrower: { id: number; display_name: string };
		start_date: string;
		end_date: string;
		message: string | null;
		status: string;
		created_at: string;
	}

	let bookings: Booking[] = $state([]);
	let total = $state(0);
	let loading = $state(true);
	let roleFilter = $state('');
	let statusFilter = $state('');

	async function loadBookings() {
		loading = true;
		try {
			const params = new URLSearchParams();
			if (roleFilter) params.set('role', roleFilter);
			if (statusFilter) params.set('status', statusFilter);
			const res = await api<{ items: Booking[]; total: number }>(
				`/bookings?${params.toString()}`,
				{ auth: true }
			);
			bookings = res.items;
			total = res.total;
		} catch {
			bookings = [];
		} finally {
			loading = false;
		}
	}

	async function updateStatus(bookingId: number, newStatus: string) {
		try {
			await api(`/bookings/${bookingId}`, {
				method: 'PATCH',
				auth: true,
				body: { status: newStatus }
			});
			await loadBookings();
		} catch (err) {
			alert(err instanceof Error ? err.message : 'Failed to update booking');
		}
	}

	function isOwnerOf(b: Booking): boolean {
		return b.borrower_id !== $user?.id;
	}

	function isBorrowerOf(b: Booking): boolean {
		return b.borrower_id === $user?.id;
	}

	function statusColor(s: string): string {
		if (s === 'approved') return '#059669';
		if (s === 'pending') return '#d97706';
		if (s === 'rejected' || s === 'cancelled') return '#ef4444';
		if (s === 'completed') return '#6b7280';
		return '#6b7280';
	}

	onMount(loadBookings);

	$effect(() => {
		roleFilter;
		statusFilter;
		loadBookings();
	});
</script>

{#if !$isLoggedIn}
	<div class="empty-state">
		<p>Please <a href="/login">log in</a> to view your bookings.</p>
	</div>
{:else}
	<div class="bookings-page">
		<h1>My Bookings</h1>

		<div class="filter-bar">
			<select bind:value={roleFilter}>
				<option value="">All</option>
				<option value="borrower">My Requests</option>
				<option value="owner">Incoming Requests</option>
			</select>
			<select bind:value={statusFilter}>
				<option value="">Any Status</option>
				<option value="pending">Pending</option>
				<option value="approved">Approved</option>
				<option value="rejected">Rejected</option>
				<option value="cancelled">Cancelled</option>
				<option value="completed">Completed</option>
			</select>
			<span class="result-count">{total} booking{total !== 1 ? 's' : ''}</span>
		</div>

		{#if loading}
			<p class="loading">Loading...</p>
		{:else if bookings.length === 0}
			<div class="empty-state">
				<p>No bookings found.</p>
			</div>
		{:else}
			<div class="booking-table">
				{#each bookings as b}
					<div class="booking-row">
						<div class="booking-info">
							<a href="/resources/{b.resource_id}" class="resource-link">
								{b.resource_title ?? `Resource #${b.resource_id}`}
							</a>
							<div class="booking-meta">
								<span class="dates">{b.start_date} &rarr; {b.end_date}</span>
								{#if isBorrowerOf(b)}
									<span class="role-tag">You requested</span>
								{:else}
									<span class="role-tag">{b.borrower.display_name} requested</span>
								{/if}
							</div>
							{#if b.message}
								<p class="message">"{b.message}"</p>
							{/if}
						</div>
						<div class="booking-actions">
							<span class="status" style="color: {statusColor(b.status)}">{b.status}</span>
							{#if b.status === 'pending' && isOwnerOf(b)}
								<button class="btn-approve" onclick={() => updateStatus(b.id, 'approved')}>Approve</button>
								<button class="btn-reject" onclick={() => updateStatus(b.id, 'rejected')}>Reject</button>
							{/if}
							{#if b.status === 'pending' && isBorrowerOf(b)}
								<button class="btn-cancel" onclick={() => updateStatus(b.id, 'cancelled')}>Cancel</button>
							{/if}
							{#if b.status === 'approved'}
								<button class="btn-complete" onclick={() => updateStatus(b.id, 'completed')}>Mark Done</button>
								{#if isBorrowerOf(b)}
									<button class="btn-cancel" onclick={() => updateStatus(b.id, 'cancelled')}>Cancel</button>
								{/if}
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}

<style>
	.bookings-page {
		max-width: 800px;
	}

	h1 {
		font-size: 1.75rem;
		margin-bottom: 1.5rem;
	}

	.filter-bar {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.filter-bar select {
		padding: 0.4rem 0.6rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.85rem;
		background: var(--color-surface);
		color: var(--color-text);
	}

	.result-count {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-left: auto;
	}

	.booking-table {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.booking-row {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1rem;
	}

	.booking-info {
		flex: 1;
		min-width: 0;
	}

	.resource-link {
		font-weight: 600;
		font-size: 1rem;
		color: var(--color-text);
		text-decoration: none;
	}

	.resource-link:hover {
		color: var(--color-primary);
	}

	.booking-meta {
		display: flex;
		gap: 0.75rem;
		font-size: 0.82rem;
		color: var(--color-text-muted);
		margin-top: 0.25rem;
	}

	.role-tag {
		font-style: italic;
	}

	.message {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-top: 0.35rem;
		font-style: italic;
	}

	.booking-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.status {
		font-weight: 700;
		text-transform: capitalize;
		font-size: 0.85rem;
		min-width: 70px;
	}

	.btn-approve, .btn-reject, .btn-cancel, .btn-complete {
		padding: 0.3rem 0.65rem;
		border-radius: var(--radius);
		font-size: 0.8rem;
		cursor: pointer;
		border: 1px solid;
	}

	.btn-approve {
		background: #ecfdf5;
		color: #059669;
		border-color: #a7f3d0;
	}
	.btn-approve:hover { background: #d1fae5; }

	.btn-reject, .btn-cancel {
		background: #fef2f2;
		color: #ef4444;
		border-color: #fca5a5;
	}
	.btn-reject:hover, .btn-cancel:hover { background: #fee2e2; }

	.btn-complete {
		background: #f5f5f5;
		color: #6b7280;
		border-color: #d1d5db;
	}
	.btn-complete:hover { background: #e5e7eb; }

	.loading {
		color: var(--color-text-muted);
	}

	.empty-state {
		text-align: center;
		padding: 3rem 1rem;
		color: var(--color-text-muted);
	}
</style>
