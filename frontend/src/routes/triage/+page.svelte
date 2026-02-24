<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isLoggedIn, user } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import type { CommunityOut, EmergencyTicket } from '$lib/types';

	let communities: CommunityOut[] = $state([]);
	let selectedCommunityId: number | null = $state(null);
	let tickets: EmergencyTicket[] = $state([]);
	let loading = $state(false);
	let loadingCommunities = $state(true);
	let error = $state('');
	let filterUrgency = $state('');
	let filterStatus = $state('');

	const URGENCY_ORDER = ['critical', 'high', 'medium', 'low'];

	function urgencyColor(urgency: string): string {
		switch (urgency) {
			case 'critical': return 'var(--color-error)';
			case 'high':     return 'var(--color-warning)';
			case 'medium':   return 'var(--color-primary)';
			default:         return 'var(--color-text-muted)';
		}
	}

	function statusColor(status: string): string {
		switch (status) {
			case 'open':        return 'var(--color-warning)';
			case 'in_progress': return 'var(--color-primary)';
			case 'resolved':    return 'var(--color-success)';
			default:            return 'var(--color-text-muted)';
		}
	}

	function formatDue(due_at: string | null): string {
		if (!due_at) return '';
		const d = new Date(due_at);
		const now = new Date();
		const overdue = d < now;
		const diff = Math.abs(d.getTime() - now.getTime());
		const hrs = Math.floor(diff / 3_600_000);
		const mins = Math.floor((diff % 3_600_000) / 60_000);
		const label = hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`;
		return overdue ? `OVERDUE by ${label}` : `Due in ${label}`;
	}

	function isOverdue(due_at: string | null): boolean {
		return due_at !== null && new Date(due_at) < new Date();
	}

	async function loadCommunities() {
		loadingCommunities = true;
		try {
			const data = await api<{ items: CommunityOut[] }>('/communities/mine', { auth: true });
			communities = data.items ?? [];
			if (communities.length > 0) {
				selectedCommunityId = communities[0].id;
				await loadTriage();
			}
		} catch {
			error = 'Failed to load your communities.';
		} finally {
			loadingCommunities = false;
		}
	}

	async function loadTriage() {
		if (!selectedCommunityId) return;
		loading = true;
		error = '';
		tickets = [];
		try {
			const data = await api<{ items: EmergencyTicket[]; total: number }>(
				`/communities/${selectedCommunityId}/tickets/triage`,
				{ auth: true }
			);
			tickets = data.items ?? [];
		} catch (e: unknown) {
			const msg = e instanceof Error ? e.message : String(e);
			if (msg.includes('403')) {
				error = 'Only community leaders and admins can view the triage dashboard.';
			} else {
				error = 'Failed to load triage data.';
			}
		} finally {
			loading = false;
		}
	}

	async function onCommunityChange() {
		await loadTriage();
	}

	let filtered = $derived(
		tickets.filter((t) => {
			if (filterUrgency && t.urgency !== filterUrgency) return false;
			if (filterStatus && t.status !== filterStatus) return false;
			return true;
		})
	);

	onMount(async () => {
		if (!$isLoggedIn) {
			goto('/login');
			return;
		}
		await loadCommunities();
	});
</script>

<svelte:head>
	<title>Triage Dashboard – NeighbourGood</title>
</svelte:head>

<div class="triage-page">
	<div class="page-header">
		<div>
			<h1>Triage Dashboard</h1>
			<p class="subtitle">Open tickets sorted by priority score. Highest urgency and oldest age appear first.</p>
		</div>
	</div>

	{#if loadingCommunities}
		<p class="loading-text">Loading communities…</p>
	{:else if communities.length === 0}
		<div class="empty-state">
			<p>You are not a member of any community yet.</p>
			<a href="/communities" class="btn-primary">Find a community</a>
		</div>
	{:else}
		<div class="controls">
			<div class="control-group">
				<label for="community-select">Community</label>
				<select id="community-select" bind:value={selectedCommunityId} onchange={onCommunityChange}>
					{#each communities as c}
						<option value={c.id}>{c.name}</option>
					{/each}
				</select>
			</div>

			<div class="control-group">
				<label for="urgency-filter">Urgency</label>
				<select id="urgency-filter" bind:value={filterUrgency}>
					<option value="">All</option>
					{#each URGENCY_ORDER as u}
						<option value={u}>{u.charAt(0).toUpperCase() + u.slice(1)}</option>
					{/each}
				</select>
			</div>

			<div class="control-group">
				<label for="status-filter">Status</label>
				<select id="status-filter" bind:value={filterStatus}>
					<option value="">All open</option>
					<option value="open">Open</option>
					<option value="in_progress">In progress</option>
				</select>
			</div>
		</div>

		{#if error}
			<div class="alert alert-error">{error}</div>
		{:else if loading}
			<p class="loading-text">Loading tickets…</p>
		{:else if filtered.length === 0}
			<div class="empty-state">
				<p>{tickets.length === 0 ? 'No open tickets in this community.' : 'No tickets match the current filters.'}</p>
			</div>
		{:else}
			<p class="count-label">{filtered.length} ticket{filtered.length !== 1 ? 's' : ''}</p>
			<div class="ticket-list">
				{#each filtered as ticket (ticket.id)}
					<div class="ticket-card" class:overdue={isOverdue(ticket.due_at)}>
						<div class="ticket-header">
							<span class="urgency-badge" style="background: {urgencyColor(ticket.urgency)}20; color: {urgencyColor(ticket.urgency)}; border-color: {urgencyColor(ticket.urgency)}40">
								{ticket.urgency.toUpperCase()}
							</span>
							<span class="score-badge" title="Triage score">
								Score {ticket.triage_score}
							</span>
							<span class="status-chip" style="color: {statusColor(ticket.status)}">
								{ticket.status.replace('_', ' ')}
							</span>
							<span class="ticket-type">{ticket.ticket_type.replace('_', ' ')}</span>
						</div>

						<h3 class="ticket-title">{ticket.title}</h3>

						{#if ticket.description}
							<p class="ticket-desc">{ticket.description}</p>
						{/if}

						<div class="ticket-meta">
							<span>By {ticket.author.display_name}</span>
							{#if ticket.assigned_to}
								<span class="assigned">→ {ticket.assigned_to.display_name}</span>
							{:else}
								<span class="unassigned">Unassigned</span>
							{/if}
							{#if ticket.due_at}
								<span class="due" class:overdue-text={isOverdue(ticket.due_at)}>
									{formatDue(ticket.due_at)}
								</span>
							{/if}
							<span class="created">#{ticket.id}</span>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.triage-page {
		max-width: 820px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: 1.5rem;
	}

	h1 {
		font-size: 1.6rem;
		font-weight: 700;
		letter-spacing: -0.02em;
		color: var(--color-text);
		margin-bottom: 0.25rem;
	}

	.subtitle {
		color: var(--color-text-muted);
		font-size: 0.9rem;
	}

	.controls {
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
		margin-bottom: 1.25rem;
		padding: 1rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
	}

	.control-group {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		min-width: 160px;
	}

	.control-group label {
		font-size: 0.78rem;
		font-weight: 600;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.control-group select {
		background: var(--color-bg);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		padding: 0.4rem 0.6rem;
		font-size: 0.9rem;
		color: var(--color-text);
		cursor: pointer;
	}

	.count-label {
		font-size: 0.82rem;
		color: var(--color-text-muted);
		margin-bottom: 0.75rem;
	}

	.ticket-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.ticket-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1rem 1.25rem;
		transition: border-color var(--transition-fast);
	}

	.ticket-card:hover {
		border-color: var(--color-border-hover);
	}

	.ticket-card.overdue {
		border-left: 3px solid var(--color-error);
	}

	.ticket-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-bottom: 0.5rem;
	}

	.urgency-badge {
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.06em;
		padding: 0.2rem 0.5rem;
		border-radius: var(--radius-sm);
		border: 1px solid;
	}

	.score-badge {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--color-text-subtle);
		background: var(--color-bg);
		padding: 0.2rem 0.5rem;
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
	}

	.status-chip {
		font-size: 0.78rem;
		font-weight: 500;
		text-transform: capitalize;
	}

	.ticket-type {
		font-size: 0.75rem;
		color: var(--color-text-subtle);
		margin-left: auto;
		text-transform: capitalize;
	}

	.ticket-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-text);
		margin-bottom: 0.35rem;
		line-height: 1.3;
	}

	.ticket-desc {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-bottom: 0.6rem;
		white-space: pre-line;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.ticket-meta {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.78rem;
		color: var(--color-text-muted);
	}

	.assigned {
		color: var(--color-accent);
	}

	.unassigned {
		font-style: italic;
		color: var(--color-text-subtle);
	}

	.due {
		font-weight: 600;
		color: var(--color-warning);
	}

	.due.overdue-text {
		color: var(--color-error);
	}

	.created {
		margin-left: auto;
		color: var(--color-text-subtle);
	}

	.btn-primary {
		display: inline-block;
		background: var(--color-primary);
		color: white;
		padding: 0.5rem 1.2rem;
		border-radius: var(--radius-sm);
		font-weight: 600;
		font-size: 0.9rem;
		text-decoration: none;
		margin-top: 0.5rem;
	}

	.btn-primary:hover {
		background: var(--color-primary-hover);
		text-decoration: none;
	}

	@media (max-width: 600px) {
		.controls {
			flex-direction: column;
		}
		.control-group {
			min-width: unset;
			width: 100%;
		}
	}
</style>
