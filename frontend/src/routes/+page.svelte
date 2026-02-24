<script lang="ts">
	import { onMount } from 'svelte';
	import { isLoggedIn } from '$lib/stores/auth';
	import { bandwidth, platformMode } from '$lib/stores/theme';

	interface PlatformStatus {
		status: string;
		version: string;
		mode: 'blue' | 'red';
	}

	let platformStatus: PlatformStatus | null = $state(null);
	let error: string | null = $state(null);

	onMount(async () => {
		try {
			const res = await fetch('/api/status');
			if (res.ok) {
				platformStatus = await res.json();
			} else {
				error = 'Backend unavailable';
			}
		} catch {
			error = 'Could not connect to backend';
		}
	});

	const modeLabel = $derived(
		$platformMode === 'red' ? 'Red Sky (Crisis)' : 'Blue Sky (Normal)'
	);
	const modeClass = $derived($platformMode === 'red' ? 'mode-red' : 'mode-blue');
</script>

<main class="landing">
	<section class="hero slide-up">
		<div class="hero-badge">Community Resource Sharing</div>
		<h1>Share more.<br />Own less.<br /><span class="hero-accent">Help each other.</span></h1>
		<p class="hero-subtitle">
			NeighbourGood connects neighbours to share tools, skills, and resources.
			When a crisis hits, the same network becomes a lifeline.
		</p>
		<div class="hero-actions">
			{#if $isLoggedIn}
				<a href="/resources" class="btn-hero">Browse Resources</a>
			{:else}
				<a href="/register" class="btn-hero">Get Started</a>
				<a href="/login" class="btn-hero-secondary">Login</a>
			{/if}
		</div>
	</section>

	{#if $bandwidth !== 'low'}
		<section class="hero-image slide-up" style="animation-delay: 0.05s">
			<img
				src="https://repository-images.githubusercontent.com/1157105951/d1f4dfb1-a28b-4cd3-8994-c4f2906d0354"
				alt="NeighbourGood – a local network for neighbours to share stuff and skills"
				class="social-preview"
			/>
		</section>
	{/if}

	<section class="features">
		<div class="feature-grid">
			<div class="feature-card slide-up" style="animation-delay: 0.05s">
				<div class="feature-icon">&#128295;</div>
				<h3>Share Resources</h3>
				<p>Lend and borrow tools, vehicles, equipment, and more within your neighbourhood.</p>
			</div>
			<div class="feature-card slide-up" style="animation-delay: 0.1s">
				<div class="feature-icon">&#128161;</div>
				<h3>Exchange Skills</h3>
				<p>Offer your expertise and learn from neighbours — from cooking to carpentry.</p>
			</div>
			<div class="feature-card slide-up" style="animation-delay: 0.15s">
				<div class="feature-icon">&#128680;</div>
				<h3>Crisis Ready</h3>
				<p>When disaster strikes, switch to emergency mode for rapid community coordination.</p>
			</div>
			<div class="feature-card slide-up" style="animation-delay: 0.2s">
				<div class="feature-icon">&#128274;</div>
				<h3>Self-Hosted</h3>
				<p>Run it on your own server. Your community's data stays in your community.</p>
			</div>
			<div class="feature-card slide-up" style="animation-delay: 0.25s">
				<div class="feature-icon">&#127760;</div>
				<h3>Neighbourhood Groups</h3>
				<p>Join or create local communities by postcode. Share within your area, merge nearby groups.</p>
			</div>
			<div class="feature-card slide-up" style="animation-delay: 0.3s">
				<div class="feature-icon">&#128172;</div>
				<h3>Built-in Messaging</h3>
				<p>Chat directly with neighbours about bookings, coordinate pickups, and stay connected.</p>
			</div>
		</div>
	</section>

	{#if error}
		<section class="status-banner status-error fade-in">
			<span class="status-icon">!</span>
			<div>
				<p class="status-text">{error}</p>
				<p class="status-hint">Make sure the backend is running on port 8300.</p>
			</div>
		</section>
	{:else if platformStatus}
		<section class="status-banner status-ok fade-in">
			<span class="status-dot"></span>
			<span class="status-text">
				v{platformStatus.version} &middot; <span class={modeClass}>{modeLabel}</span>
			</span>
		</section>
	{/if}
</main>

<style>
	.landing {
		max-width: 800px;
		margin: 0 auto;
	}

	.hero {
		text-align: center;
		padding: 3rem 0 2.5rem;
	}

	.hero-badge {
		display: inline-block;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--color-primary);
		background: var(--color-primary-light);
		padding: 0.3rem 0.9rem;
		border-radius: 999px;
		margin-bottom: 1.25rem;
	}

	.hero h1 {
		font-size: 2.75rem;
		font-weight: 700;
		line-height: 1.15;
		letter-spacing: -0.03em;
		color: var(--color-text);
		margin-bottom: 1.25rem;
	}

	.hero-accent {
		background: linear-gradient(135deg, var(--color-primary), var(--color-accent));
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.hero-subtitle {
		font-size: 1.1rem;
		color: var(--color-text-muted);
		max-width: 500px;
		margin: 0 auto 2rem;
		line-height: 1.7;
	}

	.hero-actions {
		display: flex;
		justify-content: center;
		gap: 0.75rem;
	}

	.btn-hero {
		display: inline-flex;
		align-items: center;
		padding: 0.7rem 1.5rem;
		background: var(--color-primary);
		color: white;
		border-radius: var(--radius);
		font-size: 0.95rem;
		font-weight: 600;
		text-decoration: none;
		transition: all var(--transition-fast);
		box-shadow: var(--shadow);
	}

	.btn-hero:hover {
		background: var(--color-primary-hover);
		box-shadow: var(--shadow-lg);
		transform: translateY(-2px);
		text-decoration: none;
	}

	.btn-hero-secondary {
		display: inline-flex;
		align-items: center;
		padding: 0.7rem 1.5rem;
		background: var(--color-surface);
		color: var(--color-text);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.95rem;
		font-weight: 500;
		text-decoration: none;
		transition: all var(--transition-fast);
	}

	.btn-hero-secondary:hover {
		border-color: var(--color-primary);
		color: var(--color-primary);
		text-decoration: none;
	}

	.features {
		margin-bottom: 2rem;
	}

	.hero-image {
		margin-bottom: 2rem;
		text-align: center;
	}

	.social-preview {
		width: 100%;
		max-width: 700px;
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-lg);
		border: 1px solid var(--color-border);
	}

	.feature-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
	}

	@media (max-width: 640px) {
		.feature-grid {
			grid-template-columns: 1fr;
		}
	}

	.feature-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-lg);
		padding: 1.5rem;
		transition: all var(--transition);
		box-shadow: var(--shadow-sm);
	}

	.feature-card:hover {
		box-shadow: var(--shadow-md);
		border-color: var(--color-border-hover);
		transform: translateY(-2px);
	}

	.feature-icon {
		font-size: 1.75rem;
		margin-bottom: 0.75rem;
	}

	.feature-card h3 {
		font-size: 0.95rem;
		font-weight: 600;
		margin-bottom: 0.4rem;
		color: var(--color-text);
	}

	.feature-card p {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		line-height: 1.6;
	}

	.status-banner {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1.25rem;
		border-radius: var(--radius);
		font-size: 0.85rem;
	}

	.status-ok {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		color: var(--color-text-muted);
	}

	.status-error {
		background: var(--color-error-bg);
		border: 1px solid var(--color-error);
		color: var(--color-error);
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--color-success);
		flex-shrink: 0;
	}

	.status-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: var(--color-error);
		color: white;
		font-weight: 700;
		font-size: 0.75rem;
		flex-shrink: 0;
	}

	.status-text { font-weight: 500; }
	.status-hint { font-size: 0.8rem; opacity: 0.8; margin-top: 0.15rem; }
	.mode-blue { color: var(--color-primary); }
	.mode-red { color: var(--color-error); }
</style>
