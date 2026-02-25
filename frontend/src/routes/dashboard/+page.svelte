<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isLoggedIn, user } from '$lib/stores/auth';
	import { api } from '$lib/api';

	interface DashboardData {
		resources_count: number;
		skills_count: number;
		bookings_count: number;
		messages_unread_count: number;
		reputation_score: number;
		reputation_level: string;
	}

	interface BookingItem {
		id: number;
		resource_title: string;
		borrower_name: string;
		start_date: string;
		end_date: string;
		status: string;
		is_owner: boolean;
	}

	interface CommunityMembership {
		id: number;
		name: string;
		mode: string;
	}

	let dashboard: DashboardData | null = $state(null);
	let pendingIncoming: BookingItem[] = $state([]);
	let pendingOutgoing: BookingItem[] = $state([]);
	let communities: CommunityMembership[] = $state([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		if (!$isLoggedIn) {
			goto('/login');
			return;
		}

		try {
			const [dashData, commData] = await Promise.all([
				api<DashboardData>('/users/me/dashboard', { auth: true }),
				api<CommunityMembership[]>('/communities/my/memberships', { auth: true })
			]);
			dashboard = dashData;
			communities = commData;

			// Fetch pending bookings for "needs attention" section
			const bookingsData = await api<{ items: any[] }>('/bookings?status=pending', { auth: true });
			if (bookingsData.items) {
				for (const b of bookingsData.items) {
					const item: BookingItem = {
						id: b.id,
						resource_title: b.resource?.title ?? `Resource #${b.resource_id}`,
						borrower_name: b.borrower?.display_name ?? 'Someone',
						start_date: b.start_date,
						end_date: b.end_date,
						status: b.status,
						is_owner: b.borrower_id !== $user?.id
					};
					if (item.is_owner) {
						pendingIncoming.push(item);
					} else {
						pendingOutgoing.push(item);
					}
				}
				// Trigger reactivity
				pendingIncoming = [...pendingIncoming];
				pendingOutgoing = [...pendingOutgoing];
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load dashboard';
		} finally {
			loading = false;
		}
	});

	const hasPendingActions = $derived(
		pendingIncoming.length > 0 ||
		pendingOutgoing.length > 0 ||
		(dashboard?.messages_unread_count ?? 0) > 0
	);
</script>

<svelte:head>
	<title>Home - NeighbourGood</title>
</svelte:head>

<div class="dashboard">
	<h1>Welcome back{$user?.display_name ? `, ${$user.display_name}` : ''}</h1>

	{#if loading}
		<div class="loading">Loading...</div>
	{:else if error}
		<div class="alert alert-error">{error}</div>
	{:else}
		<!-- Onboarding nudge -->
		{#if communities.length === 0}
			<div class="nudge-banner">
				<div class="nudge-icon">
					<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
				</div>
				<div class="nudge-text">
					<strong>Join a community to get started</strong>
					<span>Browse nearby communities or create your own to share resources and skills with neighbours.</span>
				</div>
				<a href="/onboarding" class="nudge-btn">Find Community</a>
			</div>
		{/if}

		<!-- Needs your attention -->
		{#if hasPendingActions}
			<section class="attention-section">
				<h2>Needs your attention</h2>
				<div class="attention-list">
					{#each pendingIncoming as booking}
						<a href="/bookings" class="attention-item">
							<span class="attention-dot attention-dot-warning"></span>
							<span class="attention-text">
								<strong>{booking.borrower_name}</strong> wants to borrow <strong>{booking.resource_title}</strong>
							</span>
							<span class="attention-action">Review</span>
						</a>
					{/each}
					{#each pendingOutgoing as booking}
						<a href="/bookings" class="attention-item">
							<span class="attention-dot attention-dot-info"></span>
							<span class="attention-text">
								Your request for <strong>{booking.resource_title}</strong> is waiting for approval
							</span>
							<span class="attention-action">View</span>
						</a>
					{/each}
					{#if (dashboard?.messages_unread_count ?? 0) > 0}
						<a href="/messages" class="attention-item">
							<span class="attention-dot attention-dot-primary"></span>
							<span class="attention-text">
								You have <strong>{dashboard?.messages_unread_count}</strong> unread message{(dashboard?.messages_unread_count ?? 0) > 1 ? 's' : ''}
							</span>
							<span class="attention-action">Read</span>
						</a>
					{/if}
				</div>
			</section>
		{/if}

		<!-- Quick stats -->
		{#if dashboard}
			<section>
				<h2>Your activity</h2>
				<div class="overview-grid">
					<a href="/resources" class="overview-card">
						<div class="card-icon">📦</div>
						<div class="card-content">
							<div class="card-label">Resources</div>
							<div class="card-value">{dashboard.resources_count}</div>
						</div>
					</a>

					<a href="/skills" class="overview-card">
						<div class="card-icon">🎯</div>
						<div class="card-content">
							<div class="card-label">Skills</div>
							<div class="card-value">{dashboard.skills_count}</div>
						</div>
					</a>

					<a href="/bookings" class="overview-card">
						<div class="card-icon">📋</div>
						<div class="card-content">
							<div class="card-label">Bookings</div>
							<div class="card-value">{dashboard.bookings_count}</div>
						</div>
					</a>

					<a href="/messages" class="overview-card">
						<div class="card-icon">💬</div>
						<div class="card-content">
							<div class="card-label">Unread Messages</div>
							<div class="card-value">{dashboard.messages_unread_count}</div>
						</div>
					</a>
				</div>
			</section>

			<section class="reputation-section">
				<h2>Your Reputation</h2>
				<div class="reputation-card">
					<div class="reputation-score">{dashboard.reputation_score}</div>
					<div class="reputation-info">
						<div class="reputation-level">{dashboard.reputation_level}</div>
						<div class="reputation-subtitle">Community Member</div>
					</div>
				</div>
			</section>
		{/if}
	{/if}
</div>

<style>
	.dashboard {
		max-width: 900px;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	h1 {
		font-size: 1.9rem;
		font-weight: 400;
		color: var(--color-text);
		margin: 0;
	}

	h2 {
		font-size: 1.2rem;
		font-weight: 600;
		color: var(--color-text);
		margin: 0 0 0.75rem 0;
	}

	.loading {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-muted);
	}

	/* ── Onboarding nudge ─────────────────────────────────────── */

	.nudge-banner {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1.25rem 1.5rem;
		background: linear-gradient(135deg, var(--color-primary-light), var(--color-surface));
		border: 1px solid var(--color-primary);
		border-radius: var(--radius-md);
	}

	.nudge-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 44px;
		height: 44px;
		border-radius: var(--radius);
		background: var(--color-primary);
		color: white;
		flex-shrink: 0;
	}

	.nudge-text {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		flex: 1;
		min-width: 0;
	}

	.nudge-text strong {
		font-size: 0.95rem;
		color: var(--color-text);
	}

	.nudge-text span {
		font-size: 0.85rem;
		color: var(--color-text-muted);
	}

	.nudge-btn {
		padding: 0.5rem 1.2rem;
		background: var(--color-primary);
		color: white;
		border-radius: var(--radius-sm);
		font-size: 0.88rem;
		font-weight: 600;
		text-decoration: none;
		white-space: nowrap;
		transition: all var(--transition-fast);
	}

	.nudge-btn:hover {
		background: var(--color-primary-hover);
		text-decoration: none;
		box-shadow: var(--shadow-md);
	}

	/* ── Needs attention ──────────────────────────────────────── */

	.attention-section {
		margin-top: 0.5rem;
	}

	.attention-list {
		display: flex;
		flex-direction: column;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		overflow: hidden;
	}

	.attention-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.85rem 1.25rem;
		text-decoration: none;
		color: inherit;
		transition: background-color var(--transition-fast);
		border-bottom: 1px solid var(--color-border);
	}

	.attention-item:last-child {
		border-bottom: none;
	}

	.attention-item:hover {
		background: var(--color-primary-light);
		text-decoration: none;
	}

	.attention-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.attention-dot-warning { background: var(--color-warning); }
	.attention-dot-info { background: var(--color-text-muted); }
	.attention-dot-primary { background: var(--color-primary); }

	.attention-text {
		flex: 1;
		font-size: 0.9rem;
		color: var(--color-text);
		min-width: 0;
	}

	.attention-text strong {
		font-weight: 600;
	}

	.attention-action {
		font-size: 0.82rem;
		font-weight: 600;
		color: var(--color-primary);
		white-space: nowrap;
	}

	/* ── Quick Stats Grid ─────────────────────────────────────── */

	.overview-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}

	.overview-card {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1.25rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
		text-decoration: none;
		color: inherit;
	}

	.overview-card:hover {
		border-color: var(--color-primary);
		box-shadow: var(--shadow-sm);
		text-decoration: none;
	}

	.card-icon {
		font-size: 1.75rem;
	}

	.card-content {
		display: flex;
		flex-direction: column;
	}

	.card-label {
		font-size: 0.8rem;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.card-value {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--color-text);
	}

	/* ── Reputation ───────────────────────────────────────────── */

	.reputation-section {
		margin-top: 0.5rem;
	}

	.reputation-card {
		display: flex;
		align-items: center;
		gap: 2rem;
		padding: 1.5rem 2rem;
		background: linear-gradient(135deg, var(--color-primary-light), var(--color-surface));
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
	}

	.reputation-score {
		font-size: 3rem;
		font-weight: 700;
		color: var(--color-primary);
		min-width: 70px;
	}

	.reputation-info {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.reputation-level {
		font-size: 1.2rem;
		font-weight: 600;
		color: var(--color-text);
	}

	.reputation-subtitle {
		font-size: 0.85rem;
		color: var(--color-text-muted);
	}

	/* ── Alerts ────────────────────────────────────────────────── */

	.alert {
		padding: 1rem;
		border-radius: var(--radius-sm);
		font-size: 0.95rem;
	}

	.alert-error {
		background-color: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: var(--color-error);
	}

	@media (max-width: 600px) {
		h1 {
			font-size: 1.5rem;
		}

		.overview-grid {
			grid-template-columns: 1fr;
		}

		.nudge-banner {
			flex-direction: column;
			text-align: center;
		}

		.reputation-card {
			flex-direction: column;
			align-items: flex-start;
			gap: 1rem;
		}

		.reputation-score {
			font-size: 2.5rem;
		}
	}
</style>
