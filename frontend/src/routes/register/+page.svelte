<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { token, user } from '$lib/stores/auth';
	import type { UserProfile } from '$lib/stores/auth';

	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let neighbourhood = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		loading = true;

		try {
			const res = await api<{ access_token: string }>('/auth/register', {
				method: 'POST',
				body: {
					email,
					password,
					display_name: displayName,
					neighbourhood: neighbourhood || null
				}
			});
			token.set(res.access_token);

			const profile = await api<UserProfile>('/users/me', { auth: true });
			user.set(profile);

			goto('/resources');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="auth-page">
	<h1>Create Account</h1>
	<p class="subtitle">Join your neighbourhood community.</p>

	{#if error}
		<p class="error">{error}</p>
	{/if}

	<form onsubmit={handleSubmit}>
		<label>
			<span>Email</span>
			<input type="email" bind:value={email} required />
		</label>
		<label>
			<span>Password</span>
			<input type="password" bind:value={password} required minlength="6" />
		</label>
		<label>
			<span>Display Name</span>
			<input type="text" bind:value={displayName} required />
		</label>
		<label>
			<span>Neighbourhood (optional)</span>
			<input type="text" bind:value={neighbourhood} placeholder="e.g. Kreuzberg, Friedrichshain" />
		</label>
		<button type="submit" disabled={loading}>
			{loading ? 'Creating account...' : 'Sign Up'}
		</button>
	</form>

	<p class="switch">Already have an account? <a href="/login">Login</a></p>
</div>

<style>
	.auth-page {
		max-width: 400px;
		margin: 2rem auto;
	}

	h1 {
		font-size: 1.75rem;
		margin-bottom: 0.25rem;
	}

	.subtitle {
		color: var(--color-text-muted);
		margin-bottom: 1.5rem;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
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

	input {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.95rem;
		background: var(--color-surface);
		color: var(--color-text);
	}

	input:focus {
		outline: 2px solid var(--color-primary);
		outline-offset: -1px;
	}

	button {
		padding: 0.6rem;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius);
		font-size: 1rem;
		cursor: pointer;
		margin-top: 0.5rem;
	}

	button:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.error {
		color: #ef4444;
		background: #fef2f2;
		padding: 0.5rem 0.75rem;
		border-radius: var(--radius);
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}

	.switch {
		text-align: center;
		margin-top: 1.5rem;
		font-size: 0.9rem;
		color: var(--color-text-muted);
	}
</style>
