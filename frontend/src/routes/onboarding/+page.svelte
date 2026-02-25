<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { isLoggedIn } from '$lib/stores/auth';
	import { onMount } from 'svelte';

	interface CommunityOut {
		id: number;
		name: string;
		description: string | null;
		postal_code: string;
		city: string;
		member_count: number;
		is_active: boolean;
	}

	let query = $state('');
	let results = $state<CommunityOut[]>([]);
	let total = $state(0);
	let searching = $state(false);
	let searched = $state(false);
	let joining = $state<number | null>(null);
	let error = $state('');
	let successMsg = $state('');

	// Create form
	let showCreate = $state(false);
	let newName = $state('');
	let newPlz = $state('');
	let newCity = $state('');
	let newDesc = $state('');
	let creating = $state(false);

	onMount(() => {
		if (!$isLoggedIn) goto('/login');
	});

	async function search() {
		if (!query.trim()) return;
		searching = true;
		error = '';
		successMsg = '';
		try {
			const param = query.trim();
			// Try to detect if it's a PLZ (digits only) or city/name
			const isPlz = /^\d{3,5}$/.test(param);
			const qs = isPlz ? `postal_code=${param}` : `q=${encodeURIComponent(param)}`;
			const res = await api<{ items: CommunityOut[]; total: number }>(
				`/communities/search?${qs}`
			);
			results = res.items;
			total = res.total;
			searched = true;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Search failed';
		} finally {
			searching = false;
		}
	}

	async function joinCommunity(id: number) {
		joining = id;
		error = '';
		try {
			await api(`/communities/${id}/join`, { method: 'POST', auth: true });
			successMsg = 'You joined the community!';
			setTimeout(() => goto(`/communities/${id}`), 1200);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not join';
		} finally {
			joining = null;
		}
	}

	async function createCommunity() {
		if (!newName.trim() || !newPlz.trim() || !newCity.trim()) return;
		creating = true;
		error = '';
		try {
			const created = await api<CommunityOut>('/communities', {
				method: 'POST',
				auth: true,
				body: {
					name: newName.trim(),
					postal_code: newPlz.trim(),
					city: newCity.trim(),
					description: newDesc.trim() || null,
				},
			});
			successMsg = `"${created.name}" created! Redirecting...`;
			setTimeout(() => goto(`/communities/${created.id}`), 1200);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not create community';
		} finally {
			creating = false;
		}
	}
</script>

