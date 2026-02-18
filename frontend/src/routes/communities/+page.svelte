<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { isLoggedIn } from '$lib/stores/auth';

	interface CommunityOut {
		id: number;
		name: string;
		description: string | null;
		postal_code: string;
		city: string;
		member_count: number;
		is_active: boolean;
		merged_into_id: number | null;
	}

	let communities = $state<CommunityOut[]>([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		if (!$isLoggedIn) {
			loading = false;
			return;
		}
		try {
			communities = await api<CommunityOut[]>('/communities/my/memberships', { auth: true });
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	});
</script>

<div class="communities-page">
	<div class="page-header">
		<h1>My Communities</h1>
		<a href="/onboarding" class="btn-find">Find or Create</a>
	</div>

	{#if error}
		<div class="alert alert-error fade-in">{error}</div>
	{/if}

	{#if loading}
		<p class="loading-text">Loading...</p>
	{:else if !$isLoggedIn}
		<div class="empty-state fade-in">
			<p>Please <a href="/login">log in</a> to view your communities.</p>
		</div>
	{:else if communities.length === 0}
		<div class="empty-state fade-in">
			<h2>No communities yet</h2>
			<p>Join or create a community to connect with your neighbours.</p>
			<a href="/onboarding" class="btn-primary">Find a Community</a>
		</div>
	{:else}
		<div class="community-grid">
			{#each communities as c (c.id)}
				<a href="/communities/{c.id}" class="community-card slide-up">
					<div class="card-header">
						<h3>{c.name}</h3>
						{#if !c.is_active}
							<span class="badge-inactive">Merged</span>
						{/if}
					</div>
					<div class="card-meta">
						<span class="tag">{c.postal_code}</span>
						<span class="tag">{c.city}</span>
					</div>
					{#if c.description}
						<p class="card-desc">{c.description}</p>
					{/if}
					<div class="card-footer">
						<span class="member-count">{c.member_count} member{c.member_count !== 1 ? 's' : ''}</span>
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>

<style>
	.communities-page {
		max-width: 700px;
		margin: 0 auto;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}

	.page-header h1 {
		font-size: 1.75rem;
		font-weight: 700;
		letter-spacing: -0.02em;
	}

	.btn-find {
		padding: 0.5rem 1rem;
		background: var(--color-primary);
		color: white;
		border-radius: var(--radius);
		font-size: 0.88rem;
		font-weight: 600;
		text-decoration: none;
		transition: all var(--transition-fast);
	}

	.btn-find:hover {
		background: var(--color-primary-hover);
		text-decoration: none;
		box-shadow: var(--shadow);
		transform: translateY(-1px);
	}

	.community-grid {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.community-card {
		display: block;
		padding: 1.25rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		text-decoration: none;
		color: var(--color-text);
		transition: all var(--transition-fast);
	}

	.community-card:hover {
		border-color: var(--color-primary);
		box-shadow: var(--shadow-md);
		transform: translateY(-2px);
		text-decoration: none;
	}

	.card-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.4rem;
	}

	.card-header h3 {
		font-size: 1.05rem;
		font-weight: 600;
	}

	.badge-inactive {
		font-size: 0.7rem;
		padding: 0.1rem 0.45rem;
		border-radius: 999px;
		background: var(--color-text-muted);
		color: white;
		font-weight: 600;
	}

	.card-meta {
		display: flex;
		gap: 0.4rem;
		margin-bottom: 0.35rem;
	}

	.tag {
		font-size: 0.72rem;
		font-weight: 500;
		padding: 0.12rem 0.45rem;
		border-radius: 999px;
		background: var(--color-primary-light);
		color: var(--color-primary);
	}

	.card-desc {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		line-height: 1.5;
		margin-bottom: 0.35rem;
	}

	.card-footer {
		margin-top: 0.35rem;
	}

	.member-count {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.empty-state {
		text-align: center;
		padding: 3rem 1rem;
		background: var(--color-surface);
		border: 1px dashed var(--color-border);
		border-radius: var(--radius-lg);
	}

	.empty-state h2 {
		font-size: 1.25rem;
		margin-bottom: 0.5rem;
	}

	.empty-state p {
		color: var(--color-text-muted);
		margin-bottom: 1rem;
	}

	.btn-primary {
		display: inline-block;
		padding: 0.5rem 1.25rem;
		background: var(--color-primary);
		color: white;
		border-radius: var(--radius);
		font-size: 0.9rem;
		font-weight: 600;
		text-decoration: none;
		transition: all var(--transition-fast);
	}

	.btn-primary:hover {
		background: var(--color-primary-hover);
		text-decoration: none;
	}

	.loading-text {
		text-align: center;
		color: var(--color-text-muted);
		padding: 2rem;
	}

	.alert {
		padding: 0.65rem 1rem;
		border-radius: var(--radius);
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}

	.alert-error {
		background: var(--color-error-bg);
		color: var(--color-error);
		border: 1px solid var(--color-error);
	}
</style>
