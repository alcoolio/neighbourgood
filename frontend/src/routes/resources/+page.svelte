<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { isLoggedIn } from '$lib/stores/auth';
	import { bandwidth } from '$lib/stores/theme';

	interface Resource {
		id: number;
		title: string;
		description: string | null;
		category: string;
		condition: string | null;
		image_url: string | null;
		is_available: boolean;
		community_id: number | null;
		owner: { display_name: string; neighbourhood: string | null };
		created_at: string;
	}

	interface MyCommunity {
		id: number;
		name: string;
		postal_code: string;
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

	const CATEGORY_ICONS: Record<string, string> = {
		tool: '🔧', vehicle: '🚗', electronics: '⚡', furniture: '🪑',
		food: '🍎', clothing: '👕', skill: '💡', other: '📦'
	};

	let resources: Resource[] = $state([]);
	let total = $state(0);
	let loading = $state(true);
	let filterCategory = $state('');
	let filterCommunity = $state(''); // Only used to filter a specific community, auto-filters to joined communities if empty
	let searchQuery = $state('');
	let searchTimeout: ReturnType<typeof setTimeout> | null = $state(null);
	let showCreateForm = $state(false);

	// Create form
	let newTitle = $state('');
	let newDescription = $state('');
	let newCategory = $state('tool');
	let newCondition = $state('good');
	let newCommunityId = $state('');
	let createError = $state('');
	let myCommunities = $state<MyCommunity[]>([]);

	async function loadResources() {
		loading = true;
		try {
			const params = new URLSearchParams();
			if (filterCommunity) params.set('community_id', filterCommunity);
			if (filterCategory) params.set('category', filterCategory);
			if (searchQuery.trim()) params.set('q', searchQuery.trim());
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

	function handleSearchInput() {
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(loadResources, 300);
	}

	async function handleCreate(e: Event) {
		e.preventDefault();
		createError = '';
		if (!newCommunityId) {
			createError = 'Please select a community';
			return;
		}
		try {
			await api('/resources', {
				method: 'POST',
				auth: true,
				body: {
					title: newTitle,
					description: newDescription || null,
					category: newCategory,
					condition: newCondition,
					community_id: Number(newCommunityId)
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

	async function loadMyCommunities() {
		try {
			myCommunities = await api<MyCommunity[]>(
				'/communities/my/memberships', { auth: true }
			);
			if (myCommunities.length > 0) {
				newCommunityId = String(myCommunities[0].id);
			}
		} catch {
			myCommunities = [];
		}
	}

	onMount(async () => {
		if ($isLoggedIn) {
			await loadMyCommunities();
		}
		loadResources();
	});

	$effect(() => {
		filterCategory;
		filterCommunity;
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
				{#if myCommunities.length > 0}
					<label>
						<span>Community</span>
						<select bind:value={newCommunityId} required>
							{#each myCommunities as c}
								<option value={c.id}>{c.name} ({c.postal_code})</option>
							{/each}
						</select>
					</label>
				{:else}
					<p class="hint">You need to <a href="/communities">join a community</a> before sharing resources.</p>
				{/if}
				<button type="submit" class="btn-primary" disabled={myCommunities.length === 0}>Share Resource</button>
			</form>
		</div>
	{/if}

	<div class="filter-bar">
		<input
			type="search"
			class="search-input"
			placeholder="Search resources..."
			bind:value={searchQuery}
			oninput={handleSearchInput}
		/>
		<select bind:value={filterCategory}>
			{#each CATEGORIES as cat}
				<option value={cat.value}>{cat.label}</option>
			{/each}
		</select>
		{#if myCommunities.length > 0}
			<select bind:value={filterCommunity}>
				<option value="">All Communities</option>
				{#each myCommunities as c}
					<option value={c.id}>{c.name}</option>
				{/each}
			</select>
		{/if}
		<span class="result-count">{total} result{total !== 1 ? 's' : ''}</span>
	</div>

	{#if loading}
		<p class="loading">Loading resources...</p>
	{:else if resources.length === 0}
		<div class="empty-state">
			<p>No resources found.</p>
			{#if searchQuery || filterCategory}
				<p>Try adjusting your search or filters.</p>
			{:else if $isLoggedIn}
				<p>Be the first to share something with your neighbourhood!</p>
			{:else}
				<p><a href="/register">Sign up</a> to start sharing.</p>
			{/if}
		</div>
	{:else}
		<div class="resource-grid">
			{#each resources as resource}
				<a href="/resources/{resource.id}" class="resource-card">
					{#if resource.image_url && $bandwidth !== 'low'}
						<div class="card-image">
							<img src="/api{resource.image_url}" alt={resource.title} />
						</div>
					{:else}
						<div class="card-image card-image-placeholder">
							<span class="placeholder-icon">{CATEGORY_ICONS[resource.category] ?? '📦'}</span>
						</div>
					{/if}
					<div class="card-body">
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
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>

<style>
	.resources-page {
		max-width: 900px;
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
		color: var(--color-error);
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}

	.hint {
		font-size: 0.85rem;
		color: var(--color-text-muted);
	}

	.filter-bar {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.search-input {
		flex: 1;
		min-width: 0;
	}

	.filter-bar select {
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		font-size: 0.85rem;
		background: var(--color-surface);
		color: var(--color-text);
	}

	.result-count {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		white-space: nowrap;
	}

	.resource-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1rem;
	}

	.resource-card {
		display: flex;
		flex-direction: column;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		text-decoration: none;
		color: var(--color-text);
		transition: border-color 0.15s;
		overflow: hidden;
	}

	.resource-card:hover {
		border-color: var(--color-primary);
		text-decoration: none;
	}

	.card-image {
		width: 100%;
		height: 140px;
		overflow: hidden;
		background: var(--color-bg);
	}

	.card-image img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.card-image-placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.placeholder-icon {
		font-size: 2.5rem;
		opacity: 0.5;
	}

	.card-body {
		padding: 0.75rem 1rem 1rem;
	}

	.card-header {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.35rem;
	}

	.category-badge {
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		background: var(--color-bg);
		padding: 0.1rem 0.45rem;
		border-radius: 999px;
		color: var(--color-primary);
		font-weight: 600;
	}

	.unavailable-badge {
		font-size: 0.7rem;
		background: var(--color-error-bg);
		color: var(--color-error);
		padding: 0.1rem 0.45rem;
		border-radius: 999px;
	}

	.resource-card h3 {
		font-size: 1rem;
		margin-bottom: 0.25rem;
	}

	.description {
		font-size: 0.82rem;
		color: var(--color-text-muted);
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		margin-bottom: 0.4rem;
	}

	.card-footer {
		display: flex;
		justify-content: space-between;
		font-size: 0.78rem;
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
