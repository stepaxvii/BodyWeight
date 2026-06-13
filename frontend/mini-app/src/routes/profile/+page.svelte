<script lang="ts">
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { PixelCard, PixelProgress, PixelIcon, PixelAvatar, PixelModal, AvatarPicker, CountUp } from '$lib/components/ui';
	import ActivityBarChart from '$lib/components/ActivityBarChart.svelte';
	import TitlePicker from '$lib/components/TitlePicker.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { Achievement, AvatarId, UserActivity, DayActivity, UserRecords } from '$lib/types';

	let achievements = $state<Achievement[]>([]);
	let showAvatarPicker = $state(false);
	let activityData = $state<UserActivity | null>(null);
	let chartRange = $state<'week' | '2weeks' | 'month' | '3months'>('week');
	let selectedDay = $state<{ date: string; activity: DayActivity | null } | null>(null);
	let showTitlePicker = $state(false);
	let records = $state<UserRecords | null>(null);

	// Streak freeze (must match backend STREAK_FREEZE_PRICE_COINS / MAX_STREAK_FREEZES)
	const STREAK_FREEZE_PRICE = 500;
	const MAX_STREAK_FREEZES = 2;
	let freezeBuying = $state(false);
	let freezeMessage = $state<string | null>(null);

	// Daily activity norm (XP/day target that colours the activity calendar)
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

	async function handleBuyFreeze() {
		if (freezeBuying) return;
		freezeBuying = true;
		freezeMessage = null;
		try {
			await userStore.buyStreakFreeze();
			telegram.hapticNotification('success');
			freezeMessage = '🧊 Заморозка куплена!';
		} catch (err) {
			telegram.hapticNotification('error');
			freezeMessage = err instanceof Error ? err.message : 'Не удалось купить';
		} finally {
			freezeBuying = false;
		}
	}

	// Account settings
	let showLinkTelegram = $state(false);
	let telegramIdInput = $state('');
	let accountMessage = $state<string | null>(null);
	let accountError = $state<string | null>(null);
	let accountLoading = $state(false);

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

	onMount(async () => {
		await userStore.loadStats();
		normInput = userStore.dailyActivityNorm;

		try {
			achievements = await api.getAllAchievements();
		} catch (err) {
			console.error('Failed to load achievements:', err);
		}

		try {
			activityData = await api.getUserActivity();
		} catch (err) {
			console.error('Failed to load activity data:', err);
		}

		try {
			records = await api.getUserRecords();
		} catch (err) {
			console.error('Failed to load records:', err);
		}
	});

	// Sort by unlock date (newest first)
	const unlockedAchievements = $derived(
		achievements
			.filter(a => a.unlocked)
			.sort((a, b) => {
				if (!a.unlocked_at || !b.unlocked_at) return 0;
				return new Date(b.unlocked_at).getTime() - new Date(a.unlocked_at).getTime();
			})
	);
	const unlockedCount = $derived(unlockedAchievements.length);

	// Level XP calculation - use store computed values
	const xpInLevel = $derived(userStore.xp - userStore.xpForCurrentLevel);
	const xpNeeded = $derived(userStore.xpForNextLevel - userStore.xpForCurrentLevel);

	function openAvatarPicker() {
		showAvatarPicker = true;
		telegram.hapticImpact('light');
	}

	function handleAvatarSelect(avatarId: AvatarId) {
		userStore.setAvatar(avatarId);
	}

	function handleDayClick(date: string, activity: DayActivity | null) {
		selectedDay = { date, activity };
		telegram.hapticImpact('light');
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('ru-RU', {
			day: 'numeric',
			month: 'long',
			year: 'numeric'
		});
	}

	function fmtDuration(seconds: number): string {
		const m = Math.floor(seconds / 60);
		const s = seconds % 60;
		return `${m}:${String(s).padStart(2, '0')}`;
	}

	const hasRecords = $derived(
		!!records &&
			(!!records.best_set ||
				!!records.best_workout ||
				records.longest_workout_seconds > 0 ||
				records.max_streak > 0)
	);

	function openTitlePicker() {
		showTitlePicker = true;
		telegram.hapticImpact('light');
	}
