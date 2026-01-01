<script lang="ts">
	import { PixelButton, PixelCard, PixelIcon, PixelModal, PixelAvatar } from '$lib/components/ui';
	import { AVATARS, canUnlockAvatar } from '$lib/data/avatars';
	import { userStore } from '$lib/stores/user.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { AvatarId, Avatar } from '$lib/types';

	interface Props {
		open?: boolean;
		currentAvatarId?: AvatarId;
		onselect?: (avatarId: AvatarId) => void;
		onclose?: () => void;
	}

	let {
		open = false,
		currentAvatarId = 'shadow-wolf',
		onselect,
		onclose
	}: Props = $props();

	let selectedAvatar = $state<AvatarId>(currentAvatarId);

	function selectAvatar(avatar: Avatar) {
		const canUse = canUnlockAvatar(avatar, userStore.level, userStore.coins);

		if (!canUse) {
			telegram.hapticNotification('error');
			return;
		}

		selectedAvatar = avatar.id;
		telegram.hapticImpact('light');
	}

	async function confirmSelection() {
		const avatar = AVATARS.find(a => a.id === selectedAvatar);
		if (!avatar) return;

		// Backend will handle coin deduction and purchase validation
		// Just call setAvatar - backend will check coins and deduct if needed
		try {
			await userStore.setAvatar(selectedAvatar);
			telegram.hapticNotification('success');
			onselect?.(selectedAvatar);
			onclose?.();
		} catch (err) {
			console.error('Failed to set avatar:', err);
			telegram.hapticNotification('error');
		}
	}

	function isLocked(avatar: Avatar): boolean {
		return userStore.level < avatar.requiredLevel;
	}

	function isAffordable(avatar: Avatar): boolean {
		return userStore.coins >= avatar.price || avatar.id === currentAvatarId;
	}
</script>

<PixelModal {open} title="Выбор аватара" {onclose}>
	<div class="avatar-picker">
		<div class="avatars-grid">
			{#each AVATARS as avatar}
				{@const locked = isLocked(avatar)}
				{@const affordable = isAffordable(avatar)}
				{@const isSelected = selectedAvatar === avatar.id}
				{@const isCurrent = currentAvatarId === avatar.id}

				<button
					class="avatar-option"
					class:selected={isSelected}
					class:locked
					class:unaffordable={!locked && !affordable}
					onclick={() => selectAvatar(avatar)}
					disabled={locked}
				>
					<div class="avatar-frame">
						{#if locked}
							<div class="lock-overlay">
								<PixelIcon name="lock" size="lg" color="var(--text-muted)" />
							</div>
						{/if}
						<PixelAvatar
							avatarId={avatar.id}
							size="lg"
							showBorder={false}
						/>
					</div>
					<span class="avatar-name">{avatar.name_ru}</span>
					{#if locked}
						<span class="avatar-req">Lv.{avatar.requiredLevel}</span>
					{:else if avatar.price > 0 && !isCurrent}
						<span class="avatar-price">
							<PixelIcon name="coin" size="sm" color="var(--pixel-orange)" />
							{avatar.price}
						</span>
					{:else if isCurrent}
						<span class="avatar-current">Текущий</span>
					{:else}
						<span class="avatar-free">Бесплатно</span>
					{/if}
				</button>
			{/each}
		</div>

		<div class="picker-footer">
			<div class="coins-display">
				<PixelIcon name="coin" color="var(--pixel-orange)" />
				<span>{userStore.coins}</span>
			</div>
			<PixelButton
				variant="primary"
				onclick={confirmSelection}
				disabled={selectedAvatar === currentAvatarId}
			>
				{#if selectedAvatar === currentAvatarId}
					Выбрано
				{:else}
					Выбрать
				{/if}
			</PixelButton>
		</div>
	</div>
</PixelModal>

<style>
	.avatar-picker {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
	}

	.avatars-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-sm);
	}

	.avatar-option {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.avatar-option:hover:not(:disabled) {
		border-color: var(--pixel-accent);
	}

	.avatar-option.selected {
		border-color: var(--pixel-green);
		background: rgba(0, 168, 0, 0.1);
	}

	.avatar-option.locked {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.avatar-option.unaffordable {
		opacity: 0.7;
	}

	.avatar-frame {
		position: relative;
		width: 48px;
		height: 48px;
	}

	.lock-overlay {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.6);
		z-index: 1;
	}

	.avatar-name {
		font-size: var(--font-size-xs);
		color: var(--text-primary);
	}

	.avatar-req {
		font-size: 8px;
		color: var(--text-muted);
	}

	.avatar-price {
		display: flex;
		align-items: center;
		gap: 2px;
		font-size: 8px;
		color: var(--pixel-orange);
	}

	.avatar-current {
		font-size: 8px;
		color: var(--pixel-green);
	}

	.avatar-free {
		font-size: 8px;
		color: var(--text-secondary);
	}

	.picker-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-top: var(--spacing-sm);
		border-top: 2px solid var(--border-color);
	}

	.coins-display {
		display: flex;
		align-items: center;
		gap: var(--spacing-xs);
		font-size: var(--font-size-sm);
		color: var(--pixel-orange);
	}
</style>
