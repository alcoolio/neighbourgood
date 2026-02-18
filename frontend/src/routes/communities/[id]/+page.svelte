<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { isLoggedIn, user } from '$lib/stores/auth';

	interface UserProfile {
		id: number;
		display_name: string;
		email: string;
	}

	interface CommunityOut {
		id: number;
		name: string;
		description: string | null;
		postal_code: string;
		city: string;
		country_code: string;
		member_count: number;
		is_active: boolean;
		merged_into_id: number | null;
		created_by: UserProfile;
		created_at: string;
	}

	interface MemberOut {
		id: number;
		user: UserProfile;
		role: string;
		joined_at: string;
	}

	interface MergeSuggestion {
		source: CommunityOut;
		target: CommunityOut;
		reason: string;
	}

	let community = $state<CommunityOut | null>(null);
	let members = $state<MemberOut[]>([]);
	let suggestions = $state<MergeSuggestion[]>([]);
	let loading = $state(true);
	let error = $state('');
	let actionMsg = $state('');
	let isAdmin = $state(false);
	let isMember = $state(false);
	let joiningOrLeaving = $state(false);
	let merging = $state<number | null>(null);

	const communityId = $derived(Number($page.params.id));

	onMount(() => loadData());

	async function loadData() {
		loading = true;
		error = '';
		try {
			community = await api<CommunityOut>(`/communities/${communityId}`);
			members = await api<MemberOut[]>(`/communities/${communityId}/members`);

			if ($isLoggedIn && $user) {
				const me = members.find((m) => m.user.id === $user!.id);
				isMember = !!me;
				isAdmin = me?.role === 'admin';

				if (isAdmin) {
					suggestions = await api<MergeSuggestion[]>(
						`/communities/merge/suggestions?community_id=${communityId}`,
						{ auth: true }
					);
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load';
		} finally {
			loading = false;
		}
	}

	async function join() {
		joiningOrLeaving = true;
		error = '';
		try {
			await api(`/communities/${communityId}/join`, { method: 'POST', auth: true });
			actionMsg = 'Joined!';
			await loadData();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not join';
		} finally {
			joiningOrLeaving = false;
		}
	}

	async function leave() {
		joiningOrLeaving = true;
		error = '';
		try {
			await api(`/communities/${communityId}/leave`, { method: 'DELETE', auth: true });
			actionMsg = 'You left this community.';
			await loadData();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not leave';
		} finally {
			joiningOrLeaving = false;
		}
	}

	async function merge(targetId: number) {
		merging = targetId;
		error = '';
		try {
			await api('/communities/merge', {
				method: 'POST',
				auth: true,
				body: { source_id: communityId, target_id: targetId },
			});
			actionMsg = 'Communities merged! Redirecting...';
			setTimeout(() => goto(`/communities/${targetId}`), 1200);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Merge failed';
		} finally {
			merging = null;
		}
	}
</script>

<div class="detail-page">
	{#if loading}
		<p class="loading-text">Loading...</p>
	{:else if error && !community}
		<div class="alert alert-error">{error}</div>
	{:else if community}
		<div class="community-header slide-up">
			<div class="header-top">
				<a href="/communities" class="back-link">&#8592; Communities</a>
				{#if !community.is_active}
					<span class="badge-merged">Merged</span>
				{/if}
			</div>

			<h1>{community.name}</h1>
			<div class="header-meta">
				<span class="tag">{community.postal_code}</span>
				<span class="tag">{community.city}</span>
				<span class="meta-sep">&middot;</span>
				<span>{community.member_count} member{community.member_count !== 1 ? 's' : ''}</span>
				<span class="meta-sep">&middot;</span>
				<span>Created {new Date(community.created_at).toLocaleDateString()}</span>
			</div>

			{#if community.description}
				<p class="description">{community.description}</p>
			{/if}

			{#if community.merged_into_id}
				<div class="alert alert-info fade-in">
					This community has been merged into <a href="/communities/{community.merged_into_id}">another community</a>.
				</div>
			{/if}

			{#if error}
				<div class="alert alert-error fade-in">{error}</div>
			{/if}
			{#if actionMsg}
				<div class="alert alert-success fade-in">{actionMsg}</div>
			{/if}

			{#if $isLoggedIn && community.is_active}
				<div class="actions">
					{#if isMember}
						<button class="btn-secondary" onclick={leave} disabled={joiningOrLeaving}>
							{joiningOrLeaving ? 'Leaving...' : 'Leave Community'}
						</button>
					{:else}
						<button class="btn-primary" onclick={join} disabled={joiningOrLeaving}>
							{joiningOrLeaving ? 'Joining...' : 'Join Community'}
						</button>
					{/if}
				</div>
			{/if}
		</div>

		<section class="members-section slide-up" style="animation-delay: 0.05s">
			<h2>Members</h2>
			<div class="members-list">
				{#each members as m (m.id)}
					<div class="member-row">
						<div class="member-info">
							<span class="member-name">{m.user.display_name}</span>
							{#if m.role === 'admin'}
								<span class="role-badge">Admin</span>
							{/if}
						</div>
						<span class="member-date">Joined {new Date(m.joined_at).toLocaleDateString()}</span>
					</div>
				{/each}
			</div>
		</section>

		{#if isAdmin && suggestions.length > 0}
			<section class="merge-section slide-up" style="animation-delay: 0.1s">
				<h2>Merge Suggestions</h2>
				<p class="section-hint">These communities share your postal code or city. Merging combines members into one group.</p>
				<div class="suggestions-list">
					{#each suggestions as s (s.target.id)}
						<div class="suggestion-card">
							<div class="suggestion-info">
								<h3>{s.target.name}</h3>
								<div class="suggestion-meta">
									<span class="tag">{s.target.postal_code}</span>
									<span class="tag">{s.target.city}</span>
									<span class="member-count">{s.target.member_count} members</span>
								</div>
								<p class="suggestion-reason">{s.reason}</p>
							</div>
							<button
								class="btn-merge"
								onclick={() => merge(s.target.id)}
								disabled={merging === s.target.id}
							>
								{merging === s.target.id ? 'Merging...' : 'Merge into this'}
							</button>
						</div>
					{/each}
				</div>
			</section>
		{/if}
	{/if}
</div>

<style>
	.detail-page {
		max-width: 700px;
		margin: 0 auto;
	}

	.loading-text {
		text-align: center;
		color: var(--color-text-muted);
		padding: 3rem;
	}

	.back-link {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		text-decoration: none;
		transition: color var(--transition-fast);
	}

	.back-link:hover {
		color: var(--color-primary);
	}

	.header-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.75rem;
	}

	.community-header h1 {
		font-size: 2rem;
		font-weight: 700;
		letter-spacing: -0.02em;
		margin-bottom: 0.5rem;
	}

	.header-meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-bottom: 0.75rem;
	}

	.meta-sep {
		color: var(--color-border);
	}

	.tag {
		font-size: 0.72rem;
		font-weight: 500;
		padding: 0.12rem 0.45rem;
		border-radius: 999px;
		background: var(--color-primary-light);
		color: var(--color-primary);
	}

	.description {
		font-size: 0.95rem;
		color: var(--color-text-muted);
		line-height: 1.6;
		margin-bottom: 1rem;
	}

	.badge-merged {
		font-size: 0.72rem;
		padding: 0.15rem 0.6rem;
		border-radius: 999px;
		background: var(--color-text-muted);
		color: white;
		font-weight: 600;
	}

	.actions {
		margin-top: 1rem;
		margin-bottom: 0.5rem;
	}

	.btn-primary {
		padding: 0.55rem 1.25rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius);
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-primary-hover);
		box-shadow: var(--shadow);
	}

	.btn-primary:disabled,
	.btn-secondary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-secondary {
		padding: 0.55rem 1.25rem;
		background: var(--color-surface);
		color: var(--color-text-muted);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-secondary:hover:not(:disabled) {
		border-color: var(--color-error);
		color: var(--color-error);
	}

	.members-section,
	.merge-section {
		margin-top: 2rem;
	}

	.members-section h2,
	.merge-section h2 {
		font-size: 1.15rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
	}

	.section-hint {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-bottom: 0.75rem;
	}

	.members-list {
		display: flex;
		flex-direction: column;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.member-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--color-border);
		background: var(--color-surface);
	}

	.member-row:last-child {
		border-bottom: none;
	}

	.member-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.member-name {
		font-weight: 500;
		font-size: 0.92rem;
	}

	.role-badge {
		font-size: 0.68rem;
		font-weight: 600;
		padding: 0.1rem 0.4rem;
		border-radius: 999px;
		background: var(--color-primary-light);
		color: var(--color-primary);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.member-date {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.suggestions-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.suggestion-card {
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

	.suggestion-card:hover {
		border-color: var(--color-border-hover);
		box-shadow: var(--shadow-md);
	}

	.suggestion-info h3 {
		font-size: 0.95rem;
		font-weight: 600;
		margin-bottom: 0.3rem;
	}

	.suggestion-meta {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		flex-wrap: wrap;
	}

	.member-count {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.suggestion-reason {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		margin-top: 0.25rem;
		font-style: italic;
	}

	.btn-merge {
		padding: 0.45rem 1rem;
		background: var(--color-accent);
		color: white;
		border: none;
		border-radius: var(--radius);
		font-size: 0.82rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
		white-space: nowrap;
		flex-shrink: 0;
	}

	.btn-merge:hover:not(:disabled) {
		filter: brightness(1.1);
		box-shadow: var(--shadow);
	}

	.btn-merge:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.alert {
		padding: 0.65rem 1rem;
		border-radius: var(--radius);
		font-size: 0.9rem;
		margin-bottom: 1rem;
		margin-top: 0.75rem;
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

	.alert-info {
		background: var(--color-primary-light);
		color: var(--color-primary);
		border: 1px solid var(--color-primary);
	}

	.alert-info a {
		color: inherit;
		font-weight: 600;
	}
</style>
