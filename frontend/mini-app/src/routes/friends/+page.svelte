<script lang="ts">
	import { onMount } from 'svelte';
	import { PixelCard, PixelButton, PixelIcon, PixelAvatar } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Friend } from '$lib/types';

	let friends = $state<Friend[]>([]);
	let friendRequests = $state<Friend[]>([]);
	let searchResults = $state<Friend[]>([]);
	let searchQuery = $state('');
	let isLoading = $state(true);
	let isSearching = $state(false);
	let activeTab = $state<'friends' | 'requests' | 'search'>('friends');
	let error = $state<string | null>(null);

	onMount(async () => {
		await loadFriends();
	});

	async function loadFriends() {
		isLoading = true;
		error = null;
		try {
			[friends, friendRequests] = await Promise.all([
				api.getFriends(),
				api.getFriendRequests()
			]);
		} catch (err) {
			error = 'Не удалось загрузить друзей';
			console.error(err);
		} finally {
			isLoading = false;
		}
	}

	async function searchUsers() {
		if (searchQuery.length < 2) return;

		isSearching = true;
		error = null;
		try {
			searchResults = await api.searchUsers(searchQuery);
		} catch (err) {
			error = 'Ошибка поиска';
			console.error(err);
		} finally {
			isSearching = false;
		}
	}

	async function addFriend(username: string) {
		telegram.hapticImpact('medium');
		try {
			await api.addFriend(username);
			// Update search results to show pending status
			searchResults = searchResults.map(u =>
				u.username === username ? { ...u, status: 'pending' as const } : u
			);
			telegram.hapticNotification('success');
		} catch (err) {
			telegram.hapticNotification('error');
			error = 'Не удалось отправить заявку';
		}
	}

	async function acceptRequest(friendshipId: number) {
		telegram.hapticImpact('medium');
		try {
			const newFriend = await api.acceptFriendRequest(friendshipId);
			friendRequests = friendRequests.filter(r => r.id !== friendshipId);
			friends = [...friends, newFriend];
			telegram.hapticNotification('success');
		} catch (err) {
			telegram.hapticNotification('error');
			error = 'Не удалось принять заявку';
		}
	}

	async function removeFriend(friendshipId: number) {
		telegram.hapticImpact('light');
		try {
			await api.removeFriend(friendshipId);
			friends = friends.filter(f => f.id !== friendshipId);
			friendRequests = friendRequests.filter(r => r.id !== friendshipId);
			telegram.hapticNotification('success');
		} catch (err) {
			telegram.hapticNotification('error');
			error = 'Не удалось удалить';
		}
	}

	function switchTab(tab: 'friends' | 'requests' | 'search') {
		activeTab = tab;
		telegram.hapticImpact('light');
		if (tab === 'search') {
			searchResults = [];
			searchQuery = '';
		}
	}

	function handleSearchInput(e: Event) {
		searchQuery = (e.target as HTMLInputElement).value;
	}

	function handleSearchKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			searchUsers();
		}
	}
</script>

