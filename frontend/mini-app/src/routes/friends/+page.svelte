<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import { api, type Friend } from '$lib/api/client';

	let friends: Friend[] = $state([]);
	let requests: Friend[] = $state([]);
	let isLoading = $state(true);
	let showAddForm = $state(false);
	let addUsername = $state('');
	let addError = $state('');
	let activeTab: 'friends' | 'requests' = $state('friends');

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		try {
			[friends, requests] = await Promise.all([
				api.getFriends(),
				api.getFriendRequests(),
			]);
		} catch (error) {
			console.error('Failed to load friends:', error);
		} finally {
			isLoading = false;
		}
	}

	async function addFriend() {
		if (!addUsername.trim()) return;

		addError = '';
		try {
			await api.addFriend(addUsername.trim());
			addUsername = '';
			showAddForm = false;

			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
			}
		} catch (error: any) {
			addError = error.message || 'Ошибка';
		}
	}

	async function acceptRequest(id: number) {
		try {
			await api.acceptFriend(id);
			await loadData();

			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
			}
		} catch (error) {
			console.error('Failed to accept friend:', error);
		}
	}

	async function rejectRequest(id: number) {
		try {
			await api.rejectFriend(id);
			requests = requests.filter(r => r.id !== id);

			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
			}
		} catch (error) {
			console.error('Failed to reject friend:', error);
		}
	}

	async function removeFriend(userId: number) {
		try {
			await api.removeFriend(userId);
			friends = friends.filter(f => f.user_id !== userId);

			if (browser) {
				window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
			}
		} catch (error) {
			console.error('Failed to remove friend:', error);
		}
	}
</script>

