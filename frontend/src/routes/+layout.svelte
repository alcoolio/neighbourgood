<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { isLoggedIn, user, token, logout } from '$lib/stores/auth';
	import type { UserProfile } from '$lib/stores/auth';
	import { theme, toggleTheme } from '$lib/stores/theme';
	import { api } from '$lib/api';

	let { children } = $props();
	let mobileMenuOpen = $state(false);

	function closeMobileMenu() {
		mobileMenuOpen = false;
	}

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
		<a href="/" class="nav-brand" onclick={closeMobileMenu}>
			<span class="brand-icon">N</span>
			<span class="brand-text">NeighbourGood</span>
		</a>

		<button
			class="hamburger"
			class:open={mobileMenuOpen}
			onclick={() => mobileMenuOpen = !mobileMenuOpen}
			aria-label="Toggle menu"
			aria-expanded={mobileMenuOpen}
		>
			<span class="hamburger-line"></span>
			<span class="hamburger-line"></span>
			<span class="hamburger-line"></span>
		</button>

		<div class="nav-links" class:mobile-open={mobileMenuOpen}>
			{#if $isLoggedIn}
				<a href="/resources" class="nav-link" onclick={closeMobileMenu}>Resources</a>
				<a href="/skills" class="nav-link" onclick={closeMobileMenu}>Skills</a>
				<a href="/communities" class="nav-link" onclick={closeMobileMenu}>Communities</a>
				<a href="/bookings" class="nav-link" onclick={closeMobileMenu}>Bookings</a>
				<a href="/messages" class="nav-link" onclick={closeMobileMenu}>Messages</a>
			{:else}
				<a href="/explore" class="nav-link" onclick={closeMobileMenu}>Explore</a>
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
					<button class="nav-btn" onclick={() => { closeMobileMenu(); logout(); window.location.href = '/'; }}>
						Logout
					</button>
				</div>
			{:else}
				<a href="/login" class="nav-link" onclick={closeMobileMenu}>Login</a>
				<a href="/register" class="nav-btn-primary" onclick={closeMobileMenu}>Sign Up</a>
			{/if}
		</div>
	</div>
</nav>

{#if mobileMenuOpen}
	<button class="mobile-overlay" onclick={closeMobileMenu} aria-label="Close menu"></button>
{/if}

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

	/* ── Hamburger button (hidden on desktop) ────────────────── */

	.hamburger {
		display: none;
		flex-direction: column;
		justify-content: center;
		gap: 4px;
		width: 36px;
		height: 36px;
		padding: 6px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		background: var(--color-surface);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.hamburger:hover {
		border-color: var(--color-primary);
	}

	.hamburger-line {
		display: block;
		width: 100%;
		height: 2px;
		background: var(--color-text);
		border-radius: 1px;
		transition: all var(--transition-fast);
		transform-origin: center;
	}

	.hamburger.open .hamburger-line:nth-child(1) {
		transform: translateY(6px) rotate(45deg);
	}

	.hamburger.open .hamburger-line:nth-child(2) {
		opacity: 0;
	}

	.hamburger.open .hamburger-line:nth-child(3) {
		transform: translateY(-6px) rotate(-45deg);
	}

	/* ── Nav links ────────────────────────────────────────────── */

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

	/* ── Mobile overlay ──────────────────────────────────────── */

	.mobile-overlay {
		display: none;
	}

	/* ── Responsive: mobile layout ───────────────────────────── */

	@media (max-width: 768px) {
		.hamburger {
			display: flex;
		}

		.nav-links {
			display: none;
			position: absolute;
			top: 100%;
			left: 0;
			right: 0;
			flex-direction: column;
			align-items: stretch;
			gap: 0;
			background: var(--color-surface);
			border-bottom: 1px solid var(--color-border);
			box-shadow: var(--shadow-md);
			padding: 0.5rem 0;
			z-index: 99;
		}

		.nav-links.mobile-open {
			display: flex;
		}

		.nav-link {
			padding: 0.75rem 1.5rem;
			border-radius: 0;
			font-size: 0.95rem;
		}

		.nav-link:hover {
			background: var(--color-primary-light);
		}

		.theme-toggle {
			margin: 0.25rem 1.5rem;
			align-self: flex-start;
		}

		.nav-user-group {
			margin: 0;
			padding: 0.5rem 1.5rem;
			border-left: none;
			border-top: 1px solid var(--color-border);
			justify-content: space-between;
		}

		.nav-btn-primary {
			margin: 0.25rem 1.5rem;
			justify-content: center;
		}

		.mobile-overlay {
			display: block;
			position: fixed;
			inset: 0;
			background: rgba(0, 0, 0, 0.3);
			z-index: 50;
			border: none;
			cursor: default;
		}

		.brand-text {
			font-size: 1rem;
		}
	}

	.page-content {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem 1.25rem;
	}
</style>