<div class="page container">
	<header class="page-header">
		<h1>Друзья</h1>
	</header>

	<!-- Tabs -->
	<div class="tabs">
		<button
			class="tab"
			class:active={activeTab === 'friends'}
			onclick={() => switchTab('friends')}
		>
			Друзья ({friends.length})
		</button>
		<button
			class="tab"
			class:active={activeTab === 'requests'}
			onclick={() => switchTab('requests')}
		>
			Заявки
			{#if friendRequests.length > 0}
				<span class="badge">{friendRequests.length}</span>
			{/if}
		</button>
		<button
			class="tab"
			class:active={activeTab === 'search'}
			onclick={() => switchTab('search')}
		>
			Поиск
		</button>
	</div>

	{#if error}
		<div class="error-message">
			<PixelIcon name="warning" size="sm" color="var(--pixel-red)" />
			<span>{error}</span>
		</div>
	{/if}

	<!-- Search Tab -->
	{#if activeTab === 'search'}
		<div class="search-section">
			<div class="search-box">
				<input
					type="text"
					placeholder="Введите @username..."
					value={searchQuery}
					oninput={handleSearchInput}
					onkeydown={handleSearchKeydown}
					class="search-input"
				/>
				<PixelButton
					size="sm"
					onclick={searchUsers}
					disabled={searchQuery.length < 2 || isSearching}
				>
					{isSearching ? '...' : 'Найти'}
				</PixelButton>
			</div>

			<p class="search-hint">Минимум 2 символа для поиска</p>

			{#if searchResults.length > 0}
				<div class="user-list">
					{#each searchResults as user}
						<PixelCard padding="sm">
							<div class="user-item">
								<PixelAvatar avatarId={user.avatar_id} size="md" />
								<div class="user-info">
									<span class="user-name">{user.first_name}</span>
									{#if user.username}
										<span class="user-username">@{user.username}</span>
									{/if}
									<span class="user-level">Ур.{user.level}</span>
								</div>
								<div class="user-action">
									{#if user.status === 'accepted'}
										<span class="status-badge accepted">Друг</span>
									{:else if user.status === 'pending'}
										<span class="status-badge pending">Отправлено</span>
									{:else if user.username}
										<PixelButton
											size="sm"
											variant="primary"
											onclick={() => addFriend(user.username!)}
										>
											Добавить
										</PixelButton>
									{/if}
								</div>
							</div>
						</PixelCard>
					{/each}
				</div>
			{:else if searchQuery.length >= 2 && !isSearching}
				<div class="empty-state">
					<PixelIcon name="search" size="xl" color="var(--text-muted)" />
					<p>Пользователи не найдены</p>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Friends Tab -->
	{#if activeTab === 'friends'}
		{#if isLoading}
			<div class="loading">
				<div class="pixel-spinner"></div>
				<span>Загрузка...</span>
			</div>
		{:else if friends.length === 0}
			<div class="empty-state">
				<PixelIcon name="friends" size="xl" color="var(--text-muted)" />
				<p>У вас пока нет друзей</p>
				<p class="empty-hint">Найдите друзей по @username</p>
				<PixelButton onclick={() => switchTab('search')}>
					Найти друзей
				</PixelButton>
			</div>
		{:else}
			<div class="user-list">
				{#each friends as friend}
					<PixelCard padding="sm">
						<div class="user-item">
							<PixelAvatar avatarId={friend.avatar_id} size="md" />
							<div class="user-info">
								<span class="user-name">{friend.first_name}</span>
								{#if friend.username}
									<span class="user-username">@{friend.username}</span>
								{/if}
								<div class="user-stats">
									<span>Ур.{friend.level}</span>
									<span class="streak">
										<PixelIcon name="streak" size="sm" color="var(--pixel-yellow)" />
										{friend.current_streak}
									</span>
								</div>
							</div>
							<button class="remove-btn" onclick={() => removeFriend(friend.id)}>
								<PixelIcon name="close" size="sm" color="var(--text-muted)" />
							</button>
						</div>
					</PixelCard>
				{/each}
			</div>
		{/if}
	{/if}

	<!-- Requests Tab -->
	{#if activeTab === 'requests'}
		{#if isLoading}
			<div class="loading">
				<div class="pixel-spinner"></div>
				<span>Загрузка...</span>
			</div>
		{:else if friendRequests.length === 0}
			<div class="empty-state">
				<PixelIcon name="mail" size="xl" color="var(--text-muted)" />
				<p>Нет входящих заявок</p>
			</div>
		{:else}
			<div class="user-list">
				{#each friendRequests as request}
					<PixelCard padding="sm">
						<div class="user-item">
							<PixelAvatar avatarId={request.avatar_id} size="md" />
							<div class="user-info">
								<span class="user-name">{request.first_name}</span>
								{#if request.username}
									<span class="user-username">@{request.username}</span>
								{/if}
								<span class="user-level">Ур.{request.level}</span>
							</div>
							<div class="request-actions">
								<PixelButton
									size="sm"
									variant="primary"
									onclick={() => acceptRequest(request.id)}
								>
									Принять
								</PixelButton>
								<button class="remove-btn" onclick={() => removeFriend(request.id)}>
									<PixelIcon name="close" size="sm" color="var(--text-muted)" />
								</button>
							</div>
						</div>
					</PixelCard>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	.page-header {
		text-align: center;
		margin-bottom: var(--spacing-md);
	}

	/* Tabs */
	.tabs {
		display: flex;
		gap: var(--spacing-xs);
		margin-bottom: var(--spacing-lg);
	}

	.tab {
		flex: 1;
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all var(--transition-fast);
		position: relative;
	}

	.tab:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.tab.active {
		background: var(--pixel-accent);
		border-color: var(--pixel-accent-hover);
		color: var(--text-primary);
	}

	.badge {
		position: absolute;
		top: -4px;
		right: -4px;
		min-width: 16px;
		height: 16px;
		padding: 0 4px;
		font-size: 8px;
		background: var(--pixel-red);
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* Error */
	.error-message {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm);
		background: rgba(232, 68, 68, 0.1);
		border: 2px solid var(--pixel-red);
		margin-bottom: var(--spacing-md);
		font-size: var(--font-size-xs);
		color: var(--pixel-red);
	}

	/* Search */
	.search-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.search-box {
		display: flex;
		gap: var(--spacing-sm);
	}

	.search-input {
		flex: 1;
		padding: var(--spacing-sm);
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		color: var(--text-primary);
		outline: none;
	}

	.search-input:focus {
		border-color: var(--pixel-accent);
	}

	.search-input::placeholder {
		color: var(--text-muted);
	}

	.search-hint {
		font-size: var(--font-size-xs);
		color: var(--text-muted);
		text-align: center;
	}

	/* User List */
	.user-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.user-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.user-info {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}

	.user-name {
		font-size: var(--font-size-sm);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.user-username {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.user-level {
		font-size: 8px;
		color: var(--text-muted);
	}

	.user-stats {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		font-size: 8px;
		color: var(--text-muted);
	}

	.streak {
		display: flex;
		align-items: center;
		gap: 2px;
		color: var(--pixel-yellow);
	}

	.user-action {
		flex-shrink: 0;
	}

	.status-badge {
		padding: 4px 8px;
		font-size: 8px;
		text-transform: uppercase;
	}

	.status-badge.accepted {
		background: var(--pixel-green);
		color: var(--text-primary);
	}

	.status-badge.pending {
		background: var(--pixel-yellow);
		color: var(--pixel-black);
	}

	.request-actions {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.remove-btn {
		background: none;
		border: none;
		padding: var(--spacing-xs);
		cursor: pointer;
		opacity: 0.6;
		transition: opacity var(--transition-fast);
	}

	.remove-btn:hover {
		opacity: 1;
	}

	/* Loading */
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-secondary);
		font-size: var(--font-size-sm);
		text-transform: uppercase;
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-muted);
		font-size: var(--font-size-sm);
		text-align: center;
	}

	.empty-hint {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}
</style>
