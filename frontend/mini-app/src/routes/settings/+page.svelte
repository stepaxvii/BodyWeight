<script lang="ts">
	import { base } from '$app/paths';
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { PixelIcon, PixelModal } from '$lib/components/ui';
	import { userStore } from '$lib/stores/user.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { sound } from '$lib/stores/sound.svelte';

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
			normMessage = 'Норма должна быть от 100 до 100000 XP';
			return;
		}
		normSaving = true;
		normMessage = null;
		try {
			await userStore.setActivityNorm(value);
			telegram.hapticNotification('success');
			normMessage = '✅ Норма обновлена';
		} catch (err) {
			telegram.hapticNotification('error');
			normMessage = err instanceof Error ? err.message : 'Не удалось сохранить';
		} finally {
			normSaving = false;
		}
	}

	// ── Уведомления (Telegram-пуши) ───────────────────────
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
			timeMessage = '✅ Время сохранено';
		} catch (err) {
			telegram.hapticNotification('error');
			timeMessage = err instanceof Error ? err.message : 'Не удалось сохранить';
		} finally {
			timeSaving = false;
		}
	}

	// ── Аккаунт ───────────────────────────────────────────
	let showLinkTelegram = $state(false);
	let telegramIdInput = $state('');
	let accountMessage = $state<string | null>(null);
	let accountError = $state<string | null>(null);
	let accountLoading = $state(false);

	const hasAccountInfo = $derived(!!userStore.user?.email || !!userStore.user?.telegram_id);

	function openLink() {
		showLinkTelegram = true;
		accountError = null;
	}

	async function handleLinkTelegram() {
		const tid = parseInt(telegramIdInput);
		if (isNaN(tid)) {
			accountError = 'Введите корректный Telegram ID (число)';
			return;
		}
		accountError = null;
		accountLoading = true;
		try {
			const result = await userStore.linkTelegram(tid);
			accountMessage = result.message;
			showLinkTelegram = false;
			telegramIdInput = '';
		} catch (err) {
			accountError = err instanceof Error ? err.message : 'Ошибка';
		} finally {
			accountLoading = false;
		}
	}

	function handleLogout() {
		userStore.logout();
	}

	function goBack() {
		goto(`${base}/profile`);
	}

	onMount(() => {
		normInput = userStore.dailyActivityNorm;
		const t = userStore.user?.notification_time;
		timeInput = t ? t.slice(0, 5) : '';
		// Native Telegram back button (no-op outside Telegram).
		telegram.showBackButton(goBack);
	});

	onDestroy(() => {
		telegram.hideBackButton();
	});
</script>

