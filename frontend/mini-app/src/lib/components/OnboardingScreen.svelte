<script lang="ts">
	import { PixelButton, PixelAvatar } from '$lib/components/ui';
	import OnboardingSlides from './OnboardingSlides.svelte';
	import { AVATARS } from '$lib/data/avatars';
	import { userStore } from '$lib/stores/user.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { AvatarId } from '$lib/types';

	// Onboarding stages: slides -> avatar selection
	let stage = $state<'slides' | 'avatar'>('slides');

	// Filter only free avatars for onboarding
	const freeAvatars = AVATARS.filter(a => a.price === 0 && a.requiredLevel === 1);

	let selectedAvatar = $state<AvatarId>('shadow-wolf');
	let isSubmitting = $state(false);

	function handleSlidesComplete() {
		stage = 'avatar';
		telegram.hapticImpact('medium');
	}

	function selectAvatar(avatarId: AvatarId) {
		selectedAvatar = avatarId;
		telegram.hapticImpact('light');
	}

	async function handleContinue() {
		if (isSubmitting) return;

		isSubmitting = true;
		telegram.hapticNotification('success');

		try {
			await userStore.setAvatar(selectedAvatar);
			await userStore.completeOnboarding();
		} catch (err) {
			console.error('Onboarding error:', err);
			telegram.hapticNotification('error');
		} finally {
			isSubmitting = false;
		}
	}
</script>

{#if stage === 'slides'}
	<OnboardingSlides onComplete={handleSlidesComplete} />
{:else}
	<div class="onboarding">
		<div class="onboarding-content">
			<div class="welcome-section">
				<h1 class="title">Выбери персонажа</h1>
				<p class="subtitle">Его можно изменить позже в профиле</p>
			</div>

			<div class="avatar-grid">
				{#each freeAvatars as avatar}
					<button
						class="avatar-option"
						class:selected={selectedAvatar === avatar.id}
						onclick={() => selectAvatar(avatar.id)}
					>
						<div class="avatar-frame">
							<PixelAvatar
								avatarId={avatar.id}
								size="xl"
								showBorder={false}
							/>
						</div>
						<span class="avatar-name">{avatar.name_ru}</span>
					</button>
				{/each}
			</div>

			<div class="selected-preview">
				<div class="preview-avatar">
					<PixelAvatar
						avatarId={selectedAvatar}
						size="xl"
						showBorder={true}
						borderColor="var(--pixel-accent)"
					/>
				</div>
				<p class="preview-text">
					{freeAvatars.find(a => a.id === selectedAvatar)?.name_ru ?? 'Волк'}
				</p>
			</div>

			<div class="action-section">
				<PixelButton
					variant="success"
					size="lg"
					fullWidth
					loading={isSubmitting}
					onclick={handleContinue}
				>
					Начать тренировки
				</PixelButton>
			</div>
		</div>
	</div>
{/if}

<style>
	.onboarding {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-lg);
		background: var(--pixel-bg);
	}

	.onboarding-content {
		width: 100%;
		max-width: 400px;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xl);
		animation: fadeIn 0.3s ease-out;
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(10px); }
		to { opacity: 1; transform: translateY(0); }
	}

	.welcome-section {
		text-align: center;
	}

	.title {
		font-size: var(--font-size-xl);
		color: var(--pixel-accent);
		margin: 0 0 var(--spacing-sm) 0;
		text-transform: uppercase;
	}

	.subtitle {
		font-size: var(--font-size-md);
		color: var(--text-secondary);
		margin: 0;
	}

	.avatar-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-md);
		width: 100%;
	}

	.avatar-option {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		background: var(--pixel-card);
		border: 3px solid var(--border-color);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.avatar-option:hover {
		border-color: var(--pixel-accent);
		background: var(--pixel-card-hover);
	}

	.avatar-option.selected {
		border-color: var(--pixel-green);
		background: rgba(0, 168, 0, 0.15);
		box-shadow: 0 0 0 2px var(--pixel-green);
	}

	.avatar-frame {
		width: 64px;
		height: 64px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.avatar-name {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
		text-transform: uppercase;
	}

	.selected-preview {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		background: var(--pixel-bg-dark);
		border: 2px solid var(--border-color);
		width: 100%;
	}

	.preview-avatar {
		animation: bounce 0.5s ease-in-out;
	}

	.preview-text {
		font-size: var(--font-size-md);
		color: var(--pixel-accent);
		margin: 0;
		text-transform: uppercase;
	}

	.action-section {
		width: 100%;
		padding-top: var(--spacing-md);
	}

	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-8px); }
	}
</style>
