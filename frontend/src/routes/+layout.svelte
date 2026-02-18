<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { isLoggedIn, user, token, logout } from '$lib/stores/auth';
	import type { UserProfile } from '$lib/stores/auth';
	import { theme, toggleTheme } from '$lib/stores/theme';
	import { api } from '$lib/api';

	let { children } = $props();

	onMount(async () => {
		const t = $token;
		if (t && !$user) {
			try {
				const profile = await api<UserProfile>('/users/me', { auth: true });
				user.set(profile);
			} catch {
				logout();
			}
		}
	});
</script>

<svelte:head>
	<title>NeighbourGood</title>
	<meta name="description" content="Community resource sharing platform" />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
</svelte:head>

<nav class="main-nav">
	<div class="nav-inner">
		<a href="/" class="nav-brand">
			<span class="brand-icon">N</span>
			<span class="brand-text">NeighbourGood</span>
		</a>
		<div class="nav-links">
			<a href="/resources" class="nav-link">Resources</a>
			<a href="/skills" class="nav-link">Skills</a>
			{#if $isLoggedIn}
				<a href="/communities" class="nav-link">Communities</a>
				<a href="/bookings" class="nav-link">Bookings</a>
				<a href="/messages" class="nav-link">Messages</a>
			{/if}

			<button
				class="theme-toggle"
				onclick={toggleTheme}
				aria-label="Toggle dark mode"
				title={$theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
			>
				{#if $theme === 'light'}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
				{:else}
					<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
				{/if}
			</button>

			{#if $isLoggedIn}
				<div class="nav-user-group">
					<span class="nav-user">{$user?.display_name ?? 'Account'}</span>
					<button class="nav-btn" onclick={() => { logout(); window.location.href = '/'; }}>
						Logout
					</button>
				</div>
			{:else}
				<a href="/login" class="nav-link">Login</a>
				<a href="/register" class="nav-btn-primary">Sign Up</a>
			{/if}
		</div>
	</div>
</nav>

<div class="page-content fade-in">
	{@render children()}
</div>

<style>
	.main-nav {
		position: sticky;
		top: 0;
		z-index: 100;
		background: var(--color-surface);
		border-bottom: 1px solid var(--color-border);
		box-shadow: var(--shadow-sm);
		transition: background-color var(--transition), border-color var(--transition), box-shadow var(--transition);
	}

	.nav-inner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.6rem 1.5rem;
		max-width: 1100px;
		margin: 0 auto;
	}

	.nav-brand {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		text-decoration: none;
		color: var(--color-text);
		transition: transform var(--transition-fast);
	}

	.nav-brand:hover {
		text-decoration: none;
		transform: scale(1.02);
	}

	.brand-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		border-radius: var(--radius-sm);
		background: var(--color-primary);
		color: white;
		font-weight: 700;
		font-size: 1rem;
	}

	.brand-text {
		font-weight: 700;
		font-size: 1.1rem;
		letter-spacing: -0.02em;
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}

	.nav-link {
		color: var(--color-text-muted);
		text-decoration: none;
		font-size: 0.88rem;
		font-weight: 500;
		padding: 0.4rem 0.7rem;
		border-radius: var(--radius-sm);
		transition: color var(--transition-fast), background-color var(--transition-fast);
	}

	.nav-link:hover {
		color: var(--color-text);
		background: var(--color-primary-light);
		text-decoration: none;
	}

	.theme-toggle {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		color: var(--color-text-muted);
		cursor: pointer;
		transition: all var(--transition-fast);
		margin: 0 0.25rem;
	}

	.theme-toggle:hover {
		border-color: var(--color-primary);
		color: var(--color-primary);
		background: var(--color-primary-light);
	}

	.theme-toggle:active {
		transform: scale(0.92);
	}

	.nav-user-group {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-left: 0.25rem;
		padding-left: 0.75rem;
		border-left: 1px solid var(--color-border);
	}

	.nav-user {
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--color-text);
	}

	.nav-btn {
		background: none;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		padding: 0.3rem 0.7rem;
		font-size: 0.82rem;
		font-weight: 500;
		color: var(--color-text-muted);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.nav-btn:hover {
		border-color: var(--color-error);
		color: var(--color-error);
	}

	.nav-btn-primary {
		display: inline-flex;
		align-items: center;
		background: var(--color-primary);
		color: white !important;
		padding: 0.4rem 0.9rem;
		border-radius: var(--radius-sm);
		font-size: 0.85rem;
		font-weight: 600;
		transition: all var(--transition-fast);
		text-decoration: none;
	}

	.nav-btn-primary:hover {
		background: var(--color-primary-hover);
		text-decoration: none;
		box-shadow: var(--shadow-md);
		transform: translateY(-1px);
	}

	.page-content {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem 1.25rem;
	}
</style>
