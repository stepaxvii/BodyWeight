<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { PixelButton, PixelCard, PixelIcon, PixelAvatar, EmptyState } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import type {
		ChallengeDetails,
		ChallengeCalendar,
		ChallengeDayProgress,
		ChallengeParticipant
	} from '$lib/types';

	const challengeId = $derived(parseInt($page.params.id));

	let details = $state<ChallengeDetails | null>(null);
	let myCalendar = $state<ChallengeCalendar | null>(null);
	let loading = $state(true);
	let joining = $state(false);
	let claiming = $state(false);
	let toast = $state<string | null>(null);

	async function load() {
		loading = true;
		try {
			details = await api.getChallenge(challengeId);
			if (details.is_member) {
				myCalendar = await api.getChallengeCalendar(challengeId);
			} else {
				myCalendar = null;
			}
		} catch (e) {
			console.error('Failed to load challenge:', e);
			details = null;
		} finally {
			loading = false;
		}
	}

	onMount(load);

	async function handleJoin() {
		if (!details || joining) return;
		joining = true;
		try {
			details = await api.joinChallenge(challengeId);
			myCalendar = await api.getChallengeCalendar(challengeId);
			toast = 'Ты участвуешь!';
			telegram.hapticNotification('success');
		} catch (e) {
			toast = e instanceof Error ? e.message : 'Не удалось присоединиться';
			telegram.hapticNotification('error');
		} finally {
			joining = false;
		}
	}

	async function handleClaim() {
		if (!details || claiming) return;
		claiming = true;
		try {
			const result = await api.claimChallengeReward(challengeId);
			toast = `Получено: +${result.coins_awarded} монет!`;
			telegram.hapticNotification('success');
			await userStore.loadStats();
			await load();
		} catch (e) {
			toast = e instanceof Error ? e.message : 'Не удалось забрать награду';
			telegram.hapticNotification('error');
		} finally {
			claiming = false;
		}
	}

	function fmtDate(iso: string): string {
		return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
	}

	function statusLabel(s: string): string {
		if (s === 'upcoming') return 'Скоро';
		if (s === 'active') return 'Идёт';
		return 'Завершён';
	}

	function todayIso(): string {
		return new Date().toISOString().split('T')[0];
	}

	// Build a 2D grid of days × exercises for the calendar visualization
	const dayCells = $derived.by(() => {
		if (!details) return [];
		const start = new Date(details.start_date);
		const end = new Date(details.end_date);
		const days: { iso: string; label: number; isToday: boolean }[] = [];
		for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
			const iso = d.toISOString().split('T')[0];
			days.push({ iso, label: d.getDate(), isToday: iso === todayIso() });
		}
		return days;
	});

	// Map progress lookups for fast access
	const progressByKey = $derived.by(() => {
		const m = new Map<string, ChallengeDayProgress>();
		if (!myCalendar) return m;
		for (const r of myCalendar.rows) {
			m.set(`${r.progress_date}::${r.exercise_id}`, r);
		}
		return m;
	});

	// Per-day completion summary for personal grid (all exercises completed?)
	const dayStatus = $derived.by(() => {
		if (!details) return new Map<string, 'full' | 'partial' | 'none' | 'future'>();
		const m = new Map<string, 'full' | 'partial' | 'none' | 'future'>();
		const today = todayIso();
		for (const cell of dayCells) {
			if (cell.iso > today) {
				m.set(cell.iso, 'future');
				continue;
			}
			let any = false;
			let allDone = true;
			for (const ex of details.exercises) {
				const r = progressByKey.get(`${cell.iso}::${ex.exercise_id}`);
				if (r && r.completed) {
					any = true;
				} else {
					allDone = false;
					if (r && r.accumulated > 0) any = true;
				}
			}
			if (allDone && details.exercises.length > 0) m.set(cell.iso, 'full');
			else if (any) m.set(cell.iso, 'partial');
			else m.set(cell.iso, 'none');
		}
		return m;
	});

	const todayProgress = $derived.by(() => {
		if (!details) return [];
		const today = todayIso();
		return details.exercises.map((ex) => {
			const r = progressByKey.get(`${today}::${ex.exercise_id}`);
			return {
				ex,
				accumulated: r?.accumulated ?? 0,
				target: ex.daily_target,
				completed: r?.completed ?? false
			};
		});
	});

	function isMe(p: ChallengeParticipant): boolean {
		return p.user_id === userStore.user?.id;
	}
</script>

