<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';
	import { isLoggedIn, user } from '$lib/stores/auth';

	interface UserInfo {
		id: number;
		display_name: string;
		email: string;
	}

	interface Conversation {
		partner: UserInfo;
		last_message_body: string;
		last_message_at: string;
		unread_count: number;
	}

	interface Message {
		id: number;
		sender_id: number;
		sender: UserInfo;
		recipient_id: number;
		recipient: UserInfo;
		booking_id: number | null;
		body: string;
		is_read: boolean;
		created_at: string;
	}

	let conversations: Conversation[] = $state([]);
	let messages: Message[] = $state([]);
	let selectedPartner: UserInfo | null = $state(null);
	let loading = $state(true);
	let newMessage = $state('');
	let sending = $state(false);

	async function loadConversations() {
		loading = true;
		try {
			conversations = await api<Conversation[]>('/messages/conversations', { auth: true });
		} catch {
			conversations = [];
		} finally {
			loading = false;
		}
	}

	async function openConversation(partner: UserInfo) {
		selectedPartner = partner;
		try {
			const res = await api<{ items: Message[]; total: number }>(
				`/messages?partner_id=${partner.id}`,
				{ auth: true }
			);
			messages = res.items.reverse();

			// Mark conversation as read
			await api(`/messages/conversation/${partner.id}/read`, {
				method: 'POST',
				auth: true
			});

			// Refresh unread counts
			const conv = conversations.find(c => c.partner.id === partner.id);
			if (conv) conv.unread_count = 0;
		} catch {
			messages = [];
		}
	}

	async function sendMessage() {
		if (!newMessage.trim() || !selectedPartner || sending) return;
		sending = true;
		try {
			const msg = await api<Message>('/messages', {
				method: 'POST',
				auth: true,
				body: {
					recipient_id: selectedPartner.id,
					body: newMessage.trim()
				}
			});
			messages = [...messages, msg];
			newMessage = '';
			await loadConversations();
		} catch (err) {
			alert(err instanceof Error ? err.message : 'Failed to send');
		} finally {
			sending = false;
		}
	}

	function formatTime(iso: string): string {
		const d = new Date(iso);
		const now = new Date();
		if (d.toDateString() === now.toDateString()) {
			return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
		}
		return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	onMount(async () => {
		await loadConversations();
		const partnerId = $page.url.searchParams.get('partner');
		if (partnerId) {
			const pid = Number(partnerId);
			const existing = conversations.find(c => c.partner.id === pid);
			if (existing) {
				openConversation(existing.partner);
			} else {
				// New conversation – get display name from reputation endpoint
				try {
					const rep = await api<{ user_id: number; display_name: string }>(
						`/users/${pid}/reputation`
					);
					selectedPartner = { id: pid, display_name: rep.display_name, email: '' };
				} catch {
					selectedPartner = { id: pid, display_name: 'User', email: '' };
				}
				messages = [];
			}
		}
	});
</script>

{#if !$isLoggedIn}
	<div class="empty-state">
		<p>Please <a href="/login">log in</a> to view your messages.</p>
	</div>
{:else}
	<div class="messages-page">
		<h1>Messages</h1>

		<div class="messages-layout">
			<!-- Conversation list -->
			<div class="conv-list">
				{#if loading}
					<p class="loading">Loading...</p>
				{:else if conversations.length === 0}
					<p class="empty-text">No conversations yet.</p>
				{:else}
					{#each conversations as conv}
						<button
							class="conv-item"
							class:active={selectedPartner?.id === conv.partner.id}
							onclick={() => openConversation(conv.partner)}
						>
							<div class="conv-header">
								<span class="conv-name">{conv.partner.display_name}</span>
								<span class="conv-time">{formatTime(conv.last_message_at)}</span>
							</div>
							<div class="conv-preview">
								<span class="conv-body">{conv.last_message_body}</span>
								{#if conv.unread_count > 0}
									<span class="unread-badge">{conv.unread_count}</span>
								{/if}
							</div>
						</button>
					{/each}
				{/if}
			</div>

			<!-- Message thread -->
			<div class="thread">
				{#if !selectedPartner}
					<div class="thread-empty">
						<p>Select a conversation to view messages.</p>
					</div>
				{:else}
					<div class="thread-header">
						<strong>{selectedPartner.display_name}</strong>
					</div>
					<div class="thread-messages">
						{#each messages as msg}
							<div
								class="msg-bubble"
								class:sent={msg.sender_id === $user?.id}
								class:received={msg.sender_id !== $user?.id}
							>
								<p class="msg-body">{msg.body}</p>
								<span class="msg-time">{formatTime(msg.created_at)}</span>
							</div>
						{/each}
					</div>
					<div class="thread-input">
						<textarea
							bind:value={newMessage}
							placeholder="Type a message..."
							rows="2"
							onkeydown={handleKeydown}
						></textarea>
						<button
							class="send-btn"
							onclick={sendMessage}
							disabled={sending || !newMessage.trim()}
						>
							Send
						</button>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.messages-page {
		max-width: 900px;
	}

	h1 {
		font-size: 1.75rem;
		margin-bottom: 1rem;
	}

	.messages-layout {
		display: grid;
		grid-template-columns: 280px 1fr;
		gap: 1px;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		overflow: hidden;
		height: 500px;
	}

	.conv-list {
		background: var(--color-surface);
		border-right: 1px solid var(--color-border);
		overflow-y: auto;
	}

	.conv-item {
		display: block;
		width: 100%;
		text-align: left;
		padding: 0.75rem 1rem;
		border: none;
		border-bottom: 1px solid var(--color-border);
		background: var(--color-surface);
		cursor: pointer;
		font-size: 0.85rem;
		color: var(--color-text);
	}

	.conv-item:hover {
		background: var(--color-primary-light);
	}

	.conv-item.active {
		background: var(--color-primary-light);
	}

	.conv-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.2rem;
	}

	.conv-name {
		font-weight: 600;
		font-size: 0.9rem;
	}

	.conv-time {
		font-size: 0.75rem;
		color: var(--color-text-muted);
	}

	.conv-preview {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.conv-body {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--color-text-muted);
		flex: 1;
	}

	.unread-badge {
		background: var(--color-primary);
		color: white;
		font-size: 0.7rem;
		font-weight: 700;
		border-radius: 10px;
		padding: 0.1rem 0.45rem;
		margin-left: 0.5rem;
	}

	.thread {
		display: flex;
		flex-direction: column;
		background: var(--color-bg);
	}

	.thread-empty {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: var(--color-text-muted);
	}

	.thread-header {
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--color-border);
		background: var(--color-surface);
	}

	.thread-messages {
		flex: 1;
		overflow-y: auto;
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.msg-bubble {
		max-width: 70%;
		padding: 0.5rem 0.75rem;
		border-radius: 12px;
		font-size: 0.88rem;
	}

	.msg-bubble.sent {
		align-self: flex-end;
		background: var(--color-primary);
		color: white;
	}

	.msg-bubble.received {
		align-self: flex-start;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
	}

	.msg-body {
		margin: 0;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.msg-time {
		display: block;
		font-size: 0.7rem;
		margin-top: 0.2rem;
		opacity: 0.7;
	}

	.msg-bubble.sent .msg-time {
		text-align: right;
	}

	.thread-input {
		display: flex;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		border-top: 1px solid var(--color-border);
		background: var(--color-surface);
	}

	.thread-input textarea {
		flex: 1;
		resize: none;
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 0.5rem;
		font-size: 0.85rem;
		font-family: inherit;
	}

	.send-btn {
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: var(--radius);
		padding: 0.5rem 1rem;
		cursor: pointer;
		font-size: 0.85rem;
		align-self: flex-end;
	}

	.send-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.send-btn:not(:disabled):hover {
		background: var(--color-primary-hover);
	}

	.loading, .empty-text {
		padding: 1.5rem;
		text-align: center;
		color: var(--color-text-muted);
		font-size: 0.85rem;
	}

	.empty-state {
		text-align: center;
		padding: 3rem 1rem;
		color: var(--color-text-muted);
	}
</style>
