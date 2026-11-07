<script lang="ts">
	import { base } from '$app/paths';
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { PixelIcon } from '$lib/components/ui';
	import { userStore } from '$lib/stores/user.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { sound } from '$lib/stores/sound.svelte';
	import { api } from '$lib/api/client';
	import { t, ln, setLocale, getLocale } from '$lib/i18n/index.svelte';
	import { TIMEZONE_GROUPS } from '$lib/timezones';

	// ── Звук ──────────────────────────────────────────────
	const soundOn = $derived(userStore.user?.sound_enabled ?? true);
	function toggleSound() {
		const next = !soundOn;
		userStore.setSoundEnabled(next);
		telegram.hapticImpact('light');
		if (next) {
			// Unlock audio on this gesture and play a confirming cue.
			sound.unlock();
			sound.start();
		}
	}

	// ── Видимость в рейтинге ──────────────────────────────
	const lbVisible = $derived(userStore.user?.leaderboard_visible ?? false);
	let lbBusy = $state(false);
	async function toggleLeaderboard() {
		if (lbBusy) return;
		lbBusy = true;
		try {
			await userStore.setLeaderboardVisible(!lbVisible);
			telegram.hapticImpact('light');
		} catch {
			telegram.hapticNotification('error');
		} finally {
			lbBusy = false;
		}
	}

	// ── Дневная норма XP ──────────────────────────────────
	let normInput = $state(1400);
	let normSaving = $state(false);
	let normMessage = $state<string | null>(null);
	async function handleSaveNorm() {
		if (normSaving) return;
		const value = Math.round(Number(normInput));
		if (!Number.isFinite(value) || value < 100 || value > 100000) {
			normMessage = t('settings.game.norm.invalid');
			return;
		}
		normSaving = true;
		normMessage = null;
		try {
			await userStore.setActivityNorm(value);
			telegram.hapticNotification('success');
			normMessage = t('settings.game.norm.saved');
		} catch (err) {
			telegram.hapticNotification('error');
			normMessage = err instanceof Error ? err.message : t('settings.game.norm.saveError');
		} finally {
			normSaving = false;
		}
	}

	// ── Уведомления (Telegram-пуши) ───────────────────────
	// ── Язык интерфейса ───────────────────────────────────
	const currentLang = $derived(userStore.user?.language ?? getLocale());
	let langBusy = $state(false);
	async function setLanguage(lang: 'ru' | 'en') {
		if (langBusy || currentLang === lang) return;
		const prev = currentLang;
		langBusy = true;
		// Live-switch the whole UI immediately (optimistic).
		setLocale(lang);
		if (userStore.user) userStore.user.language = lang;
		try {
			userStore.user = await api.updateUser({ language: lang });
			telegram.hapticImpact('light');
		} catch {
			// Server rejected it — roll the optimistic switch back.
			setLocale(prev);
			if (userStore.user) userStore.user.language = prev;
			telegram.hapticNotification('error');
		} finally {
			langBusy = false;
		}
	}

	const notifOn = $derived(userStore.user?.notifications_enabled ?? true);
	let notifBusy = $state(false);
	async function toggleNotif() {
		if (notifBusy) return;
		notifBusy = true;
		try {
			await userStore.setNotificationsEnabled(!notifOn);
			telegram.hapticImpact('light');
		} catch {
			telegram.hapticNotification('error');
		} finally {
			notifBusy = false;
		}
	}

	// Время напоминания ("HH:MM"); backend хранит time, планировщик смотрит на час.
	let timeInput = $state('');
	let timeSaving = $state(false);
	let timeMessage = $state<string | null>(null);
	async function handleSaveTime() {
		if (timeSaving || !timeInput) return;
		timeSaving = true;
		timeMessage = null;
		try {
			await userStore.setNotificationTime(timeInput);
			telegram.hapticNotification('success');
			timeMessage = t('settings.notifications.time.saved');
		} catch (err) {
			telegram.hapticNotification('error');
			timeMessage = err instanceof Error ? err.message : t('settings.notifications.time.saveError');
		} finally {
			timeSaving = false;
		}
	}

	// ── Часовой пояс ──────────────────────────────────────
	let tzInput = $state('UTC');
	let tzSaving = $state(false);
	let tzMessage = $state<string | null>(null);
	async function handleSaveTimezone() {
		if (tzSaving || !tzInput) return;
		tzSaving = true;
		tzMessage = null;
		try {
			await userStore.setTimezone(tzInput);
			telegram.hapticNotification('success');
			tzMessage = t('settings.timezone.saved');
		} catch (err) {
			telegram.hapticNotification('error');
			tzMessage = err instanceof Error ? err.message : t('settings.timezone.saveError');
		} finally {
			tzSaving = false;
		}
	}

	// ── Account ───────────────────────────────────────────
	const hasAccountInfo = $derived(!!userStore.user?.telegram_id);

	function goBack() {
		goto(`${base}/profile`);
	}

	onMount(() => {
		normInput = userStore.dailyActivityNorm;
		const t = userStore.user?.notification_time;
		timeInput = t ? t.slice(0, 5) : '';
		tzInput = userStore.user?.timezone || 'UTC';
		// Native Telegram back button (no-op outside Telegram).
		telegram.showBackButton(goBack);
	});

	onDestroy(() => {
		telegram.hideBackButton();
	});
