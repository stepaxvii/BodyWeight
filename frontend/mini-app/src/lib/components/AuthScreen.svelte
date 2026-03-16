<script lang="ts">
	import { userStore } from '$lib/stores/user.svelte';

	let mode = $state<'login' | 'register'>('login');
	let email = $state('');
	let password = $state('');
	let username = $state('');
	let firstName = $state('');
	let error = $state<string | null>(null);
	let isSubmitting = $state(false);

	async function handleLogin() {
		error = null;
		isSubmitting = true;
		try {
			await userStore.webLogin(email, password);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Ошибка входа';
		} finally {
			isSubmitting = false;
		}
	}

	async function handleRegister() {
		error = null;

		if (password.length < 6) {
			error = 'Пароль должен быть не менее 6 символов';
			return;
		}

		isSubmitting = true;
		try {
			await userStore.webRegister({
				email,
				password,
				username: username || undefined,
				first_name: firstName || undefined,
			});
		} catch (err) {
			error = err instanceof Error ? err.message : 'Ошибка регистрации';
		} finally {
			isSubmitting = false;
		}
	}

	function switchMode() {
		mode = mode === 'login' ? 'register' : 'login';
		error = null;
	}
</script>

<div class="auth-screen">
	<div class="auth-container">
		<div class="auth-header">
			<h1 class="auth-title">PixelFit</h1>
			<p class="auth-subtitle">8-bit Фитнес Трекер</p>
		</div>

		<div class="auth-tabs">
			<button
				class="auth-tab"
				class:active={mode === 'login'}
				onclick={() => { mode = 'login'; error = null; }}
			>
				Вход
			</button>
			<button
				class="auth-tab"
				class:active={mode === 'register'}
				onclick={() => { mode = 'register'; error = null; }}
			>
				Регистрация
			</button>
		</div>

		<form
			class="auth-form"
			onsubmit={(e) => { e.preventDefault(); mode === 'login' ? handleLogin() : handleRegister(); }}
		>
			{#if mode === 'register'}
				<div class="field">
					<label for="firstName">Имя</label>
					<input
						id="firstName"
						type="text"
						bind:value={firstName}
						placeholder="Ваше имя"
						autocomplete="given-name"
					/>
				</div>
				<div class="field">
					<label for="username">Username</label>
					<input
						id="username"
						type="text"
						bind:value={username}
						placeholder="Уникальный username"
						autocomplete="username"
					/>
				</div>
			{/if}

			<div class="field">
				<label for="email">
					{mode === 'login' ? 'Email или username' : 'Email'}
				</label>
				<input
					id="email"
					type={mode === 'login' ? 'text' : 'email'}
					bind:value={email}
					placeholder={mode === 'login' ? 'Email или telegram username' : 'your@email.com'}
					required
					autocomplete={mode === 'login' ? 'username' : 'email'}
				/>
			</div>

			<div class="field">
				<label for="password">Пароль</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					placeholder={mode === 'register' ? 'Минимум 6 символов' : 'Ваш пароль'}
					required
					minlength={mode === 'register' ? 6 : undefined}
					autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
				/>
			</div>

			{#if error}
				<div class="error-message">{error}</div>
			{/if}

			<button
				type="submit"
				class="submit-btn"
				disabled={isSubmitting}
			>
				{#if isSubmitting}
					<span class="spinner"></span>
				{:else}
					{mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
				{/if}
			</button>
		</form>

		<div class="auth-footer">
			<button class="switch-btn" onclick={switchMode}>
				{mode === 'login' ? 'Нет аккаунта? Зарегистрируйтесь' : 'Уже есть аккаунт? Войдите'}
			</button>
		</div>

		<div class="tg-hint">
			<p>Или откройте через Telegram бота</p>
			<p class="bot-name">@pixelfitbot</p>
		</div>

		<div class="pwa-hint">
			<p>Установите как приложение:</p>
			<p>iOS: Поделиться → На экран «Домой»</p>
			<p>Android: Меню → Установить приложение</p>
		</div>
	</div>
</div>

<style>
	.auth-screen {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-bg, #1a1a2e);
		padding: 20px;
	}

	.auth-container {
		width: 100%;
		max-width: 380px;
	}

	.auth-header {
		text-align: center;
		margin-bottom: 32px;
	}

	.auth-title {
		font-family: 'Press Start 2P', cursive;
		font-size: 24px;
		color: var(--pixel-accent, #e94560);
		margin-bottom: 8px;
	}

	.auth-subtitle {
		color: var(--pixel-text-secondary, #8b8b9e);
		font-size: 12px;
		font-family: 'Press Start 2P', cursive;
	}

	.auth-tabs {
		display: flex;
		gap: 0;
		margin-bottom: 24px;
		border: 2px solid var(--border-color, #2a2a4a);
		border-radius: 8px;
		overflow: hidden;
	}

	.auth-tab {
		flex: 1;
		padding: 10px;
		background: transparent;
		border: none;
		color: var(--pixel-text-secondary, #8b8b9e);
		font-family: 'Press Start 2P', cursive;
		font-size: 10px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.auth-tab.active {
		background: var(--pixel-accent, #e94560);
		color: white;
	}

	.auth-form {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.field label {
		font-size: 11px;
		font-family: 'Press Start 2P', cursive;
		color: var(--pixel-text, #e0e0e0);
	}

	.field input {
		padding: 12px;
		background: var(--pixel-card-bg, #16213e);
		border: 2px solid var(--border-color, #2a2a4a);
		border-radius: 8px;
		color: var(--pixel-text, #e0e0e0);
		font-size: 14px;
		outline: none;
		transition: border-color 0.2s;
	}

	.field input:focus {
		border-color: var(--pixel-accent, #e94560);
	}

	.field input::placeholder {
		color: var(--pixel-text-secondary, #8b8b9e);
		opacity: 0.6;
	}

	.error-message {
		color: var(--pixel-danger, #ff4757);
		font-size: 11px;
		font-family: 'Press Start 2P', cursive;
		text-align: center;
		padding: 8px;
		background: rgba(255, 71, 87, 0.1);
		border-radius: 6px;
	}

	.submit-btn {
		padding: 14px;
		background: var(--pixel-accent, #e94560);
		border: none;
		border-radius: 8px;
		color: white;
		font-family: 'Press Start 2P', cursive;
		font-size: 11px;
		cursor: pointer;
		transition: opacity 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 48px;
	}

	.submit-btn:hover:not(:disabled) {
		opacity: 0.9;
	}

	.submit-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.spinner {
		width: 20px;
		height: 20px;
		border: 3px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.auth-footer {
		text-align: center;
		margin-top: 16px;
	}

	.switch-btn {
		background: none;
		border: none;
		color: var(--pixel-accent, #e94560);
		font-size: 11px;
		cursor: pointer;
		text-decoration: underline;
		padding: 8px;
	}

	.tg-hint {
		text-align: center;
		margin-top: 32px;
		padding-top: 24px;
		border-top: 1px solid var(--border-color, #2a2a4a);
	}

	.tg-hint p {
		color: var(--pixel-text-secondary, #8b8b9e);
		font-size: 11px;
		margin-bottom: 4px;
	}

	.bot-name {
		font-family: 'Press Start 2P', cursive;
		color: var(--pixel-accent, #e94560) !important;
		font-size: 10px !important;
	}

	.pwa-hint {
		text-align: center;
		margin-top: 16px;
		padding: 12px;
		background: rgba(233, 69, 96, 0.08);
		border: 1px solid var(--border-color, #2a2a4a);
		border-radius: 8px;
	}

	.pwa-hint p {
		color: var(--pixel-text-secondary, #8b8b9e);
		font-size: 10px;
		margin-bottom: 4px;
		line-height: 1.6;
	}

	.pwa-hint p:last-child {
		margin-bottom: 0;
	}
</style>
