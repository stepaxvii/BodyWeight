<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { PixelCard, PixelButton, PixelIcon, PixelAvatar, EmptyState, PixelTabs } from '$lib/components/ui';
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

	// Confirmation dialog state
	let confirmRemove = $state<{ id: number; name: string; isRequest: boolean } | null>(null);

	// Debounce timer for search
	let searchTimeout: ReturnType<typeof setTimeout> | null = null;

	onMount(async () => {
		// Check URL parameter for initial tab
		const tabParam = $page.url.searchParams.get('tab');
		if (tabParam === 'requests') {
			activeTab = 'requests';
		} else if (tabParam === 'search') {
			activeTab = 'search';
		}

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
		if (searchQuery.length < 2) {
			searchResults = [];
			return;
		}

		isSearching = true;
		error = null;
		try {
			searchResults = await api.searchUsers(searchQuery);
		} catch (err) {
			error = 'Ошибка поиска';
			console.error(err);
			searchResults = [];
		} finally {
			isSearching = false;
		}
	}

	async function shareInviteLink() {
		try {
			telegram.hapticImpact('medium');

			const botUsername = 'pixelfitbot';
			const botLink = `https://t.me/${botUsername}`;

			const inviteText = `PixelFit - 8-bit фитнес трекер! Набирай опыт, прокачивай уровень, открывай достижения. Присоединяйся!`;

			// Try Telegram share if inside TMA
			if (telegram.webApp) {
				const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(botLink)}&text=${encodeURIComponent(inviteText)}`;
				telegram.openTelegramLink(shareUrl);
			} else if (navigator.share) {
				// Browser: native Web Share API
				await navigator.share({ title: 'PixelFit', text: inviteText, url: botLink });
			} else {
				// Fallback: copy to clipboard
				await navigator.clipboard.writeText(`${inviteText}\n${botLink}`);
				error = null;
				alert('Ссылка скопирована в буфер обмена');
			}

			telegram.hapticNotification('success');
		} catch (err) {
			// User cancelled share — not an error
			if (err instanceof Error && err.name === 'AbortError') return;
			telegram.hapticNotification('error');
			console.error('Failed to share invite link:', err);
		}
	}

	// Auto-search with debounce when searchQuery changes
	$effect(() => {
		// Clear previous timeout
		if (searchTimeout) {
			clearTimeout(searchTimeout);
			searchTimeout = null;
		}

		// Only search if we're on the search tab
		if (activeTab !== 'search') {
			return;
		}

		// If query is too short, clear results
		if (searchQuery.length < 2) {
			searchResults = [];
			return;
		}

		// Debounce search by 400ms
		searchTimeout = setTimeout(() => {
			searchUsers();
			searchTimeout = null;
		}, 400);

		// Cleanup function
		return () => {
			if (searchTimeout) {
				clearTimeout(searchTimeout);
				searchTimeout = null;
			}
		};
	});

	async function addFriend(usernameOrId: string | number) {
		telegram.hapticImpact('medium');
		try {
			await api.addFriend(usernameOrId);

			// Update search results to show pending status
			if (typeof usernameOrId === 'string') {
				searchResults = searchResults.map(u =>
					u.username === usernameOrId ? { ...u, status: 'pending' as const } : u
				);
			} else {
				searchResults = searchResults.map(u =>
					u.user_id === usernameOrId ? { ...u, status: 'pending' as const } : u
				);
			}

			telegram.hapticNotification('success');
			telegram.showAlert('Заявка отправлена');
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

	function showRemoveConfirmation(friendshipId: number, name: string, isRequest: boolean = false) {
		confirmRemove = { id: friendshipId, name, isRequest };
		telegram.hapticImpact('light');
	}

	function cancelRemove() {
		confirmRemove = null;
	}

	async function confirmRemoveFriend() {
		if (!confirmRemove) return;

		telegram.hapticImpact('medium');
		try {
			await api.removeFriend(confirmRemove.id);
			friends = friends.filter(f => f.id !== confirmRemove!.id);
			friendRequests = friendRequests.filter(r => r.id !== confirmRemove!.id);
			telegram.hapticNotification('success');
		} catch (err) {
			telegram.hapticNotification('error');
			error = 'Не удалось удалить';
		} finally {
			confirmRemove = null;
		}
	}

	function switchTab(tab: 'friends' | 'requests' | 'search') {
		activeTab = tab;
		if (tab === 'search') {
			searchResults = [];
			searchQuery = '';
		}
	}

	const friendTabs = $derived.by(() => [
		{ id: 'friends' as const, label: `Друзья (${friends.length})` },
		{ id: 'requests' as const, label: 'Заявки', badge: friendRequests.length },
		{ id: 'search' as const, label: 'Поиск' }
	]);

	function handleSearchInput(e: Event) {
		searchQuery = (e.target as HTMLInputElement).value;
		// Search is now automatic via $effect, but we can keep Enter for immediate search
	}

	function handleSearchKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			// Clear debounce and search immediately
			if (searchTimeout) {
				clearTimeout(searchTimeout);
			}
			searchUsers();
		}
	}
</script>

<div class="page container">
	<header class="page-header">
		<h1>Друзья</h1>
	</header>

	<!-- Tabs -->
	<PixelTabs tabs={friendTabs} activeTab={activeTab} onTabChange={switchTab} />

	{#if error}
		<div class="error-message">
			<PixelIcon name="warning" size="sm" color="var(--pixel-red)" />
			<span>{error}</span>
		</div>
	{/if}

	<!-- Search Tab -->
	{#if activeTab === 'search'}
		<div class="search-section">
			<!-- Invite Link Button -->
			<PixelCard padding="sm" style="margin-bottom: 16px;">
				<div class="invite-link-section">
					<div class="invite-info">
						<PixelIcon name="link" size="sm" color="var(--primary)" />
						<span>Пригласить друга</span>
					</div>
					<PixelButton size="sm" variant="secondary" onclick={shareInviteLink}>
						<PixelIcon name="share" />
						Поделиться приглашением
					</PixelButton>
				</div>
			</PixelCard>

			<div class="search-box">
				<input
					type="text"
					placeholder="Введите username..."
					value={searchQuery}
					oninput={handleSearchInput}
					onkeydown={handleSearchKeydown}
					class="search-input"
				/>
				{#if searchQuery}
					<button class="clear-search-btn" onclick={() => searchQuery = ''}>
						<PixelIcon name="close" size="sm" />
					</button>
				{:else}
					<PixelIcon name="search" size="sm" color="var(--text-secondary)" class="search-icon" />
				{/if}
			</div>

			<p class="search-hint">
				{#if isSearching}
					Поиск...
				{:else if searchQuery.length > 0 && searchQuery.length < 2}
					Минимум 2 символа для поиска
				{:else if searchQuery.length >= 2}
					Найдено: {searchResults.length}
				{:else}
					Введите минимум 2 символа для поиска
				{/if}
			</p>

			{#if searchResults.length > 0}
				<div class="user-list anim-rows">
					{#each searchResults as user}
						<PixelCard padding="sm">
							<div class="user-item">
								<PixelAvatar avatarId={user.avatar_id} size="md" />
								<div class="user-info">
									<span class="user-name">{user.username ? `${user.username}` : user.first_name}</span>
									{#if user.username && user.first_name}
										<span class="user-username">{user.first_name}</span>
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
				<EmptyState
					icon="search"
					message="Пользователи не найдены"
				/>
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
			<EmptyState
				icon="friends"
				message="У вас пока нет друзей"
				hint="Найдите друзей по username"
				buttonText="Найти друзей"
				onButtonClick={() => switchTab('search')}
			/>
		{:else}
			<div class="user-list anim-rows">
				{#each friends as friend}
					<PixelCard padding="sm">
						<div class="user-item">
							<PixelAvatar avatarId={friend.avatar_id} size="md" />
							<div class="user-info">
								<span class="user-name">{friend.username ? `${friend.username}` : friend.first_name}</span>
								{#if friend.username && friend.first_name}
									<span class="user-username">{friend.first_name}</span>
								{/if}
								<div class="user-stats">
									<span>Ур.{friend.level}</span>
									<span class="streak">
										<PixelIcon name="streak" size="sm" color="var(--pixel-yellow)" />
										{friend.current_streak}
									</span>
								</div>
							</div>
							<button class="remove-btn" onclick={() => showRemoveConfirmation(friend.id, friend.username || friend.first_name || 'друга', false)}>
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
			<EmptyState
				icon="mail"
				message="Нет входящих заявок"
			/>
		{:else}
			<div class="user-list anim-rows">
				{#each friendRequests as request}
					<PixelCard padding="sm">
						<div class="user-item">
							<PixelAvatar avatarId={request.avatar_id} size="md" />
							<div class="user-info">
								<span class="user-name">{request.username ? `${request.username}` : request.first_name}</span>
								{#if request.username && request.first_name}
									<span class="user-username">{request.first_name}</span>
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
								<button class="remove-btn" onclick={() => showRemoveConfirmation(request.id, request.username || request.first_name || 'пользователя', true)}>
									<PixelIcon name="close" size="sm" color="var(--text-muted)" />
								</button>
							</div>
						</div>
					</PixelCard>
				{/each}
			</div>
		{/if}
	{/if}

	<!-- Confirmation Dialog -->
	{#if confirmRemove}
		<div class="modal-overlay" onclick={cancelRemove}>
			<div class="modal-dialog" onclick={(e) => e.stopPropagation()}>
				<div class="modal-header">
					<PixelIcon name="warning" size="lg" color="var(--pixel-yellow)" />
				</div>
				<div class="modal-body">
					<p class="modal-title">
						{confirmRemove.isRequest ? 'Отклонить заявку?' : 'Удалить из друзей?'}
					</p>
					<p class="modal-text">
						{confirmRemove.isRequest
							? `Вы уверены, что хотите отклонить заявку от ${confirmRemove.name}?`
							: `Вы уверены, что хотите удалить ${confirmRemove.name} из друзей?`}
					</p>
				</div>
				<div class="modal-actions">
					<PixelButton variant="secondary" onclick={cancelRemove}>
						Отмена
					</PixelButton>
					<PixelButton variant="danger" onclick={confirmRemoveFriend}>
						{confirmRemove.isRequest ? 'Отклонить' : 'Удалить'}
					</PixelButton>
				</div>
			</div>
		</div>
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

	/* Error */
	.error-message {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-sm);
		background: rgba(200, 70, 63, 0.12);
		border: var(--border-width) solid var(--pixel-red);
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

	.invite-link-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.invite-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.search-box {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-input {
		width: 100%;
		padding: var(--spacing-sm) var(--spacing-md);
		padding-right: 40px;
		font-family: var(--font-pixel);
		font-size: var(--font-size-sm);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		color: var(--text-primary);
		outline: none;
	}

	.search-input:focus {
		border-color: var(--pixel-accent);
	}

	.search-input::placeholder {
		color: var(--text-muted);
	}

	.search-icon {
		position: absolute;
		right: var(--spacing-sm);
		pointer-events: none;
	}

	.clear-search-btn {
		position: absolute;
		right: var(--spacing-xs);
		background: none;
		border: none;
		padding: var(--spacing-xs);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-secondary);
	}

	.clear-search-btn:hover {
		color: var(--text-primary);
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
		border: var(--border-width) solid var(--border-color);
	}

	.status-badge.accepted {
		background: var(--pixel-green);
		color: #fff;
	}

	.status-badge.pending {
		background: var(--pixel-yellow);
		color: var(--text-primary);
	}

	.request-actions {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
	}

	.remove-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--border-color);
		padding: var(--spacing-xs);
		cursor: pointer;
		opacity: 0.85;
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

	/* Confirmation Modal */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-md);
	}

	.modal-dialog {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		box-shadow: var(--shadow-md);
		max-width: 320px;
		width: 100%;
		animation: modal-appear 0.2s ease-out;
	}

	@keyframes modal-appear {
		from {
			opacity: 0;
			transform: scale(0.9);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}

	.modal-header {
		display: flex;
		justify-content: center;
		padding: var(--spacing-md);
		background: rgba(244, 197, 66, 0.18);
		border-bottom: var(--border-width) solid var(--border-color);
	}

	.modal-body {
		padding: var(--spacing-md);
		text-align: center;
	}

	.modal-title {
		font-family: var(--font-pixel);
		font-size: var(--font-size-md);
		margin-bottom: var(--spacing-sm);
		color: var(--text-primary);
	}

	.modal-text {
		font-size: var(--font-size-sm);
		color: var(--text-secondary);
		line-height: 1.4;
	}

	.modal-actions {
		display: flex;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		border-top: var(--border-width) solid var(--border-color);
	}

	.modal-actions > :global(*) {
		flex: 1;
	}
</style>
