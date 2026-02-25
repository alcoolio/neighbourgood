<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isLoggedIn, user } from '$lib/stores/auth';
	import { api } from '$lib/api';

	let passwordForm = $state({
		current_password: '',
		new_password: '',
		confirm_password: '',
		error: '',
		success: false,
		loading: false
	});

	let emailForm = $state({
		new_email: '',
		password: '',
		error: '',
		success: false,
		loading: false
	});

	onMount(() => {
		if (!$isLoggedIn) {
			goto('/login');
		}
	});

	async function handlePasswordChange(e: Event) {
		e.preventDefault();
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

	async function handleEmailChange(e: Event) {
		e.preventDefault();
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
	<title>Settings - NeighbourGood</title>
</svelte:head>

<div class="settings-page">
	<h1>Account Settings</h1>

	<div class="settings-section">
		<h2>Account Information</h2>
		<div class="info-group">
			<label>Display Name</label>
			<p class="info-value">{$user?.display_name}</p>
		</div>

		<div class="info-group">
			<label>Email</label>
			<p class="info-value">{$user?.email}</p>
		</div>

		<div class="info-group">
			<label>Community/Neighbourhood</label>
			<p class="info-value">{$user?.neighbourhood || 'Not set'}</p>
			<p class="info-hint"><a href="/communities">Manage your communities</a></p>
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

		<form class="form" onsubmit={handlePasswordChange}>
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

		<form class="form" onsubmit={handleEmailChange}>
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

<style>
	.settings-page {
		max-width: 600px;
	}

	h1 {
		font-size: 1.9rem;
		font-weight: 400;
		color: var(--color-text);
		margin: 0 0 2rem 0;
	}

	h2 {
		font-size: 1.25rem;
		font-weight: 500;
		color: var(--color-text);
		margin: 1.5rem 0 1rem 0;
	}

	.settings-section {
		margin-bottom: 1rem;
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

	.alert {
		padding: 1rem;
		border-radius: var(--radius-sm);
		margin-bottom: 1rem;
		font-size: 0.95rem;
	}

	.alert-success {
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
	}
</style>
