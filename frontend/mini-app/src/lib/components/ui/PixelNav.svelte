<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { workoutStore } from '$lib/stores/workout.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { t } from '$lib/i18n/index.svelte';
	import type { NavItem } from '$lib/types';
	import PixelButton from './PixelButton.svelte';
	import PixelIcon from './PixelIcon.svelte';

	interface NavItemConfig {
		id: NavItem;
		label: string;
		href: string;
		icon: string;
		// Small "Soon" tag on the icon while the feature is beta-gated for this user.
		badge?: string;
		// Persistent accent-colour highlight once the feature is live for this user.
		highlight?: boolean;
	}

	// City access is per-user (`city_enabled` on /users/me): admins get the live
	// feature; everyone else is behind the admin-only beta flag. The toolbar always
	// shows the City entry, but reflects that state — a "Soon" tag while gated, an
	// accent-colour highlight once the flag is lifted (feature goes public).
	const cityEnabled = $derived(userStore.user?.city_enabled === true);

	const navItems = $derived<NavItemConfig[]>([
		{ id: 'home', label: t('home.nav.home'), href: `${base}/`, icon: 'home' },
		// City sits right after Home so the new feature is near the start of the bar.
		{
			id: 'city',
			label: t('home.nav.city'),
			href: `${base}/city`,
			icon: 'target',
			badge: cityEnabled ? undefined : t('home.nav.citySoon'),
			highlight: cityEnabled
		},
		{ id: 'workout', label: t('home.nav.workout'), href: `${base}/workout`, icon: 'workout' },
		{ id: 'challenges', label: t('home.nav.challenges'), href: `${base}/challenges`, icon: 'calendar' },
		{ id: 'leaderboard', label: t('home.nav.leaderboard'), href: `${base}/leaderboard`, icon: 'trophy' },
		{ id: 'profile', label: t('home.nav.profile'), href: `${base}/profile`, icon: 'user' }
	]);

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
				class:highlight={item.highlight && !active}
				onclick={(e) => handleNavClick(e, item.href)}
				aria-current={active ? 'page' : undefined}
				aria-label={item.badge ? `${item.label} — ${item.badge}` : item.label}
			>
				<div class="icon-wrapper">
					<PixelIcon name={item.icon} size="lg" />
					{#if item.badge}
						<span class="nav-badge">{item.badge}</span>
					{/if}
				</div>
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
				<p class="modal-title">{t('home.exitDialog.title')}</p>
				<p class="modal-text">{t('home.exitDialog.text')}</p>
			</div>
			<div class="modal-actions">
				<PixelButton variant="success" onclick={finishAndLeave}>
					{t('home.exitDialog.finish')}
				</PixelButton>
				<PixelButton variant="secondary" onclick={continueWorkout}>
					{t('home.exitDialog.continue')}
				</PixelButton>
				<PixelButton variant="danger" onclick={cancelAndLeave}>
					{t('home.exitDialog.cancel')}
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
		border-top: var(--border-width) solid var(--border-color);
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
		align-items: center;
		justify-content: center;
		padding: var(--spacing-sm) var(--spacing-md);
		color: var(--text-secondary);
		text-decoration: none;
		position: relative;
		flex: 1;
		transition: color var(--transition-fast);
	}

	.nav-item:hover {
		color: var(--text-primary);
	}

	.nav-item.active {
		color: var(--pixel-accent);
	}

	/* Feature is live for this user but not the current page — keep it accented so
	   the new City entry stands out among the muted icons. */
	.nav-item.highlight {
		color: var(--pixel-accent);
	}

	.icon-wrapper {
		position: relative;
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* "Soon" tag shown on a beta-gated icon (e.g. City before launch). */
	.nav-badge {
		position: absolute;
		top: -7px;
		left: 50%;
		transform: translateX(-50%);
		font-family: var(--font-pixel);
		font-size: 7px;
		line-height: 1;
		letter-spacing: 0.5px;
		padding: 2px 3px;
		background: var(--pixel-accent);
		color: var(--pixel-bg-dark);
		border-radius: 2px;
		white-space: nowrap;
		pointer-events: none;
	}

	.active-indicator {
		position: absolute;
		top: 0;
		left: 50%;
		transform: translateX(-50%);
		width: 20px;
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
		border: var(--border-width) solid var(--border-color);
		border-radius: var(--radius-sm);
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
		background: var(--pixel-bg-dark);
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
		flex-direction: column;
		gap: var(--spacing-sm);
		padding: var(--spacing-md);
		border-top: var(--border-width) solid var(--border-color);
	}

	.modal-actions > :global(*) {
		width: 100%;
	}
</style>
