<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isLoggedIn, user, token } from '$lib/stores/auth';
	import { api } from '$lib/api';

	interface DashboardData {
		resources_count: number;
		skills_count: number;
		bookings_count: number;
		messages_unread_count: number;
		reputation_score: number;
		reputation_level: string;
	}

	let dashboard: DashboardData | null = null;
	let loading = true;
	let error = '';
	let activeTab = 'overview';

	// Password change form state
	let passwordForm = {
		current_password: '',
		new_password: '',
		confirm_password: '',
		error: '',
		success: false,
		loading: false
	};

	// Email change form state
	let emailForm = {
		new_email: '',
		password: '',
		error: '',
		success: false,
		loading: false
	};

	onMount(async () => {
		if (!$isLoggedIn) {
			goto('/login');
			return;
		}

		try {
			dashboard = await api<DashboardData>('/users/me/dashboard', { auth: true });
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load dashboard';
		} finally {
			loading = false;
		}
	});

	async function handlePasswordChange() {
		passwordForm.error = '';
		passwordForm.success = false;

		if (!passwordForm.current_password || !passwordForm.new_password) {
			passwordForm.error = 'All fields are required';
			return;
		}

		if (passwordForm.new_password !== passwordForm.confirm_password) {
			passwordForm.error = 'New passwords do not match';
			return;
		}

		if (passwordForm.new_password === passwordForm.current_password) {
			passwordForm.error = 'New password must be different from current password';
			return;
		}

		passwordForm.loading = true;

		try {
			await api('/users/me/change-password', {
				method: 'POST',
				body: {
					current_password: passwordForm.current_password,
					new_password: passwordForm.new_password
				},
				auth: true
			});

			passwordForm.success = true;
			passwordForm.current_password = '';
			passwordForm.new_password = '';
			passwordForm.confirm_password = '';

			setTimeout(() => {
				passwordForm.success = false;
			}, 3000);
		} catch (err) {
			passwordForm.error = err instanceof Error ? err.message : 'Failed to change password';
		} finally {
			passwordForm.loading = false;
		}
	}

	async function handleEmailChange() {
		emailForm.error = '';
		emailForm.success = false;

		if (!emailForm.new_email || !emailForm.password) {
			emailForm.error = 'Email and password are required';
			return;
		}

		if (emailForm.new_email === $user?.email) {
			emailForm.error = 'New email must be different from current email';
			return;
		}

		emailForm.loading = true;

		try {
			const updatedUser = await api('/users/me/change-email', {
				method: 'POST',
				body: {
					new_email: emailForm.new_email,
					password: emailForm.password
				},
				auth: true
			});

			user.set(updatedUser);
			emailForm.success = true;
			emailForm.new_email = '';
			emailForm.password = '';

			setTimeout(() => {
				emailForm.success = false;
			}, 3000);
		} catch (err) {
			emailForm.error = err instanceof Error ? err.message : 'Failed to change email';
		} finally {
			emailForm.loading = false;
		}
	}
</script>

<svelte:head>
	<title>Dashboard - NeighbourGood</title>
</svelte:head>

