<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';
	import { isLoggedIn, user } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	interface Resource {
		id: number;
		title: string;
		description: string | null;
		category: string;
		condition: string | null;
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

	let resource: Resource | null = $state(null);
	let error = $state('');
	let loading = $state(true);

	const isOwner = $derived(
		$isLoggedIn && resource !== null && $user?.id === resource.owner_id
	);

	onMount(async () => {
		const id = $page.params.id;
		try {
			resource = await api<Resource>(`/resources/${id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Resource not found';
		} finally {
			loading = false;
		}
	});

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
		<a href="/resources" class="back-link">← Back to resources</a>

		<div class="detail-header">
			<div>
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
			<div class="description-section">
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

		{#if isOwner}
			<div class="owner-actions">
				<button class="btn-secondary" onclick={toggleAvailability}>
					{resource.is_available ? 'Mark Unavailable' : 'Mark Available'}
				</button>
				<button class="btn-danger" onclick={deleteResource}>Delete</button>
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
		max-width: 640px;
	}

	.detail-header {
		margin-bottom: 1.5rem;
	}

	.detail-header h1 {
		font-size: 1.75rem;
		margin-top: 0.5rem;
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
		margin-right: 0.5rem;
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

	.description-section {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.25rem;
		margin-bottom: 1.5rem;
	}

	.description-section p {
		line-height: 1.7;
		white-space: pre-wrap;
	}

	.owner-section {
		margin-bottom: 1.5rem;
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
		margin-bottom: 1.5rem;
	}

	.owner-actions {
		display: flex;
		gap: 0.75rem;
	}

	.btn-secondary {
		padding: 0.5rem 1rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		background: var(--color-surface);
		color: var(--color-text);
		cursor: pointer;
		font-size: 0.9rem;
	}

	.btn-secondary:hover {
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