<div class="page container anim-cascade">
	<header class="set-head">
		<a class="set-back" href="{base}/profile" aria-label="Назад">
			<PixelIcon name="arrowleft" size="md" color="var(--text)" />
		</a>
		<h1 class="set-title">Настройки</h1>
		<span class="set-headgear" aria-hidden="true"><PixelIcon name="gear" size="md" color="var(--accent)" /></span>
	</header>

	<!-- Игра -->
	<section class="set-section">
		<h3 class="set-section__t">Игра</h3>
		<div class="set-list">
			<button class="set-row" onclick={toggleSound}>
				<PixelIcon name="bell" size="md" color="var(--accent)" />
				<div class="set-row__text">
					<span class="set-row__title">Звук</span>
					<span class="set-row__hint">8-битные сигналы на тренировке</span>
				</div>
				<span class="set-toggle" class:on={soundOn}>{soundOn ? 'Вкл' : 'Выкл'}</span>
			</button>

			<button class="set-row" onclick={toggleLeaderboard} disabled={lbBusy}>
				<PixelIcon name="trophy" size="md" color="var(--gold)" />
				<div class="set-row__text">
					<span class="set-row__title">Виден в рейтинге</span>
					<span class="set-row__hint">Показывать тебя в общем рейтинге и у друзей</span>
				</div>
				<span class="set-toggle" class:on={lbVisible}>{lbVisible ? 'Вкл' : 'Выкл'}</span>
			</button>

			<div class="set-block">
				<div class="set-block__head">
					<PixelIcon name="target" size="md" color="var(--accent2)" />
					<div class="set-row__text">
						<span class="set-row__title">Дневная норма</span>
						<span class="set-row__hint">Цель XP в день — по ней раскрашивается календарь активности (4 уровня заливки).</span>
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
					<span class="set-unit">XP</span>
					<button class="set-save" disabled={normSaving} onclick={handleSaveNorm}>
						{normSaving ? '...' : 'Сохранить'}
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
		<h3 class="set-section__t">Уведомления</h3>
		<div class="set-list">
			<button class="set-row" onclick={toggleNotif} disabled={notifBusy}>
				<PixelIcon name="mail" size="md" color="var(--accent)" />
				<div class="set-row__text">
					<span class="set-row__title">Напоминания в Telegram</span>
					<span class="set-row__hint">Пуш о тренировке и при простое 3+ дня</span>
				</div>
				<span class="set-toggle" class:on={notifOn}>{notifOn ? 'Вкл' : 'Выкл'}</span>
			</button>

			{#if notifOn}
				<div class="set-block">
					<div class="set-block__head">
						<PixelIcon name="clock" size="md" color="var(--accent2)" />
						<div class="set-row__text">
							<span class="set-row__title">Время напоминания</span>
							<span class="set-row__hint">Придёт в выбранный час, если не тренировался в этот день</span>
						</div>
					</div>
					<div class="set-controls">
						<input class="set-input" type="time" bind:value={timeInput} />
						<button class="set-save" disabled={timeSaving || !timeInput} onclick={handleSaveTime}>
							{timeSaving ? '...' : 'Сохранить'}
						</button>
					</div>
					{#if timeMessage}
						<p class="set-msg">{timeMessage}</p>
					{/if}
				</div>
			{/if}
		</div>
	</section>

	<!-- Аккаунт -->
	<section class="set-section">
		<h3 class="set-section__t">Аккаунт</h3>

		{#if accountMessage}
			<div class="account-success">{accountMessage}</div>
		{/if}

		{#if hasAccountInfo}
			<div class="account-info">
				{#if userStore.user?.email}
					<div class="account-row">
						<span class="account-label">Email</span>
						<span class="account-value">{userStore.user.email}</span>
					</div>
				{/if}
				{#if userStore.user?.telegram_id}
					<div class="account-row">
						<span class="account-label">Telegram</span>
						<span class="account-value">ID: {userStore.user.telegram_id}</span>
					</div>
				{/if}
			</div>
		{/if}

		<div class="account-actions">
			{#if !userStore.hasTelegram}
				<button class="account-btn" onclick={openLink}>
					Привязать Telegram
				</button>
			{/if}

			{#if userStore.authMode === 'web'}
				<button class="account-btn logout-btn" onclick={handleLogout}>
					Выйти
				</button>
			{/if}
		</div>
	</section>
</div>

<!-- Link Telegram Modal -->
<PixelModal
	open={showLinkTelegram}
	title="Привязать Telegram"
	onclose={() => { showLinkTelegram = false; accountError = null; }}
>
	<div class="modal-instructions">
		<p>1. Начните диалог с ботом <b>@pixelfitbot</b></p>
		<p>2. Введите ваш Telegram ID ниже</p>
		<p>3. Подтвердите привязку в Telegram</p>
	</div>
	<form class="modal-form" onsubmit={(e) => { e.preventDefault(); handleLinkTelegram(); }}>
		<div class="modal-field">
			<label for="tg-id">Telegram ID</label>
			<input id="tg-id" type="text" bind:value={telegramIdInput} placeholder="Например: 123456789" required />
		</div>
		{#if accountError}
			<div class="modal-error">{accountError}</div>
		{/if}
		<button type="submit" class="modal-submit" disabled={accountLoading}>
			{accountLoading ? 'Отправка...' : 'Отправить запрос'}
		</button>
	</form>
</PixelModal>

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

	/* Account (moved from profile) */
	.account-success {
		padding: var(--spacing-sm);
		background: var(--bg2);
		border: var(--bw) solid var(--green);
		font-size: var(--font-size-xs);
		color: var(--green);
		margin-bottom: var(--spacing-sm);
	}
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
	.account-btn {
		padding: 10px var(--spacing-md);
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		color: var(--accent);
		font-family: var(--font-ui);
		font-size: var(--font-size-xs);
		cursor: pointer;
		text-align: left;
		box-shadow: var(--shadow);
	}
	.account-btn:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}
	.logout-btn {
		color: var(--danger);
	}

	/* Link Telegram modal */
	.modal-form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-sm) 0;
	}
	.modal-field {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.modal-field label {
		font-size: var(--font-size-xs);
		color: var(--muted);
	}
	.modal-field input {
		padding: 10px 12px;
		background: var(--bg3);
		border: var(--bw) solid var(--line);
		color: var(--text);
		font-size: 14px;
		outline: none;
	}
	.modal-field input:focus {
		border-color: var(--accent);
	}
	.modal-error {
		color: var(--danger);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs);
	}
	.modal-submit {
		padding: 12px;
		background: var(--accent);
		border: none;
		color: var(--on-accent);
		font-family: var(--font-ui);
		font-size: var(--font-size-xs);
		cursor: pointer;
	}
	.modal-submit:active:not(:disabled) {
		transform: translate(2px, 2px);
	}
	.modal-submit:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	.modal-instructions {
		padding: var(--spacing-sm) 0;
		font-size: 12px;
		color: var(--muted);
		line-height: 1.6;
	}
	.modal-instructions p {
		margin: 4px 0;
	}
</style>