<div class="dashboard">
	<h1>My Dashboard</h1>

	{#if loading}
		<div class="loading">Loading dashboard...</div>
	{:else if error}
		<div class="alert alert-error">{error}</div>
	{:else}
		<div class="tabs">
			<button
				class="tab-button"
				class:active={activeTab === 'overview'}
				onclick={() => activeTab = 'overview'}
			>
				Overview
			</button>
			<button
				class="tab-button"
				class:active={activeTab === 'settings'}
				onclick={() => activeTab = 'settings'}
			>
				Account Settings
			</button>
		</div>

		{#if activeTab === 'overview'}
			<div class="tab-content">
				<div class="overview-grid">
					<div class="overview-card">
						<div class="card-icon">📦</div>
						<div class="card-content">
							<div class="card-label">Resources</div>
							<div class="card-value">{dashboard.resources_count}</div>
						</div>
					</div>

					<div class="overview-card">
						<div class="card-icon">🎯</div>
						<div class="card-content">
							<div class="card-label">Skills</div>
							<div class="card-value">{dashboard.skills_count}</div>
						</div>
					</div>

					<div class="overview-card">
						<div class="card-icon">📋</div>
						<div class="card-content">
							<div class="card-label">Bookings</div>
							<div class="card-value">{dashboard.bookings_count}</div>
						</div>
					</div>

					<div class="overview-card">
						<div class="card-icon">💬</div>
						<div class="card-content">
							<div class="card-label">Unread Messages</div>
							<div class="card-value">{dashboard.messages_unread_count}</div>
						</div>
					</div>
				</div>

				<div class="reputation-section">
					<h2>Your Reputation</h2>
					<div class="reputation-card">
						<div class="reputation-score">{dashboard.reputation_score}</div>
						<div class="reputation-info">
							<div class="reputation-level">{dashboard.reputation_level}</div>
							<div class="reputation-subtitle">Community Member</div>
						</div>
					</div>
				</div>
			</div>
		{:else if activeTab === 'settings'}
			<div class="tab-content">
				<div class="settings-section">
					<h2>Account Information</h2>
					<div class="info-group">
						<label>Display Name</label>
						<p class="info-value">{$user?.display_name}</p>
						<p class="info-hint">Username changes are prohibited for security</p>
					</div>

					<div class="info-group">
						<label>Email</label>
						<p class="info-value">{$user?.email}</p>
					</div>

					<div class="info-group">
						<label>Community/Neighbourhood</label>
						<p class="info-value">{$user?.neighbourhood || 'Not set'}</p>
						<p class="info-hint">You can only be in one community at a time</p>
					</div>

					<div class="info-group">
						<label>Member Since</label>
						<p class="info-value">{new Date($user?.created_at || '').toLocaleDateString()}</p>
					</div>
				</div>

				<hr class="section-divider" />

				<div class="settings-section">
					<h2>Change Password</h2>

					{#if passwordForm.success}
						<div class="alert alert-success">Password changed successfully!</div>
					{:else if passwordForm.error}
						<div class="alert alert-error">{passwordForm.error}</div>
					{/if}

					<form class="form" onsubmit|preventDefault={handlePasswordChange}>
						<div class="form-group">
							<label for="current-password">Current Password</label>
							<input
								id="current-password"
								type="password"
								bind:value={passwordForm.current_password}
								required
								disabled={passwordForm.loading}
							/>
						</div>

						<div class="form-group">
							<label for="new-password">New Password</label>
							<input
								id="new-password"
								type="password"
								bind:value={passwordForm.new_password}
								required
								disabled={passwordForm.loading}
								placeholder="Min 8 chars, 1 uppercase, 1 lowercase, 1 digit"
							/>
						</div>

						<div class="form-group">
							<label for="confirm-password">Confirm New Password</label>
							<input
								id="confirm-password"
								type="password"
								bind:value={passwordForm.confirm_password}
								required
								disabled={passwordForm.loading}
							/>
						</div>

						<button type="submit" class="btn btn-primary" disabled={passwordForm.loading}>
							{passwordForm.loading ? 'Changing...' : 'Change Password'}
						</button>
					</form>
				</div>

				<hr class="section-divider" />

				<div class="settings-section">
					<h2>Change Email</h2>

					{#if emailForm.success}
						<div class="alert alert-success">Email changed successfully!</div>
					{:else if emailForm.error}
						<div class="alert alert-error">{emailForm.error}</div>
					{/if}

					<form class="form" onsubmit|preventDefault={handleEmailChange}>
						<div class="form-group">
							<label for="new-email">New Email</label>
							<input
								id="new-email"
								type="email"
								bind:value={emailForm.new_email}
								required
								disabled={emailForm.loading}
							/>
						</div>

						<div class="form-group">
							<label for="email-password">Password (to confirm change)</label>
							<input
								id="email-password"
								type="password"
								bind:value={emailForm.password}
								required
								disabled={emailForm.loading}
							/>
						</div>

						<button type="submit" class="btn btn-primary" disabled={emailForm.loading}>
							{emailForm.loading ? 'Changing...' : 'Change Email'}
						</button>
					</form>
				</div>
			</div>
		{/if}
	{/if}
</div>

<style>
	.dashboard {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	h1 {
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--color-text);
		margin: 0;
	}

	h2 {
		font-size: 1.3rem;
		font-weight: 600;
		color: var(--color-text);
		margin: 1.5rem 0 1rem 0;
	}

	.loading {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-muted);
	}

	/* ── Tabs ──────────────────────────────────────────────────── */

	.tabs {
		display: flex;
		gap: 0.5rem;
		border-bottom: 2px solid var(--color-border);
		margin-bottom: 1.5rem;
	}

	.tab-button {
		background: none;
		border: none;
		padding: 0.75rem 1rem;
		font-size: 0.95rem;
		font-weight: 500;
		color: var(--color-text-muted);
		cursor: pointer;
		border-bottom: 3px solid transparent;
		margin-bottom: -2px;
		transition: all var(--transition-fast);
	}

	.tab-button:hover {
		color: var(--color-text);
	}

	.tab-button.active {
		color: var(--color-primary);
		border-bottom-color: var(--color-primary);
	}

	.tab-content {
		animation: fadeIn 0.2s ease-in-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(5px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* ── Overview Grid ─────────────────────────────────────────── */

	.overview-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.overview-card {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1.5rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
	}

	.overview-card:hover {
		border-color: var(--color-primary);
		box-shadow: var(--shadow-sm);
	}

	.card-icon {
		font-size: 2rem;
	}

	.card-content {
		display: flex;
		flex-direction: column;
	}

	.card-label {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.card-value {
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--color-text);
	}

	/* ── Reputation Section ────────────────────────────────────── */

	.reputation-section {
		margin-top: 2rem;
	}

	.reputation-card {
		display: flex;
		align-items: center;
		gap: 2rem;
		padding: 2rem;
		background: linear-gradient(135deg, var(--color-primary-light), var(--color-surface));
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
	}

	.reputation-score {
		font-size: 3.5rem;
		font-weight: 700;
		color: var(--color-primary);
		min-width: 80px;
	}

	.reputation-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.reputation-level {
		font-size: 1.3rem;
		font-weight: 600;
		color: var(--color-text);
	}

	.reputation-subtitle {
		font-size: 0.9rem;
		color: var(--color-text-muted);
	}

	/* ── Settings Section ──────────────────────────────────────── */

	.settings-section {
		margin-bottom: 2rem;
	}

	.info-group {
		margin-bottom: 1.5rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid var(--color-border);
	}

	.info-group:last-child {
		border-bottom: none;
		padding-bottom: 0;
		margin-bottom: 0;
	}

	.info-group label {
		display: block;
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--color-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.5rem;
	}

	.info-value {
		font-size: 1rem;
		color: var(--color-text);
		margin: 0;
		word-break: break-all;
	}

	.info-hint {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin: 0.5rem 0 0 0;
		font-style: italic;
	}

	.section-divider {
		border: none;
		border-top: 1px solid var(--color-border);
		margin: 2rem 0;
	}

	/* ── Forms ─────────────────────────────────────────────────── */

	.form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.form-group label {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--color-text);
	}

	.form-group input {
		padding: 0.75rem 1rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		font-size: 0.95rem;
		background: var(--color-surface);
		color: var(--color-text);
		transition: border-color var(--transition-fast);
	}

	.form-group input:focus {
		outline: none;
		border-color: var(--color-primary);
		box-shadow: 0 0 0 2px var(--color-primary-light);
	}

	.form-group input:disabled {
		background: var(--color-border);
		cursor: not-allowed;
		opacity: 0.6;
	}

	/* ── Buttons ───────────────────────────────────────────────── */

	.btn {
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: var(--radius-sm);
		font-size: 0.95rem;
		font-weight: 600;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-primary {
		background: var(--color-primary);
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-primary-hover);
		box-shadow: var(--shadow-md);
		transform: translateY(-2px);
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* ── Alerts ────────────────────────────────────────────────── */

	.alert {
		padding: 1rem;
		border-radius: var(--radius-sm);
		margin-bottom: 1rem;
		font-size: 0.95rem;
	}

	.alert-success {
		background: var(--color-success);
		background-color: rgba(34, 197, 94, 0.1);
		border: 1px solid rgba(34, 197, 94, 0.3);
		color: var(--color-success);
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

		h2 {
			font-size: 1.1rem;
		}

		.overview-grid {
			grid-template-columns: 1fr;
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
