<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api, apiUpload } from '$lib/api';
	import { isLoggedIn, user } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	interface Resource {
		id: number;
		title: string;
		description: string | null;
		category: string;
		condition: string | null;
		image_url: string | null;
		is_available: boolean;
		owner_id: number;
		owner: {
			id: number;
			display_name: string;
			neighbourhood: string | null;
			email: string;
		};
		created_at: string;
		updated_at: string;
	}

	interface Booking {
		id: number;
		resource_id: number;
		borrower_id: number;
		borrower: { display_name: string };
		start_date: string;
		end_date: string;
		message: string | null;
		status: string;
	}

	let resource: Resource | null = $state(null);
	let bookings: Booking[] = $state([]);
	let error = $state('');
	let loading = $state(true);

	// Booking form
	let showBookingForm = $state(false);
	let bookStartDate = $state('');
	let bookEndDate = $state('');
	let bookMessage = $state('');
	let bookError = $state('');

	// Image upload
	let imageInput: HTMLInputElement;

	const isOwner = $derived(
		$isLoggedIn && resource !== null && $user?.id === resource.owner_id
	);

	const canBook = $derived(
		$isLoggedIn && resource !== null && $user?.id !== resource.owner_id && resource.is_available
	);

	onMount(async () => {
		const id = $page.params.id;
		try {
			resource = await api<Resource>(`/resources/${id}`);
			await loadBookings(Number(id));
		} catch (err) {
			error = err instanceof Error ? err.message : 'Resource not found';
		} finally {
			loading = false;
		}
	});

	async function loadBookings(resourceId: number) {
		try {
			const now = new Date();
			const res = await api<Booking[]>(
				`/bookings/resource/${resourceId}/calendar?month=${now.getMonth() + 1}&year=${now.getFullYear()}`
			);
			bookings = res;
		} catch {
			bookings = [];
		}
	}

	async function toggleAvailability() {
		if (!resource) return;
		try {
			resource = await api<Resource>(`/resources/${resource.id}`, {
				method: 'PATCH',
				auth: true,
				body: { is_available: !resource.is_available }
			});
		} catch (err) {
			error = err instanceof Error ? err.message : 'Update failed';
		}
	}

	async function deleteResource() {
		if (!resource || !confirm('Delete this resource?')) return;
		try {
			await api(`/resources/${resource.id}`, { method: 'DELETE', auth: true });
			goto('/resources');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Delete failed';
		}
	}

	async function handleImageUpload() {
		if (!resource || !imageInput?.files?.length) return;
		try {
			resource = await apiUpload<Resource>(`/resources/${resource.id}/image`, imageInput.files[0]);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Upload failed';
		}
	}

	async function handleBooking(e: Event) {
		e.preventDefault();
		if (!resource) return;
		bookError = '';
		try {
			await api('/bookings', {
				method: 'POST',
				auth: true,
				body: {
					resource_id: resource.id,
					start_date: bookStartDate,
					end_date: bookEndDate,
					message: bookMessage || null
				}
			});
			showBookingForm = false;
			bookStartDate = '';
			bookEndDate = '';
			bookMessage = '';
			await loadBookings(resource.id);
		} catch (err) {
			bookError = err instanceof Error ? err.message : 'Booking failed';
		}
	}

	function statusColor(status: string): string {
		if (status === 'approved') return '#059669';
		if (status === 'pending') return '#d97706';
		if (status === 'rejected' || status === 'cancelled') return '#ef4444';
		return '#6b7280';
	}
</script>

