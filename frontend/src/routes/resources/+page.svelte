<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { isLoggedIn } from '$lib/stores/auth';

	interface Resource {
		id: number;
		title: string;
		description: string | null;
		category: string;
		condition: string | null;
		is_available: boolean;
		owner: { display_name: string; neighbourhood: string | null };
		created_at: string;
	}

	const CATEGORIES = [
		{ value: '', label: 'All Categories' },
		{ value: 'tool', label: 'Tools' },
		{ value: 'vehicle', label: 'Vehicles' },
		{ value: 'electronics', label: 'Electronics' },
		{ value: 'furniture', label: 'Furniture' },
		{ value: 'food', label: 'Food' },
		{ value: 'clothing', label: 'Clothing' },
		{ value: 'skill', label: 'Skills' },
		{ value: 'other', label: 'Other' }
	];

	let resources: Resource[] = $state([]);
	let total = $state(0);
	let loading = $state(true);
	let filterCategory = $state('');
	let showCreateForm = $state(false);

	// Create form
	let newTitle = $state('');
	let newDescription = $state('');
	let newCategory = $state('tool');
	let newCondition = $state('good');
	let createError = $state('');

	async function loadResources() {
		loading = true;
		try {
			const params = new URLSearchParams();
			if (filterCategory) params.set('category', filterCategory);
			const res = await api<{ items: Resource[]; total: number }>(
				`/resources?${params.toString()}`
			);
			resources = res.items;
			total = res.total;
		} catch {
			resources = [];
		} finally {
			loading = false;
		}
	}

	async function handleCreate(e: Event) {
		e.preventDefault();
		createError = '';
		try {
			await api('/resources', {
				method: 'POST',
				auth: true,
				body: {
					title: newTitle,
					description: newDescription || null,
					category: newCategory,
					condition: newCondition
				}
			});
			showCreateForm = false;
			newTitle = '';
			newDescription = '';
			await loadResources();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create resource';
		}
	}

	onMount(loadResources);

	$effect(() => {
		filterCategory;
		loadResources();
	});
</script>

<div class="resources-page">
	<div class="page-header">
		<h1>Shared Resources</h1>
		{#if $isLoggedIn}
			<button class="btn-primary" onclick={() => (showCreateForm = !showCreateForm)}>
				{showCreateForm ? 'Cancel' : '+ Share Something'}
			</button>
		{/if}
	</div>

	{#if showCreateForm}
		<div class="create-form-card">
			<h2>Share a Resource</h2>
			{#if createError}
				<p class="error">{createError}</p>
			{/if}
			<form onsubmit={handleCreate}>
				<label>
					<span>Title</span>
					<input type="text" bind:value={newTitle} required placeholder="e.g. Bosch Drill" />
				</label>
				<label>
					<span>Description</span>
					<textarea bind:value={newDescription} rows="3" placeholder="What are you sharing? Any conditions?"></textarea>
				</label>
				<div class="form-row">
					<label>
						<span>Category</span>
						<select bind:value={newCategory}>
							<option value="tool">Tool</option>
							<option value="vehicle">Vehicle</option>
							<option value="electronics">Electronics</option>
							<option value="furniture">Furniture</option>
							<option value="food">Food</option>
							<option value="clothing">Clothing</option>
							<option value="skill">Skill</option>
							<option value="other">Other</option>
						</select>
					</label>
					<label>
						<span>Condition</span>
						<select bind:value={newCondition}>
							<option value="new">New</option>
							<option value="good">Good</option>
							<option value="fair">Fair</option>
							<option value="worn">Worn</option>
						</select>
					</label>
				</div>
				<button type="submit" class="btn-primary">Share Resource</button>
			</form>
		</div>
	{/if}

	<div class="filter-bar">
		<select bind:value={filterCategory}>
			{#each CATEGORIES as cat}
				<option value={cat.value}>{cat.label}</option>
			{/each}
		</select>
		<span class="result-count">{total} resource{total !== 1 ? 's' : ''}</span>
	</div>

	{#if loading}
		<p class="loading">Loading resources...</p>
	{:else if resources.length === 0}
		<div class="empty-state">
			<p>No resources shared yet.</p>
			{#if $isLoggedIn}
				<p>Be the first to share something with your neighbourhood!</p>
			{:else}
				<p><a href="/register">Sign up</a> to start sharing.</p>
			{/if}
		</div>
	{:else}
		<div class="resource-grid">
			{#each resources as resource}
				<a href="/resources/{resource.id}" class="resource-card">
					<div class="card-header">
						<span class="category-badge">{resource.category}</span>
						{#if !resource.is_available}
							<span class="unavailable-badge">Unavailable</span>
						{/if}
					</div>
					<h3>{resource.title}</h3>
					{#if resource.description}
						<p class="description">{resource.description}</p>
					{/if}
					<div class="card-footer">
						<span class="owner">by {resource.owner.display_name}</span>
						{#if resource.condition}
							<span class="condition">{resource.condition}</span>
						{/if}
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>

<style>
	.resources-page {
		max-width: 800px;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1.5rem;
	}

	h1 {
		font-size: 1.75rem;
	}

	.btn-primary {
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius);
		padding: 0.5rem 1rem;
		font-size: 0.9rem;
		cursor: pointer;
	}

	.btn-primary:hover {
		background: var(--color-primary-hover);
	}

	.create-form-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.create-form-card h2 {
		font-size: 1.1rem;
		margin-bottom: 1rem;
	}

	.create-form-card form {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
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

	input, textarea, select {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.9rem;
		background: var(--color-surface);
		color: var(--color-text);
	}

	.error {
		color: #ef4444;
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}

	.filter-bar {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.filter-bar select {
		padding: 0.4rem 0.6rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.85rem;
		background: var(--color-surface);
		color: var(--color-text);
	}

	.result-count {
		font-size: 0.85rem;
		color: var(--color-text-muted);
	}

	.resource-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: 1rem;
	}

	.resource-card {
		display: block;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1rem;
		text-decoration: none;
		color: var(--color-text);
		transition: border-color 0.15s;
	}

	.resource-card:hover {
		border-color: var(--color-primary);
		text-decoration: none;
	}

	.card-header {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.category-badge {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		background: var(--color-bg);
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
		color: var(--color-primary);
		font-weight: 600;
	}

	.unavailable-badge {
		font-size: 0.75rem;
		background: #fef2f2;
		color: #ef4444;
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
	}

	.resource-card h3 {
		font-size: 1rem;
		margin-bottom: 0.35rem;
	}

	.description {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}

	.card-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.loading {
		color: var(--color-text-muted);
	}

	.empty-state {
		text-align: center;
		padding: 3rem 1rem;
		color: var(--color-text-muted);
	}

	.empty-state p + p {
		margin-top: 0.5rem;
	}
</style>