<div class="container">
	<header class="page-header">
		<h1 class="pixel-title">👥 ДРУЗЬЯ</h1>
	</header>

	{#if showAddForm}
		<!-- Add Friend Form -->
		<div class="add-form pixel-card">
			<div class="form-title">ДОБАВИТЬ ДРУГА</div>

			<div class="form-group">
				<label>USERNAME</label>
				<input
					type="text"
					bind:value={addUsername}
					placeholder="@username"
					class="pixel-input"
				/>
			</div>

			{#if addError}
				<div class="error-text">{addError}</div>
			{/if}

			<div class="form-actions">
				<button class="pixel-btn" onclick={() => { showAddForm = false; addError = ''; }}>
					ОТМЕНА
				</button>
				<button class="pixel-btn secondary" onclick={addFriend}>
					ДОБАВИТЬ
				</button>
			</div>
		</div>
	{:else}
		<button class="pixel-btn accent w-full mb-md" onclick={() => showAddForm = true}>
			+ ДОБАВИТЬ ДРУГА
		</button>
	{/if}

	<!-- Tabs -->
	<div class="tabs">
		<button
			class="tab-btn"
			class:active={activeTab === 'friends'}
			onclick={() => activeTab = 'friends'}
		>
			ДРУЗЬЯ ({friends.length})
		</button>
		<button
			class="tab-btn"
			class:active={activeTab === 'requests'}
			onclick={() => activeTab = 'requests'}
		>
			ЗАПРОСЫ ({requests.length})
		</button>
	</div>

	{#if isLoading}
		<div class="loading">
			<div class="loading-icon">👥</div>
			<div class="loading-text">Загрузка...</div>
		</div>
	{:else if activeTab === 'friends'}
		<!-- Friends List -->
		{#if friends.length === 0}
			<div class="empty-state">
				<div class="empty-icon">😢</div>
				<div class="empty-text">У тебя пока нет друзей</div>
				<div class="empty-hint">Добавь первого друга!</div>
			</div>
		{:else}
			<div class="friends-list">
				{#each friends as friend}
					<div class="friend-card pixel-card">
						<div class="friend-avatar">⚔️</div>
						<div class="friend-info">
							<div class="friend-name">
								{friend.first_name || friend.username || 'Воин'}
							</div>
							<div class="friend-stats">
								<span class="level-badge-sm">LVL {friend.level}</span>
								<span class="streak-badge">🔥 {friend.streak_days}</span>
								<span class="workouts-badge">💪 {friend.total_workouts}</span>
							</div>
						</div>
						<button class="remove-btn" onclick={() => removeFriend(friend.user_id)}>✕</button>
					</div>
				{/each}
			</div>
		{/if}
	{:else}
		<!-- Requests List -->
		{#if requests.length === 0}
			<div class="empty-state">
				<div class="empty-icon">📭</div>
				<div class="empty-text">Нет входящих запросов</div>
			</div>
		{:else}
			<div class="requests-list">
				{#each requests as request}
					<div class="request-card pixel-card">
						<div class="friend-avatar">⚔️</div>
						<div class="friend-info">
							<div class="friend-name">
								{request.first_name || request.username || 'Воин'}
							</div>
							<div class="friend-stats">
								<span class="level-badge-sm">LVL {request.level}</span>
							</div>
						</div>
						<div class="request-actions">
							<button class="accept-btn" onclick={() => acceptRequest(request.id)}>✓</button>
							<button class="reject-btn" onclick={() => rejectRequest(request.id)}>✕</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.page-header {
		text-align: center;
		margin-bottom: var(--space-lg);
	}

	.add-form {
		margin-bottom: var(--space-lg);
	}

	.form-title {
		font-size: 12px;
		color: var(--accent);
		text-align: center;
		margin-bottom: var(--space-lg);
	}

	.form-group {
		margin-bottom: var(--space-lg);
	}

	.form-group label {
		display: block;
		font-size: 8px;
		color: var(--text-muted);
		margin-bottom: var(--space-sm);
	}

	.pixel-input {
		width: 100%;
		padding: var(--space-md);
		background: var(--bg-dark);
		border: 4px solid var(--border);
		color: var(--text-primary);
		font-family: 'Press Start 2P', monospace;
		font-size: 9px;
	}

	.pixel-input::placeholder {
		color: var(--text-muted);
	}

	.error-text {
		font-size: 8px;
		color: var(--primary);
		text-align: center;
		margin-bottom: var(--space-md);
	}

	.form-actions {
		display: flex;
		gap: var(--space-md);
		justify-content: center;
	}

	.tabs {
		display: flex;
		gap: var(--space-sm);
		margin-bottom: var(--space-lg);
	}

	.tab-btn {
		flex: 1;
		padding: var(--space-md);
		background: var(--bg-card);
		border: 4px solid var(--border);
		color: var(--text-secondary);
		font-family: 'Press Start 2P', monospace;
		font-size: 8px;
		cursor: pointer;
	}

	.tab-btn.active {
		border-color: var(--accent);
		color: var(--accent);
	}

	.loading, .empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 30vh;
		text-align: center;
	}

	.loading-icon, .empty-icon {
		font-size: 48px;
		margin-bottom: var(--space-md);
	}

	.loading-icon {
		animation: bounce 1s infinite;
	}

	.loading-text, .empty-text {
		font-size: 10px;
		color: var(--text-muted);
	}

	.empty-hint {
		font-size: 8px;
		color: var(--text-muted);
		margin-top: var(--space-sm);
	}

	.friends-list, .requests-list {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.friend-card, .request-card {
		display: flex;
		align-items: center;
		gap: var(--space-md);
	}

	.friend-avatar {
		width: 48px;
		height: 48px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--bg-dark);
		border: 2px solid var(--border);
		font-size: 24px;
	}

	.friend-info {
		flex: 1;
	}

	.friend-name {
		font-size: 10px;
		color: var(--text-primary);
	}

	.friend-stats {
		display: flex;
		gap: var(--space-sm);
		margin-top: var(--space-xs);
	}

	.level-badge-sm {
		font-size: 7px;
		background: var(--accent);
		color: var(--bg-dark);
		padding: 2px 4px;
	}

	.streak-badge {
		font-size: 7px;
		color: var(--warning);
	}

	.workouts-badge {
		font-size: 7px;
		color: var(--text-muted);
	}

	.remove-btn, .reject-btn {
		width: 28px;
		height: 28px;
		background: var(--bg-dark);
		border: 2px solid var(--primary);
		color: var(--primary);
		cursor: pointer;
		font-size: 12px;
	}

	.accept-btn {
		width: 28px;
		height: 28px;
		background: var(--secondary);
		border: 2px solid var(--secondary);
		color: var(--bg-dark);
		cursor: pointer;
		font-size: 12px;
	}

	.request-actions {
		display: flex;
		gap: var(--space-xs);
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-10px); }
	}
</style>