</script>

<div class="page container anim-cascade">
	<!-- Character sheet header (mocha hero) -->
	<section class="hero-section">
		<header class="char">
			<div class="char__top">
				<button class="char__avbtn" aria-label="Сменить аватар" onclick={openAvatarPicker}>
					<span class="char__avslot slot slot--lg">
						<PixelAvatar avatarId={userStore.user?.avatar_id || 'shadow-wolf'} size="lg" showBorder={false} />
					</span>
					<span class="char__edit"><PixelIcon name="edit" size="sm" color="#fff" /></span>
				</button>
				<div class="char__id">
					<span class="char__name">{userStore.displayName}</span>
					<button class="char__title char__title--btn" onclick={openTitlePicker} aria-label="Сменить титул">
						<PixelIcon name="crown" size="sm" color="var(--gold)" />
						{userStore.user?.equipped_title || 'Выбрать титул'}
					</button>
					<span class="char__lvl">Уровень {userStore.level}</span>
				</div>
			</div>
			<div class="char__xp">
				<PixelProgress value={xpInLevel} max={xpNeeded} variant="xp" size="sm" />
				<div class="char__xprow">
					<span>{xpInLevel} / {xpNeeded} XP</span>
					<span>до Ур.{userStore.level + 1}</span>
				</div>
			</div>
			<div class="char__facts">
				<span class="char__fact"><PixelIcon name="flame" size="sm" color="var(--danger)" /> Серия {userStore.streak}</span>
				<span class="char__fact"><PixelIcon name="medal" size="sm" color="var(--gold)" /> Рекорд {userStore.user?.max_streak || 0}</span>
				<span class="char__fact"><PixelIcon name="coin" size="sm" color="var(--gold)" /> {userStore.coins}</span>
			</div>
		</header>
	</section>

	<!-- Avatar Picker Modal -->
	<AvatarPicker
		open={showAvatarPicker}
		currentAvatarId={userStore.user?.avatar_id || 'shadow-wolf'}
		onselect={handleAvatarSelect}
		onclose={() => showAvatarPicker = false}
	/>

	<!-- Title Picker (roadmap 1.2) -->
	<TitlePicker open={showTitlePicker} onclose={() => (showTitlePicker = false)} />

	<!-- Activity bar chart: week / 2 weeks / month -->
	{#if activityData}
		<section class="activity-chart-section">
			<h3 class="chart-section-title">Активность</h3>
			<div class="chart-controls">
				<div class="chart-range-btns">
					<button
						class="range-btn"
						class:active={chartRange === 'week'}
						onclick={() => { chartRange = 'week'; telegram.hapticImpact('light'); }}
					>
						7 дней
					</button>
					<button
						class="range-btn"
						class:active={chartRange === '2weeks'}
						onclick={() => { chartRange = '2weeks'; telegram.hapticImpact('light'); }}
					>
						14 дней
					</button>
					<button
						class="range-btn"
						class:active={chartRange === 'month'}
						onclick={() => { chartRange = 'month'; telegram.hapticImpact('light'); }}
					>
						30 дней
					</button>
					<button
						class="range-btn"
						class:active={chartRange === '3months'}
						onclick={() => { chartRange = '3months'; telegram.hapticImpact('light'); }}
					>
						90 дней
					</button>
				</div>
			</div>
			<PixelCard padding="md">
				<ActivityBarChart
					activityData={activityData.days}
					range={chartRange}
					onDayClick={handleDayClick}
				/>
			</PixelCard>
		</section>
	{/if}

	<!-- Daily activity norm -->
	<section class="norm-section">
		<h3 class="section-title">Дневная норма</h3>
		<div class="norm-card">
			<p class="norm-hint">Цель XP в день — по ней раскрашивается календарь активности (4 уровня заливки).</p>
			<div class="norm-controls">
				<input
					class="norm-input"
					type="number"
					min="100"
					max="100000"
					step="50"
					bind:value={normInput}
				/>
				<span class="norm-unit">XP</span>
				<button class="norm-save" disabled={normSaving} onclick={handleSaveNorm}>
					{normSaving ? '...' : 'Сохранить'}
				</button>
			</div>
			{#if normMessage}
				<p class="norm-message">{normMessage}</p>
			{/if}
		</div>
	</section>

	<!-- Stats band -->
	<section class="stats-section">
		<div class="band3">
			<div class="band3__i">
				<PixelIcon name="xp" size="sm" color="var(--accent)" />
				<span class="band3__v"><CountUp value={userStore.xp} /></span>
				<span class="band3__l">XP</span>
			</div>
			<div class="band3__i">
				<PixelIcon name="coin" size="sm" color="var(--gold)" class="anim-coin-spin" />
				<span class="band3__v"><CountUp value={userStore.coins} /></span>
				<span class="band3__l">Монеты</span>
			</div>
			<div class="band3__i">
				<PixelIcon name="streak" size="sm" color="var(--danger)" class="anim-flicker" />
				<span class="band3__v"><CountUp value={userStore.streak} /></span>
				<span class="band3__l">Серия</span>
			</div>
			<div class="band3__i">
				<PixelIcon name="trophy" size="sm" color="var(--gold)" />
				<span class="band3__v"><CountUp value={unlockedCount} /></span>
				<span class="band3__l">Значки</span>
			</div>
		</div>
	</section>

	<!-- Personal records (roadmap 2.3) -->
	{#if hasRecords && records}
		<section class="records-section">
			<h3 class="section-title">Личные рекорды</h3>
			<div class="rec-grid">
				<div class="rec">
					<PixelIcon name="dumbbell" size="md" color="var(--accent)" />
					<span class="rec__v">{records.best_set ? records.best_set.value : '—'}</span>
					<span class="rec__l">Лучший подход</span>
					<span class="rec__sub">{records.best_set ? records.best_set.exercise_name_ru : 'нет данных'}</span>
				</div>
				<div class="rec">
					<PixelIcon name="flame" size="md" color="var(--danger)" />
					<span class="rec__v">{records.best_workout ? records.best_workout.value : '—'}</span>
					<span class="rec__l">Рекорд за трен.</span>
					<span class="rec__sub">{records.best_workout ? records.best_workout.exercise_name_ru : 'нет данных'}</span>
				</div>
				<div class="rec">
					<PixelIcon name="timer" size="md" color="var(--accent2)" />
					<span class="rec__v">{fmtDuration(records.longest_workout_seconds)}</span>
					<span class="rec__l">Дольше всего</span>
					<span class="rec__sub">одна тренировка</span>
				</div>
				<div class="rec">
					<PixelIcon name="medal" size="md" color="var(--gold)" />
					<span class="rec__v">{records.max_streak}</span>
					<span class="rec__l">Макс. серия</span>
					<span class="rec__sub">дней подряд</span>
				</div>
			</div>
		</section>
	{/if}

	<!-- Unlocked Badges -->
	{#if unlockedAchievements.length > 0}
		<section class="badges-section">
			<div class="badges-card">
				<div class="badges-header">
					<PixelIcon name="trophy" size="md" color="var(--pixel-accent)" />
					<span class="badges-title">Значки</span>
					<span class="badges-count">{unlockedCount}/{achievements.length}</span>
				</div>
				<div class="badges-grid anim-rows">
					{#each unlockedAchievements.slice(0, 16) as achievement}
						<div class="badge-item" title={achievement.name_ru}>
							<img
								src="{base}/sprites/badges/{achievement.slug}.svg"
								alt={achievement.name_ru}
								class="badge-icon"
							/>
						</div>
					{/each}
					{#if achievements.length - unlockedCount > 0 || unlockedAchievements.length > 16}
						<a href="{base}/achievements" class="badge-item badge-more">
							<span>+{achievements.length - Math.min(unlockedCount, 16)}</span>
						</a>
					{/if}
				</div>
			</div>
		</section>
	{/if}

	<!-- Streak Info - Compact -->
	<section class="streak-section">
		<div class="streak-card">
			<div class="streak-left">
				<PixelIcon name="streak" size="lg" color="var(--pixel-yellow)" />
				<div class="streak-numbers">
					<span class="streak-current">{userStore.streak} дней</span>
					<span class="streak-max">Рекорд: {userStore.user?.max_streak || 0}</span>
				</div>
			</div>
			<div class="streak-visual">
				{#each Array(7) as _, i}
					<div class="streak-day" class:active={i < Math.min(userStore.streak, 7)}></div>
				{/each}
			</div>
		</div>

		<div class="freeze-card">
			<div class="freeze-left">
				<span class="freeze-icon"><PixelIcon name="snowflake" size="lg" color="var(--accent2)" /></span>
				<div class="freeze-numbers">
					<span class="freeze-title">Заморозки: {userStore.streakFreezes}/{MAX_STREAK_FREEZES}</span>
					<span class="freeze-hint">Спасают серию за пропущенный день</span>
				</div>
			</div>
			<button
				class="freeze-buy"
				disabled={freezeBuying || userStore.streakFreezes >= MAX_STREAK_FREEZES || userStore.coins < STREAK_FREEZE_PRICE}
				onclick={handleBuyFreeze}
			>
				{#if userStore.streakFreezes >= MAX_STREAK_FREEZES}
					Максимум
				{:else}
					{STREAK_FREEZE_PRICE} <PixelIcon name="coin" size="sm" color="var(--gold)" />
				{/if}
			</button>
		</div>
		{#if freezeMessage}
			<p class="freeze-message">{freezeMessage}</p>
		{/if}
	</section>

	<!-- Quick Link - Friends -->
	<section class="links-section">
		<a href="{base}/friends" class="link-item">
			<PixelCard hoverable>
				<div class="link-content">
					<PixelIcon name="friend" color="var(--pixel-cyan)" />
					<span>Друзья</span>
				</div>
			</PixelCard>
		</a>
	</section>

	<!-- Account Settings -->
	<section class="account-section">
		<h3 class="section-title">Аккаунт</h3>

		{#if accountMessage}
			<div class="account-success">{accountMessage}</div>
		{/if}

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

		<div class="account-actions">
			{#if !userStore.hasTelegram}
				<button class="account-btn" onclick={() => { showLinkTelegram = true; accountError = null; }}>
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

<!-- Day details modal (from bar chart click) -->
<PixelModal
	open={selectedDay !== null}
	title={selectedDay ? formatDate(selectedDay.date) : ''}
	onclose={() => selectedDay = null}
>
	{#if selectedDay?.activity}
		<div class="day-details">
			<div class="day-stat">
				<PixelIcon name="workout" size="md" color="var(--pixel-accent)" />
				<div class="day-stat-content">
					<span class="day-stat-label">Тренировки</span>
					<span class="day-stat-value">{selectedDay.activity.workouts}</span>
				</div>
			</div>
			<div class="day-stat">
				<PixelIcon name="xp" size="md" color="var(--pixel-blue)" />
				<div class="day-stat-content">
					<span class="day-stat-label">XP заработано</span>
					<span class="day-stat-value">{selectedDay.activity.total_xp}</span>
				</div>
			</div>
		</div>
	{:else}
		<div class="no-activity">
			<PixelIcon name="calendar" size="lg" color="var(--text-muted)" />
			<p>Нет тренировок в этот день</p>
		</div>
	{/if}
</PixelModal>

<style>
	.page {
		padding-top: var(--spacing-md);
		padding-bottom: var(--spacing-lg);
	}

	/* Character sheet header — .char / .char__* live in hud.css */
	.hero-section {
		margin-bottom: var(--spacing-md);
	}

	/* Gold XP fill on the dark mocha track (matches the designer's char segbar) */
	.char :global(.pixel-progress.xp .track) {
		background: rgba(0, 0, 0, 0.25);
		border-color: var(--hero-edge);
	}
	.char :global(.pixel-progress.xp .bar) {
		background: var(--gold);
	}

	/* Sections */
	.section-title {
		font-size: var(--font-size-sm);
		margin-bottom: var(--spacing-sm);
		text-transform: uppercase;
	}

	/* Activity chart section */
	.activity-chart-section {
		margin-bottom: var(--spacing-md);
	}

	.chart-section-title {
		font-size: var(--font-size-sm);
		text-transform: uppercase;
		margin: 0 0 var(--spacing-sm) 0;
	}

	.chart-controls {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-sm);
	}

	.chart-range-btns {
		display: flex;
		gap: 4px;
	}

	.range-btn {
		padding: 6px 10px;
		font-size: var(--font-size-xs);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all 0.15s;
	}

	.range-btn:hover {
		border-color: var(--pixel-accent);
		color: var(--text-primary);
	}

	.range-btn.active {
		background: var(--pixel-accent);
		border-color: var(--border-color);
		color: var(--on-accent);
	}

	/* Daily activity norm */
	.norm-section {
		margin-bottom: var(--spacing-md);
	}

	.norm-card {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		box-shadow: var(--shadow-md);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.norm-hint {
		font-size: 10px;
		color: var(--text-secondary);
		margin: 0 0 var(--spacing-sm) 0;
		line-height: 1.5;
	}

	.norm-controls {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.norm-input {
		flex: 1;
		min-width: 0;
		padding: 8px 10px;
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--border-color);
		color: var(--text-primary);
		font-family: inherit;
		font-size: 14px;
		outline: none;
	}

	.norm-input:focus {
		border-color: var(--pixel-accent);
	}

	.norm-unit {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.norm-save {
		padding: 8px var(--spacing-md);
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--pixel-accent);
		color: var(--pixel-accent);
		font-family: inherit;
		font-size: var(--font-size-xs);
		cursor: pointer;
		white-space: nowrap;
	}

	.norm-save:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.norm-message {
		font-size: 10px;
		color: var(--text-secondary);
		margin: var(--spacing-sm) 0 0 0;
		text-align: center;
	}

	/* Stats Row - compact horizontal */
	.stats-section {
		margin-bottom: var(--spacing-md);
	}

	/* stats now use the global .band3 kit */

	/* Personal records (roadmap 2.3) — neo pixel tiles, matching .band3 aesthetic */
	.records-section {
		margin-bottom: var(--spacing-md);
	}
	.rec-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-sm);
	}
	.rec {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		padding: 12px 8px;
		text-align: center;
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
	}
	.rec__v {
		font-family: var(--font-data);
		font-size: 22px;
		color: var(--text);
		line-height: 1;
		margin-top: 2px;
	}
	.rec__l {
		font-family: var(--font-display);
		font-size: 11px;
		color: var(--muted);
	}
	.rec__sub {
		font-size: 10px;
		color: var(--dim);
		max-width: 100%;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	/* Tappable title chip (roadmap 1.2) — reuses .char__title visuals from hud.css */
	.char__title--btn {
		border: none;
		cursor: pointer;
		color: inherit;
	}

	/* Badges Section */
	.badges-section {
		margin-bottom: var(--spacing-md);
	}

	.badges-card {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		box-shadow: var(--shadow-md);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.badges-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		margin-bottom: var(--spacing-sm);
	}

	.badges-title {
		font-size: var(--font-size-sm);
		flex: 1;
	}

	.badges-count {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.badges-grid {
		display: grid;
		grid-template-columns: repeat(9, 1fr);
		gap: 4px;
	}

	.badge-item {
		aspect-ratio: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pixel-yellow);
		border: var(--border-width) solid var(--border-color);
		transition: transform var(--transition-fast);
	}

	.badge-item:hover {
		transform: scale(1.1);
		border-color: var(--pixel-accent);
	}

	.badge-icon {
		width: 70%;
		height: 70%;
		image-rendering: pixelated;
	}

	.badge-more {
		background: var(--pixel-bg-dark);
		text-decoration: none;
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.badge-more:hover {
		color: var(--pixel-accent);
		border-color: var(--pixel-accent);
	}

	/* Streak Section - Compact */
	.streak-section {
		margin-bottom: var(--spacing-md);
	}

	.streak-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		box-shadow: var(--shadow-md);
		padding: var(--spacing-sm) var(--spacing-md);
	}

	.streak-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.streak-numbers {
		display: flex;
		flex-direction: column;
	}

	.streak-current {
		font-size: var(--font-size-sm);
		font-family: var(--font-display);
		color: var(--pixel-yellow);
	}

	.streak-max {
		font-size: 10px;
		color: var(--text-secondary);
	}

	.streak-visual {
		display: flex;
		gap: 4px;
	}

	.streak-day {
		width: 16px;
		height: 16px;
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--border-color);
	}

	.streak-day.active {
		border-color: var(--pixel-green);
		background: var(--pixel-green);
	}

	/* Streak freeze */
	.freeze-card {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		box-shadow: var(--shadow-md);
		padding: var(--spacing-sm) var(--spacing-md);
		margin-top: var(--spacing-sm);
	}

	.freeze-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.freeze-icon {
		font-size: 20px;
	}

	.freeze-numbers {
		display: flex;
		flex-direction: column;
	}

	.freeze-title {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
	}

	.freeze-hint {
		font-size: 10px;
		color: var(--text-secondary);
	}

	.freeze-buy {
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--pixel-yellow);
		color: var(--pixel-yellow);
		padding: var(--spacing-sm);
		font-family: inherit;
		font-size: var(--font-size-sm);
		cursor: pointer;
		white-space: nowrap;
	}

	.freeze-buy:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		border-color: var(--border-color);
		color: var(--text-secondary);
	}

	.freeze-message {
		font-size: 10px;
		color: var(--text-secondary);
		margin-top: var(--spacing-sm);
		text-align: center;
	}

	/* Links Section */
	.links-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-sm);
	}

	.link-item {
		text-decoration: none;
	}

	.link-content {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		font-size: var(--font-size-sm);
		text-transform: uppercase;
	}

	.link-count {
		margin-left: auto;
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	/* Day details modal */
	.day-details {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-sm) 0;
	}

	.day-stat {
		display: flex;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--border-color);
	}

	.day-stat-content {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.day-stat-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.day-stat-value {
		font-size: var(--font-size-md);
		color: var(--text-primary);
	}

	.no-activity {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-md);
		padding: var(--spacing-xl);
		color: var(--text-muted);
		text-align: center;
	}

	.no-activity p {
		margin: 0;
		font-size: var(--font-size-sm);
	}

	/* Account Section */
	.account-section {
		margin-bottom: var(--spacing-md);
	}

	.account-success {
		padding: var(--spacing-sm);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--pixel-green);
		font-size: var(--font-size-xs);
		color: var(--pixel-green);
		margin-bottom: var(--spacing-sm);
	}

	.account-info {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		box-shadow: var(--shadow-md);
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
		border-top: 1px solid var(--border-color);
	}

	.account-label {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
	}

	.account-value {
		font-size: var(--font-size-xs);
		color: var(--text-primary);
	}

	.account-actions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.account-btn {
		padding: 10px var(--spacing-md);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		color: var(--pixel-accent);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		cursor: pointer;
		text-align: left;
		transition: border-color 0.2s;
	}

	.account-btn:hover {
		border-color: var(--pixel-accent);
	}

	.logout-btn {
		color: var(--pixel-red);
	}

	.logout-btn:hover {
		border-color: var(--pixel-red);
	}

	/* Modal form styles */
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
		color: var(--text-secondary);
	}

	.modal-field input {
		padding: 10px 12px;
		background: var(--pixel-bg-dark);
		border: var(--border-width) solid var(--border-color);
		color: var(--text-primary);
		font-size: 14px;
		outline: none;
	}

	.modal-field input:focus {
		border-color: var(--pixel-accent);
	}

	.modal-error {
		color: var(--pixel-red);
		font-size: var(--font-size-xs);
		padding: var(--spacing-xs);
	}

	.modal-submit {
		padding: 12px;
		background: var(--pixel-accent);
		border: none;
		color: var(--on-accent);
		font-family: var(--font-pixel);
		font-size: var(--font-size-xs);
		cursor: pointer;
	}

	.modal-submit:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.modal-instructions {
		padding: var(--spacing-sm) 0;
		font-size: 12px;
		color: var(--text-secondary);
		line-height: 1.6;
	}

	.modal-instructions p {
		margin: 4px 0;
	}
</style>
