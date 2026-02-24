<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';
	import { isLoggedIn, user } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	interface SkillOwner {
		id: number;
		display_name: string;
		neighbourhood: string | null;
	}

	interface Skill {
		id: number;
		title: string;
		description: string | null;
		category: string;
		skill_type: string;
		owner_id: number;
		community_id: number | null;
		owner: SkillOwner;
		created_at: string;
		updated_at: string;
	}

	let skill: Skill | null = $state(null);
	let error = $state('');
	let loading = $state(true);

	const isOwner = $derived(
		$isLoggedIn && skill !== null && $user?.id === skill.owner_id
	);

	const CATEGORY_ICONS: Record<string, string> = {
		tutoring: '📚', repairs: '🔧', cooking: '🍳', languages: '🌐',
		music: '🎵', gardening: '🌱', tech: '💻', crafts: '✂️',
		fitness: '💪', other: '⭐'
	};

	onMount(async () => {
		const id = $page.params.id;
		try {
			skill = await api<Skill>(`/skills/${id}`);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Skill not found';
		} finally {
			loading = false;
		}
	});

	async function deleteSkill() {
		if (!skill || !confirm('Delete this skill listing?')) return;
		try {
			await api(`/skills/${skill.id}`, { method: 'DELETE', auth: true });
			goto('/skills');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Delete failed';
		}
	}

	function startConversation(ownerId: number) {
		goto(`/messages?partner=${ownerId}`);
	}
</script>

{#if loading}
	<p class="loading">Loading...</p>
{:else if error}
	<div class="error-page">
		<h1>Oops</h1>
		<p>{error}</p>
		<a href="/skills">Back to skills</a>
	</div>
{:else if skill}
	<article class="skill-detail">
		<a href="/skills" class="back-link">&larr; Back to skills</a>

		<div class="detail-header">
			<div class="icon-section">
				<span class="skill-icon">{CATEGORY_ICONS[skill.category] ?? '⭐'}</span>
			</div>
			<div class="header-content">
				<div class="badges">
					<span class="category-badge">{skill.category}</span>
					<span class="type-badge" class:type-offer={skill.skill_type === 'offer'} class:type-request={skill.skill_type === 'request'}>
						{skill.skill_type === 'offer' ? 'Offering' : 'Looking for'}
					</span>
				</div>
				<h1>{skill.title}</h1>
			</div>
		</div>

		{#if skill.description}
			<div class="section-card">
				<h3>About</h3>
				<p>{skill.description}</p>
			</div>
		{/if}

		<div class="owner-section">
			<h3>Listed by</h3>
			<p class="owner-name">{skill.owner.display_name}</p>
			{#if skill.owner.neighbourhood}
				<p class="owner-neighbourhood">{skill.owner.neighbourhood}</p>
			{/if}
			{#if $isLoggedIn && $user?.id !== skill.owner_id}
				<button class="btn-message-owner" onclick={() => startConversation(skill!.owner_id)}>
					Message {skill.skill_type === 'offer' ? 'Tutor' : 'Requester'}
				</button>
			{/if}
		</div>

		<div class="meta">
			<span>Listed {new Date(skill.created_at).toLocaleDateString()}</span>
		</div>

		<!-- Owner actions -->
		{#if isOwner}
			<div class="section-card owner-panel">
				<h3>Manage Skill</h3>
				<div class="owner-actions">
					<button class="btn-danger" onclick={deleteSkill}>Delete Listing</button>
				</div>
			</div>
		{/if}
	</article>
{/if}

<style>
	.back-link {
		font-size: 0.9rem;
		color: var(--color-text-muted);
		text-decoration: none;
		display: inline-block;
		margin-bottom: 1rem;
	}

	.back-link:hover {
		color: var(--color-primary);
	}

	.skill-detail {
		max-width: 680px;
	}

	.detail-header {
		display: flex;
		gap: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.icon-section {
		flex-shrink: 0;
	}

	.skill-icon {
		font-size: 3rem;
		display: block;
	}

	.header-content {
		flex: 1;
	}

	.detail-header h1 {
		font-size: 1.75rem;
		margin-top: 0.5rem;
	}

	.badges {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.category-badge, .type-badge {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 0.2rem 0.6rem;
		border-radius: 999px;
		font-weight: 600;
	}

	.category-badge {
		background: var(--color-bg);
		color: var(--color-primary);
	}

	.type-badge {
		color: white;
	}

	.type-offer {
		background: var(--color-success);
	}

	.type-request {
		background: var(--color-warning);
	}

	.section-card {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.25rem;
		margin-bottom: 1.25rem;
	}

	.section-card p {
		line-height: 1.7;
		white-space: pre-wrap;
	}

	.section-card h3 {
		font-size: 0.85rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
		margin-bottom: 0.75rem;
	}

	.owner-section {
		margin-bottom: 1rem;
	}

	.owner-section h3 {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
		margin-bottom: 0.25rem;
	}

	.owner-name {
		font-weight: 600;
	}

	.owner-neighbourhood {
		font-size: 0.9rem;
		color: var(--color-text-muted);
	}

	.btn-message-owner {
		margin-top: 0.5rem;
		padding: 0.4rem 0.9rem;
		background: var(--color-surface);
		border: 1px solid var(--color-primary);
		border-radius: var(--radius);
		color: var(--color-primary);
		font-size: 0.85rem;
		font-weight: 500;
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-message-owner:hover {
		background: var(--color-primary);
		color: white;
	}

	.meta {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		margin-bottom: 1.25rem;
	}

	.owner-panel {
		background: var(--color-bg);
	}

	.owner-actions {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.btn-danger {
		padding: 0.5rem 1rem;
		border: 1px solid var(--color-error);
		border-radius: var(--radius);
		background: var(--color-error-bg);
		color: var(--color-error);
		cursor: pointer;
		font-size: 0.9rem;
	}

	.btn-danger:hover {
		background: var(--color-error);
		color: white;
	}

	.error {
		color: var(--color-error);
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}

	.loading {
		color: var(--color-text-muted);
	}

	.error-page {
		text-align: center;
		padding: 3rem 1rem;
	}

	.error-page h1 {
		color: var(--color-error);
	}
</style>
