<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { workoutStore } from '$lib/stores/workout.svelte';
	import type { NavItem } from '$lib/types';
	import PixelButton from './PixelButton.svelte';
	import PixelIcon from './PixelIcon.svelte';

	interface NavItemConfig {
		id: NavItem;
		label: string;
		href: string;
		icon: string;
	}

	const navItems: NavItemConfig[] = [
		{ id: 'home', label: 'Главная', href: `${base}/`, icon: 'home' },
		{ id: 'workout', label: 'Тренировка', href: `${base}/workout`, icon: 'workout' },
		{ id: 'profile', label: 'Профиль', href: `${base}/profile`, icon: 'profile' },
		{ id: 'leaderboard', label: 'Рейтинг', href: `${base}/leaderboard`, icon: 'trophy' }
	];

	// Confirmation dialog state
	let showConfirmDialog = $state(false);
	let pendingHref = $state<string | null>(null);

	function isActive(href: string, pathname: string): boolean {
		if (href === `${base}/`) {
			return pathname === `${base}/` || pathname === base;
		}
		return pathname.startsWith(href);
	}

	function handleNavClick(e: MouseEvent, href: string) {
		telegram.hapticImpact('light');

		// Check if we're leaving workout page while workout is active
		const isOnWorkoutPage = $page.url.pathname.startsWith(`${base}/workout`);
		const isGoingToWorkout = href === `${base}/workout`;

		if (isOnWorkoutPage && !isGoingToWorkout && workoutStore.isActive) {
			e.preventDefault();
			pendingHref = href;
			showConfirmDialog = true;
		}
	}

	function continueWorkout() {
		showConfirmDialog = false;
		pendingHref = null;
	}

	async function finishAndLeave() {
		showConfirmDialog = false;
		await workoutStore.completeWorkout();
		if (pendingHref) {
			goto(pendingHref);
		}
		pendingHref = null;
	}

	function cancelAndLeave() {
		showConfirmDialog = false;
		workoutStore.cancelWorkout();
		if (pendingHref) {
			goto(pendingHref);
		}
		pendingHref = null;
	}
</script>

<nav class="pixel-nav">
	<div class="nav-container">
		{#each navItems as item}
			{@const active = isActive(item.href, $page.url.pathname)}
			<a
				href={item.href}
				class="nav-item"
				class:active
				onclick={(e) => handleNavClick(e, item.href)}
				aria-current={active ? 'page' : undefined}
			>
				<div class="icon-wrapper">
					<svg class="icon" viewBox="0 0 16 16" fill="currentColor">
						{#if item.icon === 'home'}
							<path d="M8 1L1 7h2v7h4v-4h2v4h4V7h2L8 1zm0 2.5L12 7v6h-2v-4H6v4H4V7l4-3.5z"/>
						{:else if item.icon === 'workout'}
							<path d="M2 7h2v2H2V7zm10 0h2v2h-2V7zM5 6h6v4H5V6zm0 5h6v1H5v-1zm0-7h6v1H5V4z"/>
						{:else if item.icon === 'profile'}
							<path d="M8 2a3 3 0 100 6 3 3 0 000-6zM4 10c0-1 1-2 4-2s4 1 4 2v3H4v-3z"/>
						{:else if item.icon === 'trophy'}
							<path d="M4 2h8v2h2v3c0 1-1 2-2 2h-1c0 2-1 3-3 3s-3-1-3-3H4c-1 0-2-1-2-2V4h2V2zm1 2v2h1c0 1 1 2 2 2s2-1 2-2h1V4H5zm1 8h4v2H6v-2z"/>
						{/if}
					</svg>
				</div>
				<span class="label">{item.label}</span>
				{#if active}
					<div class="active-indicator"></div>
				{/if}
			</a>
		{/each}
	</div>
</nav>

<!-- Workout Exit Confirmation Dialog -->
{#if showConfirmDialog}
	<div class="modal-overlay" onclick={continueWorkout}>
		<div class="modal-dialog" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<PixelIcon name="workout" size="lg" color="var(--pixel-accent)" />
			</div>
			<div class="modal-body">
				<p class="modal-title">Тренировка активна</p>
				<p class="modal-text">Что сделать с текущей тренировкой?</p>
			</div>
			<div class="modal-actions">
				<PixelButton variant="success" onclick={finishAndLeave}>
					Завершить
				</PixelButton>
				<PixelButton variant="secondary" onclick={continueWorkout}>
					Продолжить
				</PixelButton>
				<PixelButton variant="danger" onclick={cancelAndLeave}>
					Отменить
				</PixelButton>
			</div>
		</div>
	</div>
{/if}

<style>
	.pixel-nav {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		background: var(--pixel-bg-dark);
		border-top: 2px solid var(--border-color);
		z-index: 100;
		padding-bottom: env(safe-area-inset-bottom, 0);
	}

	.nav-container {
		display: flex;
		justify-content: space-around;
		align-items: center;
		max-width: 480px;
		margin: 0 auto;
		padding: var(--spacing-sm) 0;
	}

	.nav-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-xs);
		padding: var(--spacing-xs) var(--spacing-md);
		color: var(--text-secondary);
		text-decoration: none;
		position: relative;
		transition: color var(--transition-fast);
	}

	.nav-item:hover {
		color: var(--text-primary);
	}

	.nav-item.active {
		color: var(--pixel-accent);
	}

	.icon-wrapper {
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.icon {
		width: 16px;
		height: 16px;
		image-rendering: pixelated;
	}

	.label {
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		text-transform: uppercase;
	}

	.active-indicator {
		position: absolute;
		top: -2px;
		left: 50%;
		transform: translateX(-50%);
		width: 4px;
		height: 4px;
		background: var(--pixel-accent);
	}

	/* Modal styles */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.85);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-md);
	}

	.modal-dialog {
		background: var(--pixel-card);
		border: 4px solid var(--border-color);
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
		background: rgba(233, 69, 96, 0.1);
		border-bottom: 2px solid var(--border-color);
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
		flex-direction: column;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		border-top: 2px solid var(--border-color);
	}

	.modal-actions > :global(*) {
		width: 100%;
	}
</style>
