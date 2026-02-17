<script lang="ts">
	import { onMount } from 'svelte';

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
				if (platformStatus?.mode === 'red') {
					document.documentElement.setAttribute('data-mode', 'red');
				}
			} else {
				error = 'Backend unavailable';
			}
		} catch {
			error = 'Could not connect to backend';
		}
	});

	const modeLabel = $derived(
		platformStatus?.mode === 'red' ? 'Red Sky (Crisis)' : 'Blue Sky (Normal)'
	);

	const modeClass = $derived(platformStatus?.mode === 'red' ? 'mode-red' : 'mode-blue');
</script>

<main class="container">
	<header>
		<h1>NeighbourGood</h1>
		<p class="tagline">Share more. Own less. Help each other.</p>
	</header>

	<section class="status-card">
		<h2>Platform Status</h2>
		{#if error}
			<p class="error">{error}</p>
			<p class="hint">Make sure the backend is running on port 8000.</p>
		{:else if platformStatus}
			<div class="status-grid">
				<div class="status-item">
					<span class="label">Status</span>
					<span class="value">
						<span class="status-dot"></span>
						{platformStatus.status}
					</span>
				</div>
				<div class="status-item">
					<span class="label">Version</span>
					<span class="value">{platformStatus.version}</span>
				</div>
				<div class="status-item">
					<span class="label">Mode</span>
					<span class="value {modeClass}">{modeLabel}</span>
				</div>
			</div>
		{:else}
			<p class="loading">Connecting to backend...</p>
		{/if}
	</section>

	<section class="features">
		<h2>What is NeighbourGood?</h2>
		<div class="feature-grid">
			<div class="feature-card">
				<h3>Share Resources</h3>
				<p>
					Lend and borrow tools, vehicles, equipment, and more within your
					neighbourhood.
				</p>
			</div>
			<div class="feature-card">
				<h3>Exchange Skills</h3>
				<p>
					Offer your expertise and learn from neighbours — from cooking to
					carpentry.
				</p>
			</div>
			<div class="feature-card">
				<h3>Crisis Ready</h3>
				<p>
					When disaster strikes, the platform switches to emergency mode for
					rapid coordination.
				</p>
			</div>
			<div class="feature-card">
				<h3>Self-Hosted</h3>
				<p>
					Run it on your own server. Your community's data stays in your
					community.
				</p>
			</div>
		</div>
	</section>
</main>

<style>
	.container {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}

	header {
		text-align: center;
		margin-bottom: 3rem;
	}

	header h1 {
		font-size: 2.5rem;
		color: var(--color-primary);
		margin-bottom: 0.5rem;
	}

	.tagline {
		font-size: 1.2rem;
		color: var(--color-text-muted);
	}

	.status-card,
	.features {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.5rem;
		margin-bottom: 2rem;
		box-shadow: var(--shadow);
	}

	h2 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: var(--color-text);
	}

	.status-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
	}

	.status-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.label {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
	}

	.value {
		font-size: 1.1rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background-color: var(--color-status-dot);
		display: inline-block;
	}

	.mode-blue {
		color: var(--color-primary);
	}

	.mode-red {
		color: #ef4444;
	}

	.error {
		color: #ef4444;
		font-weight: 600;
	}

	.hint {
		color: var(--color-text-muted);
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}

	.loading {
		color: var(--color-text-muted);
	}

	.feature-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}

	.feature-card {
		padding: 1rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
	}

	.feature-card h3 {
		font-size: 1rem;
		margin-bottom: 0.5rem;
		color: var(--color-primary);
	}

	.feature-card p {
		font-size: 0.9rem;
		color: var(--color-text-muted);
	}
</style>