<div class="onboarding slide-up">
	<div class="onboarding-header">
		<div class="step-badge">Step 1 of 1</div>
		<h1>Find your community</h1>
		<p class="subtitle">
			Search by city, neighbourhood name, or postal code to find an existing group — or create a new one.
		</p>
	</div>

	{#if error}
		<div class="alert alert-error fade-in">{error}</div>
	{/if}
	{#if successMsg}
		<div class="alert alert-success fade-in">{successMsg}</div>
	{/if}

	<form class="search-form" onsubmit={(e) => { e.preventDefault(); search(); }}>
		<div class="search-input-group">
			<input
				type="text"
				bind:value={query}
				placeholder="e.g. Kreuzberg, 10999, Berlin..."
				class="search-input"
			/>
			<button type="submit" class="btn-search" disabled={searching || !query.trim()}>
				{searching ? 'Searching...' : 'Search'}
			</button>
		</div>
	</form>

	{#if searched}
		<div class="results-section fade-in">
			{#if results.length > 0}
				<p class="results-count">{total} communit{total === 1 ? 'y' : 'ies'} found</p>
				<div class="results-list">
					{#each results as community (community.id)}
						<div class="community-card slide-up">
							<div class="card-info">
								<h3>{community.name}</h3>
								<div class="card-meta">
									<span class="tag">{community.postal_code}</span>
									<span class="tag">{community.city}</span>
									<span class="member-count">{community.member_count} member{community.member_count !== 1 ? 's' : ''}</span>
								</div>
								{#if community.description}
									<p class="card-desc">{community.description}</p>
								{/if}
							</div>
							<button
								class="btn-join"
								onclick={() => joinCommunity(community.id)}
								disabled={joining === community.id}
							>
								{joining === community.id ? 'Joining...' : 'Join'}
							</button>
						</div>
					{/each}
				</div>
			{:else}
				<div class="no-results">
					<p>No communities found for "{query}".</p>
					<p class="hint">Be the first to create one for your area!</p>
				</div>
			{/if}
		</div>
	{/if}

	<div class="divider">
		<span>or</span>
	</div>

	{#if !showCreate}
		<button class="btn-create-toggle" onclick={() => (showCreate = true)}>
			Create a new community
		</button>
	{:else}
		<div class="create-form fade-in">
			<h2>Create a new community</h2>
			<form onsubmit={(e) => { e.preventDefault(); createCommunity(); }}>
				<label>
					<span>Community Name</span>
					<input type="text" bind:value={newName} required placeholder="e.g. Nachbarschaft Kreuzberg" />
				</label>
				<div class="form-row">
					<label class="flex-1">
						<span>Postal Code</span>
						<input type="text" bind:value={newPlz} required placeholder="e.g. 10999" />
					</label>
					<label class="flex-2">
						<span>City</span>
						<input type="text" bind:value={newCity} required placeholder="e.g. Berlin" />
					</label>
				</div>
				<label>
					<span>Description (optional)</span>
					<textarea bind:value={newDesc} rows="3" placeholder="What's this community about?"></textarea>
				</label>
				<div class="form-actions">
					<button type="button" class="btn-cancel" onclick={() => (showCreate = false)}>Cancel</button>
					<button type="submit" class="btn-primary" disabled={creating || !newName.trim() || !newPlz.trim() || !newCity.trim()}>
						{creating ? 'Creating...' : 'Create Community'}
					</button>
				</div>
			</form>
		</div>
	{/if}

	<div class="skip-section">
		<a href="/dashboard" class="skip-link">Skip for now</a>
	</div>
</div>

<style>
	.onboarding {
		max-width: 600px;
		margin: 0 auto;
	}

	.onboarding-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.step-badge {
		display: inline-block;
		font-size: 0.72rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--color-primary);
		background: var(--color-primary-light);
		padding: 0.25rem 0.75rem;
		border-radius: 999px;
		margin-bottom: 1rem;
	}

	.onboarding-header h1 {
		font-size: 2rem;
		font-weight: 700;
		letter-spacing: -0.02em;
		margin-bottom: 0.5rem;
	}

	.subtitle {
		color: var(--color-text-muted);
		font-size: 1rem;
		line-height: 1.6;
	}

	.search-form {
		margin-bottom: 1.5rem;
	}

	.search-input-group {
		display: flex;
		gap: 0.5rem;
	}

	.search-input {
		flex: 1;
		padding: 0.65rem 1rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 1rem;
		background: var(--color-surface);
		color: var(--color-text);
		transition: border-color var(--transition-fast);
	}

	.search-input:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 3px var(--color-primary-light);
	}

	.btn-search {
		padding: 0.65rem 1.25rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius);
		font-size: 0.95rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
		white-space: nowrap;
	}

	.btn-search:hover:not(:disabled) {
		background: var(--color-primary-hover);
		box-shadow: var(--shadow-md);
	}

	.btn-search:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.results-section {
		margin-bottom: 1.5rem;
	}

	.results-count {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-bottom: 0.75rem;
	}

	.results-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.community-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 1rem 1.25rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		transition: all var(--transition-fast);
	}

	.community-card:hover {
		border-color: var(--color-border-hover);
		box-shadow: var(--shadow-md);
	}

	.card-info h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 0.35rem;
	}

	.card-meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.tag {
		font-size: 0.75rem;
		font-weight: 500;
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
		background: var(--color-primary-light);
		color: var(--color-primary);
	}

	.member-count {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.card-desc {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-top: 0.35rem;
		line-height: 1.5;
	}

	.btn-join {
		padding: 0.5rem 1.25rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius);
		font-size: 0.88rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
		white-space: nowrap;
		flex-shrink: 0;
	}

	.btn-join:hover:not(:disabled) {
		background: var(--color-primary-hover);
		transform: translateY(-1px);
		box-shadow: var(--shadow);
	}

	.btn-join:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.no-results {
		text-align: center;
		padding: 1.5rem;
		background: var(--color-surface);
		border: 1px dashed var(--color-border);
		border-radius: var(--radius-lg);
	}

	.no-results p {
		margin-bottom: 0.25rem;
	}

	.hint {
		color: var(--color-text-muted);
		font-size: 0.9rem;
	}

	.divider {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin: 1.5rem 0;
		color: var(--color-text-muted);
		font-size: 0.85rem;
	}

	.divider::before,
	.divider::after {
		content: '';
		flex: 1;
		height: 1px;
		background: var(--color-border);
	}

	.btn-create-toggle {
		width: 100%;
		padding: 0.75rem;
		background: var(--color-surface);
		color: var(--color-primary);
		border: 1px dashed var(--color-primary);
		border-radius: var(--radius);
		font-size: 0.95rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-create-toggle:hover {
		background: var(--color-primary-light);
	}

	.create-form {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
	}

	.create-form h2 {
		font-size: 1.15rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.create-form form {
		display: flex;
		flex-direction: column;
		gap: 0.85rem;
	}

	.create-form label {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.create-form label span {
		font-size: 0.82rem;
		font-weight: 500;
		color: var(--color-text-muted);
	}

	.create-form input,
	.create-form textarea {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.95rem;
		background: var(--color-bg);
		color: var(--color-text);
		font-family: inherit;
	}

	.create-form input:focus,
	.create-form textarea:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 3px var(--color-primary-light);
	}

	.form-row {
		display: flex;
		gap: 0.75rem;
	}

	.flex-1 { flex: 1; }
	.flex-2 { flex: 2; }

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.5rem;
		margin-top: 0.5rem;
	}

	.btn-cancel {
		padding: 0.5rem 1rem;
		background: none;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		color: var(--color-text-muted);
		font-size: 0.88rem;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-cancel:hover {
		border-color: var(--color-text-muted);
	}

	.btn-primary {
		padding: 0.5rem 1.25rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius);
		font-size: 0.88rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
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

	.alert-success {
		background: #ecfdf5;
		color: #065f46;
		border: 1px solid #a7f3d0;
	}

	:global([data-theme='dark']) .alert-success {
		background: #064e3b;
		color: #6ee7b7;
		border-color: #065f46;
	}

	.skip-section {
		text-align: center;
		margin-top: 2rem;
		padding-top: 1rem;
	}

	.skip-link {
		font-size: 0.88rem;
		color: var(--color-text-muted);
		text-decoration: none;
		transition: color var(--transition-fast);
	}

	.skip-link:hover {
		color: var(--color-primary);
	}
</style>