<div class="detail-page">
	<header class="page-header">
		<a href="{base}/challenges" class="back-link">
			<PixelIcon name="arrow-left" size="sm" />
		</a>
		<h1>Челлендж</h1>
	</header>

	{#if loading}
		<div class="loading">Загрузка...</div>
	{:else if !details}
		<EmptyState title="Не найдено" message="Челлендж не существует или удалён" />
	{:else}
		<PixelCard padding="md">
			<div class="hero">
				<div class="hero-top">
					<h2 class="hero-title">{details.title}</h2>
					<div class="status-pill status-{details.status}">{statusLabel(details.status)}</div>
				</div>
				<div class="hero-meta">
					<span>{fmtDate(details.start_date)} → {fmtDate(details.end_date)}</span>
					<span class="dot">•</span>
					<span>{details.duration_days} дн.</span>
					{#if details.creator_name}
						<span class="dot">•</span>
						<span>от @{details.creator_name}</span>
					{/if}
				</div>
				{#if details.description}
					<p class="hero-desc">{details.description}</p>
				{/if}
			</div>

			<div class="exercise-targets">
				{#each details.exercises as ex (ex.exercise_id)}
					<div class="ex-target">
						<span class="ex-name">{ex.exercise_name_ru}</span>
						<span class="ex-target-val">
							{ex.daily_target}
							{#if ex.is_timed}сек{:else if ex.exercise_slug === 'walking'}шагов{:else}повт.{/if}
							/ день
						</span>
					</div>
				{/each}
			</div>

			{#if details.can_join}
				<PixelButton variant="success" fullWidth loading={joining} onclick={handleJoin}>
					Присоединиться
				</PixelButton>
			{:else if details.status === 'upcoming' && details.is_member}
				<div class="info-msg">Ты в челлендже. Старт {fmtDate(details.start_date)}.</div>
			{:else if details.status === 'active' && !details.is_member}
				<div class="info-msg muted">Челлендж уже идёт — присоединиться нельзя, но можно следить.</div>
			{/if}
		</PixelCard>

		{#if details.is_member && details.status === 'active'}
			<PixelCard padding="md">
				<h3 class="section-title">Сегодня</h3>
				<div class="today-list">
					{#each todayProgress as t}
						<div class="today-row" class:done={t.completed}>
							<span class="today-name">{t.ex.exercise_name_ru}</span>
							<div class="today-bar-wrap">
								<div
									class="today-bar"
									style="width: {Math.min(100, (t.accumulated / t.target) * 100)}%"
								></div>
							</div>
							<span class="today-val">{t.accumulated} / {t.target}</span>
						</div>
					{/each}
				</div>
			</PixelCard>
		{/if}

		{#if myCalendar && details.is_member}
			<PixelCard padding="md">
				<h3 class="section-title">Твой календарь</h3>
				<div class="calendar-grid">
					{#each dayCells as cell (cell.iso)}
						{@const st = dayStatus.get(cell.iso) ?? 'none'}
						<div
							class="cal-cell cal-{st}"
							class:cal-today={cell.isToday}
							title={cell.iso}
						>
							{cell.label}
						</div>
					{/each}
				</div>
				<div class="cal-legend">
					<span><span class="lg lg-full"></span>Полностью</span>
					<span><span class="lg lg-partial"></span>Частично</span>
					<span><span class="lg lg-none"></span>Пропуск</span>
					<span><span class="lg lg-future"></span>Впереди</span>
				</div>
			</PixelCard>
		{/if}

		{#if details.finalized_at && details.is_member}
			{@const me = details.participants.find(isMe)}
			{#if me && me.reward_claimable}
				<PixelCard padding="md">
					<div class="claim-block">
						<div class="claim-info">
							<div class="claim-coins">+{me.reward_coins} монет</div>
							<div class="claim-stat">
								Выполнено: <b>{me.completion_percent}%</b> ({me.completed_days} дн.)
							</div>
						</div>
						<PixelButton variant="success" loading={claiming} onclick={handleClaim}>
							Забрать
						</PixelButton>
					</div>
				</PixelCard>
			{:else if me && me.reward_claimed_at}
				<div class="info-msg muted">Награда забрана: {me.reward_coins} монет ({me.completion_percent}%)</div>
			{/if}
		{/if}

		<PixelCard padding="md">
			<h3 class="section-title">Участники ({details.participants.length})</h3>
			<div class="part-list">
				{#each details.participants as p (p.user_id)}
					<div class="part-row" class:part-me={isMe(p)}>
						<PixelAvatar avatarId={p.avatar_id || 'shadow-wolf'} size="sm" />
						<div class="part-info">
							<div class="part-name">
								{p.username || p.first_name || 'Игрок'}
								{#if isMe(p)}<span class="me-tag">(ты)</span>{/if}
							</div>
							<div class="part-pct-bar">
								<div class="part-pct-fill" style="width: {p.completion_percent}%"></div>
							</div>
						</div>
						<div class="part-pct">{p.completion_percent}%</div>
					</div>
				{/each}
			</div>
		</PixelCard>

		{#if toast}
			<div class="toast">{toast}</div>
		{/if}
	{/if}
</div>

<style>
	.detail-page {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
	}

	.page-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
	}

	.page-header h1 {
		font-size: var(--font-size-md);
		color: var(--text-primary);
		margin: 0;
		flex: 1;
	}

	.back-link {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		padding: var(--spacing-xs);
		display: flex;
		align-items: center;
		justify-content: center;
		text-decoration: none;
		color: var(--text-primary);
	}

	.loading {
		text-align: center;
		color: var(--text-muted);
		padding: var(--spacing-lg);
	}

	.hero-top {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: var(--spacing-sm);
	}

	.hero-title {
		font-size: var(--font-size-md);
		color: var(--text-primary);
		margin: 0;
	}

	.status-pill {
		font-size: 9px;
		padding: 2px 6px;
		border: 1px solid var(--border-color);
		text-transform: uppercase;
		letter-spacing: 1px;
		flex-shrink: 0;
	}

	.status-upcoming {
		color: var(--pixel-accent);
		border-color: var(--pixel-accent);
	}
	.status-active {
		color: var(--pixel-green);
		border-color: var(--pixel-green);
	}
	.status-finished {
		color: var(--text-muted);
	}

	.hero-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 4px;
		font-size: 11px;
		color: var(--text-muted);
	}

	.dot {
		opacity: 0.5;
	}

	.hero-desc {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		line-height: 1.5;
		margin: var(--spacing-sm) 0 0 0;
	}

	.exercise-targets {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin: var(--spacing-md) 0;
		padding: var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
	}

	.ex-target {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: var(--font-size-xs);
	}

	.ex-name {
		color: var(--text-primary);
	}

	.ex-target-val {
		color: var(--pixel-accent);
	}

	.info-msg {
		font-size: var(--font-size-xs);
		color: var(--text-secondary);
		text-align: center;
		padding: var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
	}

	.info-msg.muted {
		color: var(--text-muted);
	}

	.section-title {
		font-size: var(--font-size-sm);
		color: var(--text-primary);
		margin: 0 0 var(--spacing-sm) 0;
	}

	/* Today list */
	.today-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.today-row {
		display: grid;
		grid-template-columns: 1fr auto;
		grid-template-rows: auto auto;
		gap: 4px var(--spacing-sm);
		align-items: center;
	}

	.today-name {
		grid-column: 1;
		font-size: var(--font-size-xs);
	}

	.today-val {
		grid-column: 2;
		font-size: 10px;
		color: var(--text-muted);
		text-align: right;
	}

	.today-bar-wrap {
		grid-column: 1 / -1;
		height: 6px;
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
	}

	.today-bar {
		height: 100%;
		background: var(--pixel-accent);
		transition: width 0.3s ease;
	}

	.today-row.done .today-bar {
		background: var(--pixel-green);
	}

	.today-row.done .today-val {
		color: var(--pixel-green);
	}

	/* Calendar */
	.calendar-grid {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 4px;
	}

	.cal-cell {
		aspect-ratio: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 10px;
		font-family: var(--font-pixel);
		color: var(--text-muted);
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
		min-height: 32px;
	}

	.cal-full {
		background: var(--pixel-green);
		color: #fff;
		border-color: var(--pixel-green);
	}

	.cal-partial {
		background: var(--pixel-yellow);
		color: var(--stat-text);
		border-color: var(--pixel-yellow);
	}

	.cal-none {
		background: var(--pixel-bg-dark);
		color: var(--text-muted);
		opacity: 0.6;
	}

	.cal-future {
		background: transparent;
		color: var(--text-muted);
		opacity: 0.4;
	}

	.cal-today {
		outline: var(--border-width) solid var(--pixel-accent);
		outline-offset: calc(-1 * var(--border-width));
	}

	.cal-legend {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-sm);
		margin-top: var(--spacing-sm);
		font-size: 10px;
		color: var(--text-muted);
	}

	.cal-legend span {
		display: flex;
		align-items: center;
		gap: 4px;
	}

	.lg {
		display: inline-block;
		width: 10px;
		height: 10px;
		border: 1px solid var(--border-color);
	}

	.lg-full {
		background: var(--pixel-green);
	}
	.lg-partial {
		background: var(--pixel-yellow);
	}
	.lg-none {
		background: var(--pixel-bg-dark);
	}
	.lg-future {
		background: transparent;
	}

	/* Claim */
	.claim-block {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--spacing-sm);
	}

	.claim-coins {
		font-size: var(--font-size-md);
		color: var(--pixel-yellow);
	}

	.claim-stat {
		font-size: 10px;
		color: var(--text-muted);
	}

	/* Participants */
	.part-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-xs);
	}

	.part-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		padding: var(--spacing-xs) var(--spacing-sm);
		background: var(--pixel-bg-dark);
		border: 1px solid var(--border-color);
	}

	.part-me {
		border-color: var(--pixel-accent);
	}

	.part-info {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.part-name {
		font-size: var(--font-size-xs);
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.me-tag {
		font-size: 9px;
		color: var(--pixel-accent);
		margin-left: 4px;
	}

	.part-pct-bar {
		height: 4px;
		background: var(--pixel-card);
		border: 1px solid var(--border-color);
		overflow: hidden;
	}

	.part-pct-fill {
		height: 100%;
		background: var(--pixel-green);
		transition: width 0.4s ease;
	}

	.part-pct {
		font-size: var(--font-size-xs);
		color: var(--pixel-accent);
		min-width: 36px;
		text-align: right;
	}

	.toast {
		position: fixed;
		bottom: 80px;
		left: 50%;
		transform: translateX(-50%);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--pixel-accent);
		padding: var(--spacing-sm) var(--spacing-md);
		font-size: var(--font-size-xs);
		color: var(--text-primary);
		z-index: 100;
	}
</style>
