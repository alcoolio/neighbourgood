<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { isLoggedIn, user, token, logout } from '$lib/stores/auth';
	import type { UserProfile } from '$lib/stores/auth';
	import { api } from '$lib/api';

	let { children } = $props();

	onMount(async () => {
		// If we have a stored token, try to load the user profile
		const t = $token;
		if (t && !$user) {
			try {
				const profile = await api<UserProfile>('/users/me', { auth: true });
				user.set(profile);
			} catch {
				// token is expired or invalid
				logout();
			}
		}
	});
</script>

<svelte:head>
	<title>NeighbourGood</title>
	<meta name="description" content="Community resource sharing platform" />
</svelte:head>

<nav class="main-nav">
	<a href="/" class="nav-brand">NeighbourGood</a>
	<div class="nav-links">
		<a href="/resources">Resources</a>
		{#if $isLoggedIn}
			<a href="/bookings">Bookings</a>
			<a href="/messages">Messages</a>
			<span class="nav-user">{$user?.display_name ?? 'Account'}</span>
			<button class="nav-btn" onclick={() => { logout(); window.location.href = '/'; }}>
				Logout
			</button>
		{:else}
			<a href="/login">Login</a>
			<a href="/register" class="nav-btn-primary">Sign Up</a>
		{/if}
	</div>
</nav>

<div class="page-content">
	{@render children()}
</div>

<style>
	.main-nav {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1.5rem;
		background: var(--color-surface);
		border-bottom: 1px solid var(--color-border);
	}

	.nav-brand {
		font-weight: 700;
		font-size: 1.2rem;
		color: var(--color-primary);
		text-decoration: none;
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.nav-links a {
		color: var(--color-text);
		text-decoration: none;
		font-size: 0.9rem;
	}

	.nav-links a:hover {
		color: var(--color-primary);
	}

	.nav-user {
		font-size: 0.9rem;
		color: var(--color-text-muted);
	}

	.nav-btn {
		background: none;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 0.35rem 0.75rem;
		font-size: 0.85rem;
		color: var(--color-text);
		cursor: pointer;
	}

	.nav-btn:hover {
		border-color: var(--color-primary);
		color: var(--color-primary);
	}

	.nav-btn-primary {
		background: var(--color-primary);
		color: white !important;
		padding: 0.35rem 0.75rem;
		border-radius: var(--radius);
		font-size: 0.85rem;
	}

	.nav-btn-primary:hover {
		background: var(--color-primary-hover);
		text-decoration: none;
	}

	.page-content {
		max-width: 960px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}
</style>
