<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isLoggedIn, user } from '$lib/stores/auth';
	import { api } from '$lib/api';
	import { isOnline, enqueueRequest } from '$lib/stores/offline';
	import { token } from '$lib/stores/auth';
	import { get } from 'svelte/store';
	import {
		meshStatus,
		meshDeviceName,
		meshMessages,
		meshPeerCount,
		meshIsSupported,
		connectToMesh,
		disconnectFromMesh,
		broadcastEmergencyTicket,
		clearMeshMessages,
		getMeshMessages
	} from '$lib/stores/mesh';
	import { isBluetoothSupported } from '$lib/bluetooth/connection';
	import type { CommunityOut, NGMeshMessage, MeshSyncResult } from '$lib/types';

	interface Ticket {
		id: number;
		community_id: number;
		author: { id: number; display_name: string };
		ticket_type: string;
		title: string;
		description: string;
		status: string;
		urgency: string;
		due_at: string | null;
		triage_score?: number;
		assigned_to: { id: number; display_name: string } | null;
		created_at: string;
		updated_at: string;
	}

	interface MemberInfo {
		user: { id: number };
		role: string;
	}

	let communities: CommunityOut[] = $state([]);
	let selectedCommunityId: number | null = $state(null);
	let tickets: Ticket[] = $state([]);
	let myRole: string = $state('member');
	let loading = $state(false);
	let loadingCommunities = $state(true);
	let error = $state('');
	let filterUrgency = $state('');
	let filterStatus = $state('');

	// New ticket form
	let showNewTicketForm = $state(false);
	let newTicketTitle = $state('');
	let newTicketDesc = $state('');
	let newTicketType = $state('request');
	let newTicketUrgency = $state('medium');
	let creatingTicket = $state(false);
	let selectedCommunityMode = $state('blue');

	let meshConnecting = $state(false);
	let meshError = $state('');
	let syncing = $state(false);

	// Filter mesh messages for the selected community
	let communityMeshTickets = $derived(
		$meshMessages.filter(
			(m) => m.type === 'emergency_ticket' && m.community_id === selectedCommunityId
		)
	);

	async function handleMeshConnect() {
		meshConnecting = true;
		meshError = '';
		try {
			await connectToMesh();
		} catch (e) {
			meshError = e instanceof Error ? e.message : 'Failed to connect to mesh';
		} finally {
			meshConnecting = false;
		}
	}

	async function handleMeshDisconnect() {
		disconnectFromMesh();
	}

	async function createTicketViaMesh() {
		if (!selectedCommunityId || !newTicketTitle.trim()) return;
		creatingTicket = true;
		error = '';
		try {
			const msg = await broadcastEmergencyTicket(
				selectedCommunityId,
				$user?.display_name ?? 'Unknown',
				{
					title: newTicketTitle,
					description: newTicketDesc,
					ticket_type: newTicketType as 'request' | 'offer' | 'emergency_ping',
					urgency: newTicketUrgency as 'low' | 'medium' | 'high' | 'critical'
				}
			);
			// Also enqueue for server sync when internet returns
			enqueueRequest(
				{
					method: 'POST',
					path: `/communities/${selectedCommunityId}/tickets`,
					body: {
						ticket_type: newTicketType,
						title: newTicketTitle,
						description: newTicketDesc,
						urgency: newTicketUrgency
					},
					authToken: get(token),
					label: `Emergency ticket: ${newTicketTitle}`
				},
				{ meshSent: true }
			);
			showNewTicketForm = false;
			newTicketTitle = '';
			newTicketDesc = '';
			newTicketType = 'request';
			newTicketUrgency = 'medium';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to broadcast ticket via mesh';
		} finally {
			creatingTicket = false;
		}
	}

	async function syncMeshMessages() {
		const msgs = getMeshMessages();
		if (msgs.length === 0) return;
		syncing = true;
		try {
			const result = await api<MeshSyncResult>('/mesh/sync', {
				method: 'POST',
				auth: true,
				body: { messages: msgs }
			});
			clearMeshMessages();
			await loadTickets();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to sync mesh messages';
		} finally {
			syncing = false;
		}
	}

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

	function isOverdue(due_at: string | null): boolean {
		return due_at !== null && new Date(due_at) < new Date();
	}

	async function loadCommunities() {
		loadingCommunities = true;
		try {
			const data = await api<CommunityOut[]>('/communities/my/memberships', { auth: true });
			communities = data ?? [];
			if (communities.length > 0) {
				selectedCommunityId = communities[0].id;
				selectedCommunityMode = communities[0].mode ?? 'blue';
				await loadTickets();
			}
		} catch {
			error = 'Failed to load your communities.';
		} finally {
			loadingCommunities = false;
		}
	}

	async function loadTickets() {
		if (!selectedCommunityId) return;
		loading = true;
		error = '';
		tickets = [];
		myRole = 'member';
		try {
			// Use the member-accessible tickets endpoint
			const data = await api<{ items: Ticket[]; total: number }>(
				`/communities/${selectedCommunityId}/tickets`,
				{ auth: true }
			);
			tickets = data.items ?? [];

			// Determine current user's role in this community
			try {
				const members = await api<MemberInfo[]>(
					`/communities/${selectedCommunityId}/members`
				);
				const me = members.find((m) => m.user.id === $user?.id);
				myRole = me?.role ?? 'member';
			} catch {
				myRole = 'member';
			}

			const selectedCommunity = communities.find(c => c.id === selectedCommunityId);
			selectedCommunityMode = selectedCommunity?.mode ?? 'blue';
		} catch {
			error = 'Failed to load tickets.';
		} finally {
			loading = false;
		}
	}

	async function onCommunityChange() {
		await loadTickets();
	}

	async function updateTicketStatus(ticketId: number, newStatus: string) {
		try {
			await api(`/communities/${selectedCommunityId}/tickets/${ticketId}`, {
				method: 'PATCH', auth: true, body: { status: newStatus }
			});
			await loadTickets();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to update ticket';
		}
	}

	async function createTicket() {
		if (!selectedCommunityId || !newTicketTitle.trim()) return;
		creatingTicket = true;
		error = '';
		try {
			await api(`/communities/${selectedCommunityId}/tickets`, {
				method: 'POST', auth: true,
				body: {
					ticket_type: newTicketType,
					title: newTicketTitle,
					description: newTicketDesc,
					urgency: newTicketUrgency
				}
			});
			showNewTicketForm = false;
			newTicketTitle = '';
			newTicketDesc = '';
			newTicketType = 'request';
			newTicketUrgency = 'medium';
			await loadTickets();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create ticket';
		} finally {
			creatingTicket = false;
		}
	}

	const isAdminOrLeader = $derived(myRole === 'admin' || myRole === 'leader');

	let filtered = $derived(
		tickets
			.filter((t) => {
				if (filterUrgency && t.urgency !== filterUrgency) return false;
				if (filterStatus === '') {
					return t.status !== 'resolved';
				}
				return t.status === filterStatus;
			})
			.sort((a, b) => {
				// Sort by urgency first, then by creation date
				const urgencyRank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
				const aRank = urgencyRank[a.urgency] ?? 4;
				const bRank = urgencyRank[b.urgency] ?? 4;
				if (aRank !== bRank) return aRank - bRank;
				return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
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
	<title>Emergency – NeighbourGood</title>
</svelte:head>

<div class="emergency-page">
	<div class="page-header">
		<div>
			<h1>Emergency</h1>
			<p class="subtitle">Community emergency tickets — requests, offers, and crisis coordination.</p>
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
						<option value={c.id}>{c.name}{c.mode === 'red' ? ' 🔴' : ''}</option>
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
					<option value="">Open (excl. resolved)</option>
					<option value="open">Open</option>
					<option value="in_progress">In progress</option>
					<option value="resolved">Resolved</option>
				</select>
			</div>

			<button class="btn-new-ticket" onclick={() => showNewTicketForm = !showNewTicketForm}>
				{showNewTicketForm ? 'Cancel' : '+ New Ticket'}
			</button>
		</div>

		{#if isBluetoothSupported() && selectedCommunityMode === 'red'}
			<div class="mesh-panel">
				<div class="mesh-header">
					<div class="mesh-status-row">
						<span class="mesh-dot" class:mesh-connected={$meshStatus === 'connected'} class:mesh-scanning={$meshStatus === 'scanning' || $meshStatus === 'connecting'}></span>
						<span class="mesh-label">
							{#if $meshStatus === 'connected'}
								Mesh: connected{$meshDeviceName ? ` to ${$meshDeviceName}` : ''}
							{:else if $meshStatus === 'scanning' || $meshStatus === 'connecting'}
								Mesh: {$meshStatus}...
							{:else}
								Mesh: offline
							{/if}
						</span>
						{#if $meshStatus === 'connected'}
							<span class="mesh-peers">{$meshPeerCount} peer{$meshPeerCount !== 1 ? 's' : ''}</span>
						{/if}
					</div>
					<div class="mesh-actions">
						{#if $meshStatus === 'disconnected'}
							<button class="btn-mesh" onclick={handleMeshConnect} disabled={meshConnecting}>
								{meshConnecting ? 'Connecting...' : 'Connect to Mesh'}
							</button>
						{:else if $meshStatus === 'connected'}
							<button class="btn-mesh btn-mesh-disconnect" onclick={handleMeshDisconnect}>Disconnect</button>
						{/if}
						{#if $isOnline && $meshMessages.length > 0}
							<button class="btn-mesh btn-mesh-sync" onclick={syncMeshMessages} disabled={syncing}>
								{syncing ? 'Syncing...' : `Sync ${$meshMessages.length} message${$meshMessages.length !== 1 ? 's' : ''}`}
							</button>
						{/if}
					</div>
				</div>
				{#if meshError}
					<p class="mesh-error">{meshError}</p>
				{/if}
			</div>
		{/if}

		{#if communityMeshTickets.length > 0}
			<div class="mesh-tickets-section">
				<h2>Mesh Tickets <span class="via-mesh-badge">via BLE mesh</span></h2>
				<div class="ticket-list">
					{#each communityMeshTickets as msg (msg.id)}
						<div class="ticket-card mesh-ticket-card">
							<div class="ticket-header">
								<span class="urgency-badge" style="background: {urgencyColor(String(msg.data.urgency ?? 'medium'))}20; color: {urgencyColor(String(msg.data.urgency ?? 'medium'))}; border-color: {urgencyColor(String(msg.data.urgency ?? 'medium'))}40">
									{String(msg.data.urgency ?? 'medium').toUpperCase()}
								</span>
								<span class="via-mesh-badge">mesh</span>
								<span class="ticket-type">{String(msg.data.ticket_type ?? 'request').replace('_', ' ')}</span>
							</div>
							<h3 class="ticket-title">{msg.data.title ?? 'Untitled'}</h3>
							{#if msg.data.description}
								<p class="ticket-desc">{msg.data.description}</p>
							{/if}
							<div class="ticket-meta">
								<span>By {msg.sender_name}</span>
								<span class="ticket-id">{new Date(msg.ts).toLocaleTimeString()}</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if showNewTicketForm}
			<div class="new-ticket-form">
				<h2>New Emergency Ticket</h2>
				<div class="form-row">
					<label>
						<span>Type</span>
						<select bind:value={newTicketType}>
							<option value="request">Request</option>
							<option value="offer">Offer</option>
							{#if selectedCommunityMode === 'red'}
								<option value="emergency_ping">Emergency Ping</option>
							{/if}
						</select>
					</label>
					<label>
						<span>Urgency</span>
						<select bind:value={newTicketUrgency}>
							<option value="low">Low</option>
							<option value="medium">Medium</option>
							<option value="high">High</option>
							<option value="critical">Critical</option>
						</select>
					</label>
				</div>
				<label>
					<span>Title</span>
					<input type="text" bind:value={newTicketTitle} placeholder="Short description..." maxlength="300" />
				</label>
				<label>
					<span>Description (optional)</span>
					<textarea bind:value={newTicketDesc} rows="3" placeholder="More details..." maxlength="5000"></textarea>
				</label>
				{#if !$isOnline && $meshStatus === 'connected'}
				<button class="btn-primary btn-mesh-send" onclick={createTicketViaMesh} disabled={creatingTicket || !newTicketTitle.trim()}>
					{creatingTicket ? 'Broadcasting...' : 'Broadcast via Mesh'}
				</button>
			{:else}
				<button class="btn-primary" onclick={createTicket} disabled={creatingTicket || !newTicketTitle.trim()}>
					{creatingTicket ? 'Creating...' : 'Create Ticket'}
				</button>
			{/if}
			</div>
		{/if}

		{#if error}
			<div class="alert alert-error">{error}</div>
		{:else if loading}
			<p class="loading-text">Loading tickets…</p>
		{:else if filtered.length === 0}
			<div class="empty-state">
				<p>{tickets.length === 0 ? 'No tickets in this community yet.' : 'No tickets match the current filters.'}</p>
			</div>
		{:else}
			<p class="count-label">{filtered.length} ticket{filtered.length !== 1 ? 's' : ''}</p>
			<div class="ticket-list">
				{#each filtered as ticket (ticket.id)}
					<a href="/triage/{ticket.id}?community={selectedCommunityId}" class="ticket-card" class:overdue={isOverdue(ticket.due_at)}>
						<div class="ticket-header">
							<span class="urgency-badge" style="background: {urgencyColor(ticket.urgency)}20; color: {urgencyColor(ticket.urgency)}; border-color: {urgencyColor(ticket.urgency)}40">
								{ticket.urgency.toUpperCase()}
							</span>
							{#if isAdminOrLeader && ticket.triage_score !== undefined}
								<span class="score-badge" title="Triage score">Score {ticket.triage_score}</span>
							{/if}
							<span class="status-chip" style="color: {statusColor(ticket.status)}">
								{ticket.status.replace('_', ' ')}
							</span>
							<span class="ticket-type">{ticket.ticket_type.replace('_', ' ')}</span>
						</div>

						<h3 class="ticket-title">{ticket.title}</h3>

						{#if ticket.description}
							<p class="ticket-desc">{ticket.description}</p>
						{/if}

						<div class="ticket-footer">
							<div class="ticket-meta">
								<span>By {ticket.author.display_name}</span>
								{#if ticket.assigned_to}
									<span class="assigned">→ {ticket.assigned_to.display_name}</span>
								{:else}
									<span class="unassigned">Unassigned</span>
								{/if}
								<span class="ticket-id">#{ticket.id}</span>
							</div>
							{#if ticket.status !== 'resolved' && (isAdminOrLeader || ticket.author.id === $user?.id)}
								<div class="ticket-actions">
									{#if ticket.status === 'open'}
										<button class="btn-tiny" onclick={(e) => { e.preventDefault(); e.stopPropagation(); updateTicketStatus(ticket.id, 'in_progress'); }}>Start</button>
									{/if}
									<button class="btn-tiny btn-tiny-success" onclick={(e) => { e.preventDefault(); e.stopPropagation(); updateTicketStatus(ticket.id, 'resolved'); }}>Resolve</button>
								</div>
							{/if}
						</div>
					</a>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.emergency-page {
		max-width: 900px;
	}

	.page-header {
		margin-bottom: 1.5rem;
	}

	h1 {
		font-size: 1.9rem;
		font-weight: 400;
		margin-bottom: 0.25rem;
	}

	h2 {
		font-size: 1.2rem;
		font-weight: 600;
		color: var(--color-text);
		margin: 0 0 1rem 0;
	}

	.subtitle {
		color: var(--color-text-muted);
		font-size: 0.9rem;
	}

	/* ── Controls bar ────────────────────────────────── */

	.controls {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		gap: 1rem;
		margin-bottom: 1.5rem;
		padding: 1rem 1.25rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
	}

	.control-group {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		flex: 1;
		min-width: 140px;
	}

	.control-group label {
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.control-group select {
		padding: 0.45rem 0.6rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.88rem;
		background: var(--color-bg);
		color: var(--color-text);
	}

	.btn-new-ticket {
		padding: 0.5rem 1.1rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 0.88rem;
		font-weight: 600;
		cursor: pointer;
		white-space: nowrap;
		transition: all var(--transition-fast);
		align-self: flex-end;
	}

	.btn-new-ticket:hover {
		background: var(--color-primary-hover);
	}

	/* ── New ticket form ─────────────────────────────── */

	.new-ticket-form {
		padding: 1.25rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		margin-bottom: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.85rem;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.new-ticket-form label {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}

	.new-ticket-form label span {
		font-size: 0.82rem;
		font-weight: 600;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.new-ticket-form input,
	.new-ticket-form select,
	.new-ticket-form textarea {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.9rem;
		background: var(--color-bg);
		color: var(--color-text);
	}

	.new-ticket-form input:focus,
	.new-ticket-form textarea:focus {
		outline: none;
		border-color: var(--color-primary);
	}

	.btn-primary {
		padding: 0.6rem 1.2rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: background var(--transition-fast);
		align-self: flex-start;
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* ── Ticket list ─────────────────────────────────── */

	.count-label {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-bottom: 0.75rem;
	}

	.ticket-list {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.ticket-card {
		display: block;
		padding: 1rem 1.25rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		border-left: 4px solid transparent;
		transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
		text-decoration: none;
		color: inherit;
		cursor: pointer;
	}

	.ticket-card:hover {
		box-shadow: var(--shadow-sm);
	}

	.ticket-card.overdue {
		border-left-color: var(--color-error);
	}

	.ticket-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-bottom: 0.5rem;
	}

	.urgency-badge {
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
		font-size: 0.72rem;
		font-weight: 700;
		border: 1px solid;
		letter-spacing: 0.04em;
	}

	.score-badge {
		font-size: 0.75rem;
		color: var(--color-text-muted);
		background: var(--color-bg);
		border: 1px solid var(--color-border);
		padding: 0.15rem 0.5rem;
		border-radius: var(--radius-sm);
	}

	.status-chip {
		font-size: 0.78rem;
		font-weight: 600;
		text-transform: capitalize;
	}

	.ticket-type {
		font-size: 0.78rem;
		color: var(--color-text-muted);
		text-transform: capitalize;
		margin-left: auto;
	}

	.ticket-title {
		font-size: 1rem;
		font-weight: 600;
		color: var(--color-text);
		margin: 0 0 0.35rem 0;
	}

	.ticket-desc {
		font-size: 0.88rem;
		color: var(--color-text-muted);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		margin: 0 0 0.5rem 0;
	}

	.ticket-footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.ticket-meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.8rem;
		color: var(--color-text-muted);
		flex-wrap: wrap;
	}

	.assigned { color: var(--color-primary); }
	.unassigned { font-style: italic; }
	.ticket-id { opacity: 0.5; }

	.ticket-actions {
		display: flex;
		gap: 0.4rem;
	}

	.btn-tiny {
		padding: 0.25rem 0.6rem;
		font-size: 0.78rem;
		font-weight: 600;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		color: var(--color-text-muted);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-tiny:hover {
		border-color: var(--color-primary);
		color: var(--color-primary);
	}

	.btn-tiny-success:hover {
		border-color: var(--color-success);
		color: var(--color-success);
	}

	/* ── States ──────────────────────────────────────── */

	.loading-text {
		text-align: center;
		color: var(--color-text-muted);
		padding: 3rem;
	}

	.empty-state {
		text-align: center;
		padding: 3rem;
		color: var(--color-text-muted);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}

	.alert {
		padding: 0.75rem 1rem;
		border-radius: var(--radius-sm);
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}

	.alert-error {
		background-color: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: var(--color-error);
	}

	/* ── Mesh panel ─────────────────────────────────── */

	.mesh-panel {
		padding: 0.85rem 1.25rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		margin-bottom: 1rem;
		border-left: 3px solid var(--color-warning);
	}

	.mesh-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.mesh-status-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.mesh-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--color-text-muted);
		flex-shrink: 0;
	}

	.mesh-dot.mesh-connected {
		background: var(--color-success);
	}

	.mesh-dot.mesh-scanning {
		background: var(--color-warning);
		animation: pulse 1.2s infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	.mesh-label {
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--color-text);
	}

	.mesh-peers {
		font-size: 0.78rem;
		color: var(--color-text-muted);
		background: var(--color-bg);
		padding: 0.15rem 0.5rem;
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
	}

	.mesh-actions {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.btn-mesh {
		padding: 0.35rem 0.8rem;
		font-size: 0.82rem;
		font-weight: 600;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		color: var(--color-primary);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-mesh:hover:not(:disabled) {
		border-color: var(--color-primary);
		background: var(--color-primary);
		color: white;
	}

	.btn-mesh:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-mesh-disconnect {
		color: var(--color-text-muted);
	}

	.btn-mesh-disconnect:hover {
		border-color: var(--color-error);
		background: var(--color-error);
		color: white;
	}

	.btn-mesh-sync {
		color: var(--color-success);
		border-color: var(--color-success);
	}

	.btn-mesh-sync:hover:not(:disabled) {
		background: var(--color-success);
		color: white;
	}

	.mesh-error {
		font-size: 0.82rem;
		color: var(--color-error);
		margin: 0.5rem 0 0 0;
	}

	.via-mesh-badge {
		display: inline-block;
		font-size: 0.68rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0.15rem 0.45rem;
		border-radius: 999px;
		background: var(--color-warning);
		color: white;
	}

	.mesh-tickets-section {
		margin-bottom: 1.5rem;
	}

	.mesh-tickets-section h2 {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.mesh-ticket-card {
		border-left: 3px solid var(--color-warning);
	}

	.btn-mesh-send {
		background: var(--color-warning);
	}

	.btn-mesh-send:hover:not(:disabled) {
		background: var(--color-warning);
		filter: brightness(0.9);
	}

	@media (max-width: 640px) {
		.form-row {
			grid-template-columns: 1fr;
		}

		.controls {
			flex-direction: column;
		}

		.ticket-type {
			margin-left: 0;
		}
	}
</style>