{#if loading}
	<p class="loading">Loading...</p>
{:else if error}
	<div class="error-page">
		<h1>Oops</h1>
		<p>{error}</p>
		<a href="/resources">Back to resources</a>
	</div>
{:else if resource}
	<article class="resource-detail">
		<a href="/resources" class="back-link">&larr; Back to resources</a>

		{#if resource.image_url}
			<div class="detail-image">
				<img src="/api{resource.image_url}" alt={resource.title} />
			</div>
		{/if}

		<div class="detail-header">
			<div class="badges">
				<span class="category-badge">{resource.category}</span>
				{#if resource.condition}
					<span class="condition-badge">{resource.condition}</span>
				{/if}
				<span class="availability" class:available={resource.is_available}>
					{resource.is_available ? 'Available' : 'Unavailable'}
				</span>
			</div>
			<h1>{resource.title}</h1>
		</div>

		{#if resource.description}
			<div class="section-card">
				<p>{resource.description}</p>
			</div>
		{/if}

		<div class="owner-section">
			<h3>Shared by</h3>
			<p class="owner-name">{resource.owner.display_name}</p>
			{#if resource.owner.neighbourhood}
				<p class="owner-neighbourhood">{resource.owner.neighbourhood}</p>
			{/if}
		</div>

		<div class="meta">
			<span>Listed {new Date(resource.created_at).toLocaleDateString()}</span>
		</div>

		<!-- Owner actions -->
		{#if isOwner}
			<div class="section-card owner-panel">
				<h3>Manage Resource</h3>
				<div class="owner-actions">
					<button class="btn-secondary" onclick={toggleAvailability}>
						{resource.is_available ? 'Mark Unavailable' : 'Mark Available'}
					</button>
					<label class="btn-secondary upload-btn">
						Upload Image
						<input
							type="file"
							accept="image/jpeg,image/png,image/webp,image/gif"
							bind:this={imageInput}
							onchange={handleImageUpload}
							hidden
						/>
					</label>
					<button class="btn-danger" onclick={deleteResource}>Delete</button>
				</div>
			</div>
		{/if}

		<!-- Booking section -->
		{#if bookings.length > 0}
			<div class="section-card">
				<h3>Upcoming Bookings</h3>
				<div class="booking-list">
					{#each bookings as b}
						<div class="booking-item">
							<span class="booking-dates">{b.start_date} &rarr; {b.end_date}</span>
							<span class="booking-status" style="color: {statusColor(b.status)}">{b.status}</span>
							<span class="booking-who">{b.borrower.display_name}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if canBook}
			<div class="section-card">
				{#if showBookingForm}
					<h3>Request to Borrow</h3>
					{#if bookError}
						<p class="error">{bookError}</p>
					{/if}
					<form onsubmit={handleBooking} class="booking-form">
						<div class="form-row">
							<label>
								<span>Start Date</span>
								<input type="date" bind:value={bookStartDate} required />
							</label>
							<label>
								<span>End Date</span>
								<input type="date" bind:value={bookEndDate} required />
							</label>
						</div>
						<label>
							<span>Message (optional)</span>
							<textarea bind:value={bookMessage} rows="2" placeholder="Hi! I'd like to borrow this for..."></textarea>
						</label>
						<div class="form-actions">
							<button type="submit" class="btn-primary">Send Request</button>
							<button type="button" class="btn-secondary" onclick={() => (showBookingForm = false)}>Cancel</button>
						</div>
					</form>
				{:else}
					<button class="btn-primary" onclick={() => (showBookingForm = true)}>
						Request to Borrow
					</button>
				{/if}
			</div>
		{/if}
	</article>
{/if}

<style>
	.back-link {
		font-size: 0.9rem;
		color: var(--color-text-muted);
		text-decoration: none;
		display: inline-block;
		margin-bottom: 1rem;
	}

	.back-link:hover {
		color: var(--color-primary);
	}

	.resource-detail {
		max-width: 680px;
	}

	.detail-image {
		border-radius: var(--radius);
		overflow: hidden;
		margin-bottom: 1.5rem;
		max-height: 350px;
	}

	.detail-image img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.detail-header {
		margin-bottom: 1.5rem;
	}

	.detail-header h1 {
		font-size: 1.75rem;
		margin-top: 0.5rem;
	}

	.badges {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.category-badge, .condition-badge {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
		background: var(--color-bg);
		color: var(--color-primary);
		font-weight: 600;
	}

	.condition-badge {
		color: var(--color-text-muted);
	}

	.availability {
		font-size: 0.75rem;
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
		font-weight: 600;
	}

	.availability.available {
		background: #ecfdf5;
		color: #059669;
	}

	.availability:not(.available) {
		background: #fef2f2;
		color: #ef4444;
	}

	.section-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.25rem;
		margin-bottom: 1.25rem;
	}

	.section-card p {
		line-height: 1.7;
		white-space: pre-wrap;
	}

	.section-card h3 {
		font-size: 0.85rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
		margin-bottom: 0.75rem;
	}

	.owner-section {
		margin-bottom: 1rem;
	}

	.owner-section h3 {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
		margin-bottom: 0.25rem;
	}

	.owner-name {
		font-weight: 600;
	}

	.owner-neighbourhood {
		font-size: 0.9rem;
		color: var(--color-text-muted);
	}

	.meta {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-bottom: 1.25rem;
	}

	.owner-panel {
		background: var(--color-bg);
	}

	.owner-actions {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.btn-primary {
		padding: 0.5rem 1rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius);
		font-size: 0.9rem;
		cursor: pointer;
	}

	.btn-primary:hover {
		background: var(--color-primary-hover);
	}

	.btn-secondary, .upload-btn {
		padding: 0.5rem 1rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		background: var(--color-surface);
		color: var(--color-text);
		cursor: pointer;
		font-size: 0.9rem;
	}

	.btn-secondary:hover, .upload-btn:hover {
		border-color: var(--color-primary);
	}

	.btn-danger {
		padding: 0.5rem 1rem;
		border: 1px solid #fca5a5;
		border-radius: var(--radius);
		background: #fef2f2;
		color: #ef4444;
		cursor: pointer;
		font-size: 0.9rem;
	}

	.btn-danger:hover {
		background: #fee2e2;
	}

	/* Booking list */
	.booking-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.booking-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		font-size: 0.85rem;
		padding: 0.5rem 0;
		border-bottom: 1px solid var(--color-border);
	}

	.booking-item:last-child {
		border-bottom: none;
	}

	.booking-dates {
		font-weight: 500;
	}

	.booking-status {
		font-weight: 600;
		text-transform: capitalize;
	}

	.booking-who {
		color: var(--color-text-muted);
		margin-left: auto;
	}

	/* Booking form */
	.booking-form {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	label span {
		font-size: 0.85rem;
		font-weight: 500;
	}

	input, textarea {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.9rem;
		background: var(--color-surface);
		color: var(--color-text);
	}

	.form-actions {
		display: flex;
		gap: 0.75rem;
	}

	.error {
		color: #ef4444;
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}

	.loading {
		color: var(--color-text-muted);
	}

	.error-page {
		text-align: center;
		padding: 3rem 1rem;
	}

	.error-page h1 {
		color: #ef4444;
	}
</style>
