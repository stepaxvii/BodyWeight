<script lang="ts">
	import { base } from '$app/paths';
	import { PixelButton, PixelIcon, PixelAvatar } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { UserProfile } from '$lib/types';

	interface Props {
		userId: number | null;
		onclose: () => void;
	}

	let { userId, onclose }: Props = $props();

	let profile = $state<UserProfile | null>(null);
	let isLoading = $state(false);
	let error = $state<string | null>(null);
	let isAddingFriend = $state(false);

	$effect(() => {
		if (userId) {
			loadProfile(userId);
		} else {
			profile = null;
		}
	});

	async function loadProfile(id: number) {
		isLoading = true;
		error = null;
		try {
			profile = await api.getUserProfile(id);
		} catch (err) {
			console.error('Failed to load user profile:', err);
			error = 'Не удалось загрузить профиль';
		} finally {
			isLoading = false;
		}
	}

	async function handleAddFriend() {
		if (!profile?.username) return;

		isAddingFriend = true;
		try {
			await api.addFriend(profile.username);
			profile = { ...profile, is_friend: true };
			telegram.hapticNotification('success');
		} catch (err) {
			console.error('Failed to add friend:', err);
			telegram.hapticNotification('error');
		} finally {
			isAddingFriend = false;
		}
	}

	function handleOverlayClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onclose();
		}
	}
</script>

{#if userId !== null}
	<div class="modal-overlay" onclick={handleOverlayClick}>
		<div class="modal-container">
			<button class="close-btn" onclick={onclose}>
				<PixelIcon name="close" />
			</button>

			{#if isLoading}
				<div class="loading">
					<div class="loading-spinner"></div>
					<span>Загрузка...</span>
				</div>
			{:else if error}
				<div class="error">
					<PixelIcon name="close" size="lg" color="var(--pixel-red)" />
					<p>{error}</p>
				</div>
			{:else if profile}
				<!-- Profile Header -->
				<div class="profile-header">
					<PixelAvatar
						avatarId={profile.avatar_id}
						size="xl"
						borderColor="var(--pixel-accent)"
					/>
					<h2 class="username">
						{profile.username ? `@${profile.username}` : (profile.first_name || 'Пользователь')}
					</h2>
					<div class="level-badge">Ур.{profile.level}</div>
				</div>

				<!-- Stats -->
				<div class="stats-grid">
					<div class="stat-item">
						<PixelIcon name="xp" size="md" color="var(--pixel-blue)" />
						<span class="stat-value">{profile.total_xp}</span>
						<span class="stat-label">XP</span>
					</div>
					<div class="stat-item">
						<PixelIcon name="coin" size="md" color="var(--pixel-orange)" />
						<span class="stat-value">{profile.coins}</span>
						<span class="stat-label">Монеты</span>
					</div>
					<div class="stat-item">
						<PixelIcon name="streak" size="md" color="var(--pixel-yellow)" />
						<span class="stat-value">{profile.current_streak}</span>
						<span class="stat-label">Серия</span>
					</div>
				</div>

				<!-- Badges -->
				{#if profile.achievements.length > 0}
					<div class="badges-section">
						<h3 class="section-title">Значки</h3>
						<div class="badges-grid">
							{#each profile.achievements as slug}
								<div class="badge-item">
									<img
										src="{base}/sprites/badges/{slug}.svg"
										alt={slug}
										class="badge-icon"
									/>
								</div>
							{/each}
						</div>
					</div>
				{:else}
					<div class="no-badges">
						<PixelIcon name="trophy" size="md" color="var(--text-muted)" />
						<span>Пока нет значков</span>
					</div>
				{/if}

				<!-- Friend Status / Add Button -->
				<div class="friend-section">
					{#if profile.is_friend}
						<div class="friend-status">
							<PixelIcon name="friend" size="sm" color="var(--pixel-green)" />
							<span>Друг</span>
						</div>
					{:else if profile.friendship_pending}
						<div class="friend-status pending">
							<PixelIcon name="time" size="sm" color="var(--pixel-yellow)" />
							<span>Заявка отправлена</span>
						</div>
					{:else if profile.username}
						<PixelButton
							variant="primary"
							fullWidth
							onclick={handleAddFriend}
							disabled={isAddingFriend}
						>
							{#if isAddingFriend}
								<span class="spinner"></span>
							{:else}
								<PixelIcon name="plus" size="sm" />
							{/if}
							Добавить в друзья
						</PixelButton>
					{:else}
						<p class="no-username">У пользователя нет username</p>
					{/if}
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.8);
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-md);
	}

	.modal-container {
		width: 100%;
		max-width: 320px;
		background: var(--pixel-bg);
		border: 2px solid var(--border-color);
		padding: var(--spacing-lg);
		position: relative;
	}

	.close-btn {
		position: absolute;
		top: var(--spacing-sm);
		right: var(--spacing-sm);
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: none;
		cursor: pointer;
		opacity: 0.7;
	}

	.close-btn:hover {
		opacity: 1;
	}

	.loading, .error {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-secondary);
	}

	.loading-spinner {
		width: 32px;
		height: 32px;
		border: 3px solid var(--border-color);
		border-top-color: var(--pixel-accent);
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Profile Header */
	.profile-header {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-lg);
	}

	.username {
		font-size: var(--font-size-md);
		margin: 0;
	}

	.level-badge {
		background: var(--pixel-accent);
		padding: 2px 8px;
		font-size: var(--font-size-xs);
	}

	/* Stats Grid */
	.stats-grid {
		display: flex;
		justify-content: space-around;
		padding: var(--spacing-md);
		background: var(--pixel-card);
		border: 2px solid var(--border-color);
		margin-bottom: var(--spacing-md);
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
	}

	.stat-value {
		font-size: var(--font-size-sm);
	}

	.stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	/* Badges */
	.badges-section {
		margin-bottom: var(--spacing-md);
	}

	.section-title {
		font-size: var(--font-size-xs);
		text-transform: uppercase;
		color: var(--text-secondary);
		margin-bottom: var(--spacing-sm);
	}

	.badges-grid {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-xs);
		justify-content: center;
	}

	.badge-item {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
	}

	.badge-icon {
		width: 28px;
		height: 28px;
		image-rendering: pixelated;
	}

	.no-badges {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		color: var(--text-muted);
		font-size: var(--font-size-xs);
	}

	/* Friend Section */
	.friend-section {
		margin-top: var(--spacing-md);
	}

	.friend-status {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm);
		background: rgba(0, 168, 0, 0.2);
		border: 2px solid var(--pixel-green);
		color: var(--pixel-green);
		font-size: var(--font-size-sm);
		text-transform: uppercase;
	}

	.friend-status.pending {
		background: rgba(255, 204, 0, 0.2);
		border-color: var(--pixel-yellow);
		color: var(--pixel-yellow);
	}

	.no-username {
		text-align: center;
		font-size: var(--font-size-xs);
		color: var(--text-muted);
	}

	.spinner {
		width: 14px;
		height: 14px;
		border: 2px solid currentColor;
		border-top-color: transparent;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
</style>
