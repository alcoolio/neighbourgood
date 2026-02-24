<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { isLoggedIn } from '$lib/stores/auth';

	interface SkillOwner {
		display_name: string;
		neighbourhood: string | null;
	}

	interface Skill {
		id: number;
		title: string;
		description: string | null;
		category: string;
		skill_type: string;
		community_id: number | null;
		owner: SkillOwner;
		created_at: string;
	}

	interface MyCommunity {
		id: number;
		name: string;
		postal_code: string;
	}

	const CATEGORIES = [
		{ value: '', label: 'All Categories' },
		{ value: 'tutoring', label: 'Tutoring' },
		{ value: 'repairs', label: 'Repairs' },
		{ value: 'cooking', label: 'Cooking' },
		{ value: 'languages', label: 'Languages' },
		{ value: 'music', label: 'Music' },
		{ value: 'gardening', label: 'Gardening' },
		{ value: 'tech', label: 'Tech' },
		{ value: 'crafts', label: 'Crafts' },
		{ value: 'fitness', label: 'Fitness' },
		{ value: 'other', label: 'Other' }
	];

	const CATEGORY_ICONS: Record<string, string> = {
		tutoring: '📚', repairs: '🔧', cooking: '🍳', languages: '🌐',
		music: '🎵', gardening: '🌱', tech: '💻', crafts: '✂️',
		fitness: '💪', other: '⭐'
	};

	const TYPE_FILTERS = [
		{ value: '', label: 'All Types' },
		{ value: 'offer', label: 'Offers' },
		{ value: 'request', label: 'Requests' }
	];

	let skills: Skill[] = $state([]);
	let total = $state(0);
	let loading = $state(true);
	let filterCategory = $state('');
	let filterType = $state('');
	let filterCommunity = $state('');
	let searchQuery = $state('');
	let searchTimeout: ReturnType<typeof setTimeout> | null = $state(null);
	let showCreateForm = $state(false);

	// Create form
	let newTitle = $state('');
	let newDescription = $state('');
	let newCategory = $state('tutoring');
	let newSkillType = $state('offer');
	let newCommunityId = $state('');
	let createError = $state('');
	let myCommunities = $state<MyCommunity[]>([]);

	async function loadSkills() {
		loading = true;
		try {
			const params = new URLSearchParams();
			if (filterCommunity) params.set('community_id', filterCommunity);
			if (filterCategory) params.set('category', filterCategory);
			if (filterType) params.set('skill_type', filterType);
			if (searchQuery.trim()) params.set('q', searchQuery.trim());
			const res = await api<{ items: Skill[]; total: number }>(
				`/skills?${params.toString()}`
			);
			skills = res.items;
			total = res.total;
		} catch {
			skills = [];
		} finally {
			loading = false;
		}
	}

	function handleSearchInput() {
		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(loadSkills, 300);
	}

	async function handleCreate(e: Event) {
		e.preventDefault();
		createError = '';
		if (!newCommunityId) {
			createError = 'Please select a community';
			return;
		}
		try {
			await api('/skills', {
				method: 'POST',
				auth: true,
				body: {
					title: newTitle,
					description: newDescription || null,
					category: newCategory,
					skill_type: newSkillType,
					community_id: Number(newCommunityId)
				}
			});
			showCreateForm = false;
			newTitle = '';
			newDescription = '';
			await loadSkills();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create skill listing';
		}
	}

	async function loadMyCommunities() {
		try {
			myCommunities = await api<MyCommunity[]>(
				'/communities/my/memberships', { auth: true }
			);
			if (myCommunities.length > 0) {
				filterCommunity = String(myCommunities[0].id);
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
		loadSkills();
	});

	$effect(() => {
		filterCategory;
		filterType;
		filterCommunity;
		loadSkills();
	});
</script>

<div class="skills-page">
	<div class="page-header">
		<h1>Skill Exchange</h1>
		{#if $isLoggedIn}
			<button class="btn-primary" onclick={() => (showCreateForm = !showCreateForm)}>
				{showCreateForm ? 'Cancel' : '+ Share a Skill'}
			</button>
		{/if}
	</div>

	{#if showCreateForm}
		<div class="create-form-card">
			<h2>Share a Skill</h2>
			{#if createError}
				<p class="error">{createError}</p>
			{/if}
			<form onsubmit={handleCreate}>
				<label>
					<span>Title</span>
					<input type="text" bind:value={newTitle} required placeholder="e.g. Piano Lessons" />
				</label>
				<label>
					<span>Description</span>
					<textarea bind:value={newDescription} rows="3" placeholder="What skill are you offering or looking for?"></textarea>
				</label>
				<div class="form-row">
					<label>
						<span>Category</span>
						<select bind:value={newCategory}>
							{#each CATEGORIES.slice(1) as cat}
								<option value={cat.value}>{cat.label}</option>
							{/each}
						</select>
					</label>
					<label>
						<span>Type</span>
						<select bind:value={newSkillType}>
							<option value="offer">I'm offering</option>
							<option value="request">I'm looking for</option>
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
					<p class="hint">You need to <a href="/communities">join a community</a> before sharing skills.</p>
				{/if}
				<button type="submit" class="btn-primary" disabled={myCommunities.length === 0}>Post Skill Listing</button>
			</form>
		</div>
	{/if}

	<div class="filter-bar">
		<input
			type="search"
			class="search-input"
			placeholder="Search skills..."
			bind:value={searchQuery}
			oninput={handleSearchInput}
		/>
		{#if myCommunities.length > 0}
			<select bind:value={filterCommunity}>
				{#each myCommunities as c}
					<option value={c.id}>{c.name}</option>
				{/each}
			</select>
		{/if}
		<select bind:value={filterCategory}>
			{#each CATEGORIES as cat}
				<option value={cat.value}>{cat.label}</option>
			{/each}
		</select>
		<select bind:value={filterType}>
			{#each TYPE_FILTERS as t}
				<option value={t.value}>{t.label}</option>
			{/each}
		</select>
		<span class="result-count">{total} result{total !== 1 ? 's' : ''}</span>
	</div>

	{#if loading}
		<p class="loading">Loading skills...</p>
	{:else if skills.length === 0}
		<div class="empty-state">
			<p>No skill listings found.</p>
			{#if searchQuery || filterCategory || filterType}
				<p>Try adjusting your search or filters.</p>
			{:else if $isLoggedIn}
				<p>Be the first to offer a skill to your neighbourhood!</p>
			{:else}
				<p><a href="/register">Sign up</a> to start exchanging skills.</p>
			{/if}
		</div>
	{:else}
		<div class="skill-grid">
			{#each skills as skill}
				<div class="skill-card">
					<div class="card-icon">
						<span>{CATEGORY_ICONS[skill.category] ?? '⭐'}</span>
					</div>
					<div class="card-body">
						<div class="card-header">
							<span class="category-badge">{skill.category}</span>
							<span class="type-badge" class:type-offer={skill.skill_type === 'offer'} class:type-request={skill.skill_type === 'request'}>
								{skill.skill_type === 'offer' ? 'Offering' : 'Looking for'}
							</span>
						</div>
						<h3>{skill.title}</h3>
						{#if skill.description}
							<p class="description">{skill.description}</p>
						{/if}
						<div class="card-footer">
							<span class="owner">by {skill.owner.display_name}</span>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.skills-page {
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

	.skill-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
	}

	.skill-card {
		display: flex;
		gap: 1rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1rem 1.25rem;
		transition: border-color 0.15s;
	}

	.skill-card:hover {
		border-color: var(--color-primary);
	}

	.card-icon {
		font-size: 1.75rem;
		flex-shrink: 0;
		padding-top: 0.1rem;
	}

	.card-body {
		flex: 1;
		min-width: 0;
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

	.type-badge {
		font-size: 0.7rem;
		padding: 0.1rem 0.45rem;
		border-radius: 999px;
		font-weight: 600;
	}

	.type-offer {
		background: var(--color-success-bg);
		color: var(--color-success);
	}

	.type-request {
		background: var(--color-warning-bg);
		color: var(--color-warning);
	}

	.skill-card h3 {
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