</script>

<div class="page container anim-cascade">
	<header class="set-head">
		<a class="set-back" href="{base}/profile" aria-label={t('settings.back')}>
			<PixelIcon name="arrowleft" size="md" color="var(--text)" />
		</a>
		<h1 class="set-title">{t('settings.title')}</h1>
		<span class="set-headgear" aria-hidden="true"><PixelIcon name="gear" size="md" color="var(--accent)" /></span>
	</header>

	<!-- Игра -->
	<section class="set-section">
		<h3 class="set-section__t">{t('settings.game.heading')}</h3>
		<div class="set-list">
			<button class="set-row" onclick={toggleSound}>
				<PixelIcon name="bell" size="md" color="var(--accent)" />
				<div class="set-row__text">
					<span class="set-row__title">{t('settings.game.sound.title')}</span>
					<span class="set-row__hint">{t('settings.game.sound.hint')}</span>
				</div>
				<span class="set-toggle" class:on={soundOn}>{soundOn ? t('settings.toggle.on') : t('settings.toggle.off')}</span>
			</button>

			<button class="set-row" onclick={toggleLeaderboard} disabled={lbBusy}>
				<PixelIcon name="trophy" size="md" color="var(--gold)" />
				<div class="set-row__text">
					<span class="set-row__title">{t('settings.game.leaderboard.title')}</span>
					<span class="set-row__hint">{t('settings.game.leaderboard.hint')}</span>
				</div>
				<span class="set-toggle" class:on={lbVisible}>{lbVisible ? t('settings.toggle.on') : t('settings.toggle.off')}</span>
			</button>

			<div class="set-block">
				<div class="set-block__head">
					<PixelIcon name="target" size="md" color="var(--accent2)" />
					<div class="set-row__text">
						<span class="set-row__title">{t('settings.game.norm.title')}</span>
						<span class="set-row__hint">{t('settings.game.norm.hint')}</span>
					</div>
				</div>
				<div class="set-controls">
					<input
						class="set-input"
						type="number"
						min="100"
						max="100000"
						step="50"
						bind:value={normInput}
					/>
					<span class="set-unit">{t('settings.game.norm.unit')}</span>
					<button class="set-save" disabled={normSaving} onclick={handleSaveNorm}>
						{normSaving ? t('settings.common.saving') : t('settings.common.save')}
					</button>
				</div>
				{#if normMessage}
					<p class="set-msg">{normMessage}</p>
				{/if}
			</div>
		</div>
	</section>

	<!-- Уведомления -->
	<section class="set-section">
		<h3 class="set-section__t">{t('settings.timezone.heading')}</h3>
		<div class="set-list">
			<div class="set-block">
				<div class="set-block__head">
					<PixelIcon name="clock" size="md" color="var(--accent2)" />
					<div class="set-row__text">
						<span class="set-row__title">{t('settings.timezone.title')}</span>
						<span class="set-row__hint">{t('settings.timezone.hint')}</span>
					</div>
				</div>
				<div class="set-controls">
					<select class="set-input set-select" bind:value={tzInput}>
						{#each TIMEZONE_GROUPS as group (group.region)}
							<optgroup label={ln(group.region_en, group.region)}>
								{#each group.zones as z (z.value)}
									<option value={z.value}>{ln(z.label_en, z.label)}</option>
								{/each}
							</optgroup>
						{/each}
					</select>
					<button class="set-save" disabled={tzSaving || !tzInput} onclick={handleSaveTimezone}>
						{tzSaving ? t('settings.common.saving') : t('settings.common.save')}
					</button>
				</div>
				{#if tzMessage}
					<p class="set-msg">{tzMessage}</p>
				{/if}
			</div>
		</div>
	</section>

	<section class="set-section">
		<h3 class="set-section__t">{t('settings.notifications.heading')}</h3>
		<div class="set-list">
			<button class="set-row" onclick={toggleNotif} disabled={notifBusy}>
				<PixelIcon name="mail" size="md" color="var(--accent)" />
				<div class="set-row__text">
					<span class="set-row__title">{t('settings.notifications.push.title')}</span>
					<span class="set-row__hint">{t('settings.notifications.push.hint')}</span>
				</div>
				<span class="set-toggle" class:on={notifOn}>{notifOn ? t('settings.toggle.on') : t('settings.toggle.off')}</span>
			</button>

			{#if notifOn}
				<div class="set-block">
					<div class="set-block__head">
						<PixelIcon name="clock" size="md" color="var(--accent2)" />
						<div class="set-row__text">
							<span class="set-row__title">{t('settings.notifications.time.title')}</span>
							<span class="set-row__hint">{t('settings.notifications.time.hint')}</span>
						</div>
					</div>
					<div class="set-controls">
						<input class="set-input" type="time" bind:value={timeInput} />
						<button class="set-save" disabled={timeSaving || !timeInput} onclick={handleSaveTime}>
							{timeSaving ? t('settings.common.saving') : t('settings.common.save')}
						</button>
					</div>
					{#if timeMessage}
						<p class="set-msg">{timeMessage}</p>
					{/if}
				</div>
			{/if}
		</div>
	</section>

	<!-- Язык -->
	<section class="set-section">
		<h3 class="set-section__t">{t('settings.language.heading')}</h3>
		<div class="set-list">
			<div class="set-block">
				<div class="set-block__head">
					<PixelIcon name="star" size="md" color="var(--accent2)" />
					<div class="set-row__text">
						<span class="set-row__title">{t('settings.language.title')}</span>
						<span class="set-row__hint">{t('settings.language.hint')}</span>
					</div>
				</div>
				<div class="set-controls lang-controls">
					<button
						class="set-lang"
						class:on={currentLang === 'ru'}
						disabled={langBusy}
						onclick={() => setLanguage('ru')}
					>
						{t('settings.language.ru')}
					</button>
					<button
						class="set-lang"
						class:on={currentLang === 'en'}
						disabled={langBusy}
						onclick={() => setLanguage('en')}
					>
						{t('settings.language.en')}
					</button>
				</div>
			</div>
		</div>
	</section>

	<!-- Account -->
	{#if hasAccountInfo}
		<section class="set-section">
			<h3 class="set-section__t">{t('settings.account.heading')}</h3>
			<div class="account-info">
				{#if userStore.user?.telegram_id}
					<div class="account-row">
						<span class="account-label">{t('settings.account.telegram')}</span>
						<span class="account-value">{t('settings.account.telegramId', { id: userStore.user.telegram_id })}</span>
					</div>
				{/if}
			</div>
		</section>
	{/if}
</div>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	/* Header with back arrow */
	.set-head {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-md);
	}
	.set-back {
		flex: 0 0 auto;
		width: 40px;
		height: 40px;
		display: grid;
		place-items: center;
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		cursor: pointer;
	}
	.set-back:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}
	.set-title {
		flex: 1;
		margin: 0;
		font-family: var(--font-display);
		font-size: var(--font-size-md);
		color: var(--text);
	}
	.set-headgear {
		flex: 0 0 auto;
		display: grid;
		place-items: center;
		width: 40px;
		height: 40px;
	}

	/* Sections */
	.set-section {
		margin-bottom: var(--spacing-md);
	}
	.set-section__t {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin: 0 0 var(--spacing-sm) 0;
		color: var(--muted);
	}
	.set-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	/* Toggle row (mirrors the neo .sound-row pattern) */
	.set-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		width: 100%;
		text-align: left;
		padding: var(--spacing-sm) var(--spacing-md);
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		cursor: pointer;
	}
	.set-row:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}
	.set-row:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.set-row__text {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}
	.set-row__title {
		font-size: var(--font-size-sm);
		color: var(--text);
	}
	.set-row__hint {
		font-size: 10px;
		color: var(--muted);
		line-height: 1.4;
	}
	.set-toggle {
		flex: 0 0 auto;
		font-family: var(--font-display);
		font-size: 12px;
		padding: 4px 10px;
		background: var(--bg3);
		border: 2px solid var(--line);
		color: var(--muted);
	}
	.set-toggle.on {
		background: var(--accent);
		color: var(--on-accent);
	}

	/* Input block (norm / time) */
	.set-block {
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		padding: var(--spacing-sm) var(--spacing-md);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}
	.set-block__head {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}
	.set-controls {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}
	.set-input {
		flex: 1;
		min-width: 0;
		padding: 8px 10px;
		background: var(--bg3);
		border: var(--bw) solid var(--line);
		color: var(--text);
		font-family: inherit;
		font-size: 14px;
		outline: none;
	}
	.set-input:focus {
		border-color: var(--accent);
	}
	/* Native <select> reusing the .set-input skin (timezone picker). */
	.set-select {
		appearance: none;
		-webkit-appearance: none;
		cursor: pointer;
		background-image: linear-gradient(45deg, transparent 50%, var(--muted) 50%),
			linear-gradient(135deg, var(--muted) 50%, transparent 50%);
		background-position:
			calc(100% - 16px) calc(50% - 2px),
			calc(100% - 11px) calc(50% - 2px);
		background-size: 5px 5px, 5px 5px;
		background-repeat: no-repeat;
		padding-right: 28px;
	}
	.set-unit {
		font-size: var(--font-size-xs);
		color: var(--muted);
	}
	.set-save {
		padding: 8px var(--spacing-md);
		background: var(--bg3);
		border: var(--bw) solid var(--accent);
		color: var(--accent);
		font-family: inherit;
		font-size: var(--font-size-xs);
		cursor: pointer;
		white-space: nowrap;
	}
	.set-save:active:not(:disabled) {
		transform: translate(2px, 2px);
	}
	.set-save:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.set-msg {
		font-size: 10px;
		color: var(--muted);
		margin: 0;
		text-align: center;
	}

	/* Language selector (RU / EN) */
	.lang-controls {
		gap: var(--spacing-sm);
	}
	.set-lang {
		flex: 1;
		padding: 8px var(--spacing-md);
		background: var(--bg3);
		border: var(--bw) solid var(--line);
		color: var(--muted);
		font-family: inherit;
		font-size: var(--font-size-xs);
		cursor: pointer;
		text-align: center;
	}
	.set-lang:active:not(:disabled) {
		transform: translate(2px, 2px);
	}
	.set-lang:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.set-lang.on {
		background: var(--accent);
		border-color: var(--accent);
		color: var(--on-accent);
	}

	/* Account (moved from profile) */
	.account-info {
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		padding: var(--spacing-sm) var(--spacing-md);
		margin-bottom: var(--spacing-sm);
	}
	.account-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-xs) 0;
	}
	.account-row + .account-row {
		border-top: 1px solid var(--line);
	}
	.account-label {
		font-size: var(--font-size-xs);
		color: var(--muted);
	}
	.account-value {
		font-size: var(--font-size-xs);
		color: var(--text);
	}
	.account-actions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}
</style>
