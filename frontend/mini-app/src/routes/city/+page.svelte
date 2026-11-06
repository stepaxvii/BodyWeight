<script lang="ts">
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount, onDestroy, tick } from 'svelte';
	import { PixelButton, PixelIcon } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { userStore } from '$lib/stores/user.svelte';
	import { cityStore } from '$lib/city/city.svelte';
	import { t, ln } from '$lib/i18n/index.svelte';
	import type { DistrictResponse, DistrictDialogueLine, DistrictStatus, Friend } from '$lib/types';
	import { ISO_MAP, pctX, pctY } from '$lib/city/iso';
	import type { Rect } from '$lib/city/render/sprites';
	import { loadAvatarHead } from '$lib/city/render/heroAvatar';
	import { drawYard } from '$lib/city/render/scenes/yard';
	import { drawFrench } from '$lib/city/render/scenes/french';
	import { drawCossack } from '$lib/city/render/scenes/cossack';

	// District scene canvas buffer (low-res; CSS upscales with `pixelated`).
	const DISTRICT_W = 200,
		DISTRICT_H = 356;

	// 'landing' is the stats hub the route opens to; 'map' is the iso district map;
	// 'travel' is the brief fade between map and a scene; 'district' is a scene.
	type Mode = 'landing' | 'map' | 'travel' | 'district';

	// Scene key → detailed renderer. downtown/port have no scene (locked stubs).
	// The 3rd arg is the player's avatar as the hero head (null → default fox).
	const SCENE_RENDERERS: Record<
		string,
		(ctx: CanvasRenderingContext2D, t: number, heroAv: Rect[] | null) => void
	> = {
		yard: drawYard,
		french: drawFrench,
		cossack: drawCossack
	};

	// The player's avatar parsed into a hero head once on mount; null keeps the fox.
	let heroAv = $state<Rect[] | null>(null);

	let canvasEl = $state<HTMLCanvasElement | null>(null);
	let ctx: CanvasRenderingContext2D | null = null;
	let rafId = 0;
	const reduce =
		typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;

	let mode = $state<Mode>('landing');
	let loading = $state(true);
	// Beta gate: non-admins (city_enabled=false) get a localized "coming soon" stub
	// and never call the access-gated /api/districts. The layout guarantees the user
	// is loaded before this route mounts, so reading it in onMount is safe.
	const cityEnabled = $derived(userStore.user?.city_enabled === true);
	// id of the district the player is currently on (marked "you are here" on the map).
	let playerId = $state<string>('home');
	// id of the district whose scene is being shown (district mode).
	let currentId = $state<string | null>(null);
	// id of the district the callout is open for (map mode).
	let selectedId = $state<string | null>(null);

	let fadeAlpha = $state(0);
	let busy = $state(false);
	let toastMsg = $state<string | null>(null);
	let toastTimer: ReturnType<typeof setTimeout> | null = null;

	// ---- co-op friend invite (inviter side; only ever shown on coop districts) ----
	let pickerOpen = $state(false);
	let friendsLoading = $state(false);
	let friends = $state<Friend[]>([]);

	// ---- derived views ----
	const selectedDistrict = $derived<DistrictResponse | undefined>(cityStore.get(selectedId));
	const currentDistrict = $derived<DistrictResponse | undefined>(cityStore.get(currentId));
	const currentProgress = $derived(currentDistrict?.quest_progress ?? null);
	const currentIsActive = $derived(currentDistrict?.status === 'active');
	const incomingInvite = $derived(currentDistrict?.incoming_invite ?? null);
	// Co-op surfaces appear ONLY on districts flagged coop (none of the solo v1 set).
	const coopEnabled = $derived(currentDistrict?.coop === true);

	// ---- iso map overlay nodes (anchored to the base-image art via ISO_MAP) ----
	type OverlayNode = {
		id: string;
		name: string;
		status: DistrictStatus;
		isPlayer: boolean;
		cx: number;
		cy: number;
		lx: number;
		ly: number;
		bx: number;
		by: number;
	};
	const overlayNodes = $derived<OverlayNode[]>(
		cityStore.districts
			.filter((d) => ISO_MAP.districts[d.id])
			.map((d) => {
				const a = ISO_MAP.districts[d.id];
				return {
					id: d.id,
					name: ln(d.name, d.name_ru),
					status: d.status,
					isPlayer: d.id === playerId,
					cx: pctX(a.center[0]),
					cy: pctY(a.center[1]),
					lx: pctX(a.label[0]),
					ly: pctY(a.label[1]),
					bx: pctX(a.badge[0]),
					by: pctY(a.badge[1])
				};
			})
	);

	// ---- landing (stats hub) derivations ----
	const allDistricts = $derived(cityStore.districts);
	const totalDistricts = $derived(allDistricts.length);
	const openedCount = $derived(allDistricts.filter((d) => d.status !== 'locked').length);
	const clearedCount = $derived(allDistricts.filter((d) => d.status === 'completed').length);
	const activeDistrict = $derived(allDistricts.find((d) => d.status === 'active'));
	const earnedTitles = $derived(
		allDistricts.filter((d) => d.status === 'completed' && d.quest?.reward?.title)
	);

	// ---- JRPG dialogue state machine (district mode) ----
	type TalkPhase = 'idle' | 'intro' | 'offer';
	let talkPhase = $state<TalkPhase>('idle');
	let introIndex = $state(0);

	const introLines = $derived<DistrictDialogueLine[]>(
		Array.isArray(currentDistrict?.dialogue?.intro)
			? (currentDistrict.dialogue.intro as DistrictDialogueLine[])
			: []
	);
	const currentLine = $derived<DistrictDialogueLine | null>(introLines[introIndex] ?? null);
	const hasIntro = $derived(introLines.length > 0);

	// Reset the dialogue machine to 'idle' whenever we land on a new district.
	$effect(() => {
		void currentId;
		talkPhase = 'idle';
		introIndex = 0;
	});

	// ---- tween engine ----
	type Tween = { t0: number | null; dur: number; upd: (p: number) => void; done?: () => void };
	let tweens: Tween[] = [];
	const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
	const ease = (p: number) => (p < 0.5 ? 2 * p * p : 1 - (-2 * p + 2) ** 2 / 2);

	function tween(dur: number, upd: (p: number) => void, done?: () => void) {
		if (reduce) {
			upd(1);
			done?.();
			return;
		}
		tweens.push({ t0: null, dur, upd, done });
	}

	function stepTweens(now: number) {
		for (let i = tweens.length - 1; i >= 0; i--) {
			const tw = tweens[i];
			if (tw.t0 == null) tw.t0 = now;
			const p = clamp((now - tw.t0) / tw.dur, 0, 1);
			tw.upd(ease(p));
			if (p >= 1) {
				tweens.splice(i, 1);
				tw.done?.();
			}
		}
	}

	// ---- district scene canvas ----
	function sizeCanvas() {
		if (!canvasEl) return;
		canvasEl.width = DISTRICT_W;
		canvasEl.height = DISTRICT_H;
		ctx = canvasEl.getContext('2d');
		if (ctx) ctx.imageSmoothingEnabled = false;
	}

	function render(now: number) {
		stepTweens(now);
		if (mode !== 'district' || !ctx || !currentId) return;
		try {
			const renderer = SCENE_RENDERERS[currentDistrict?.scene ?? ''];
			if (renderer) renderer(ctx, now, heroAv);
		} catch (e) {
			console.error('[city] render error', e);
		}
	}

	function loop(now: number) {
		render(now);
		rafId = requestAnimationFrame(loop);
	}

	function startLoop() {
		if (reduce) {
			render(9000);
			return;
		}
		cancelAnimationFrame(rafId);
		rafId = requestAnimationFrame(loop);
	}

	// Under prefers-reduced-motion there is no rAF loop; redraw one fixed scene
	// frame whenever the shown district changes.
	$effect(() => {
		void currentId;
		if (reduce && ctx && mode === 'district') render(9000);
	});

	// ---- toast ----
	function toast(msg: string) {
		toastMsg = msg;
		if (toastTimer) clearTimeout(toastTimer);
		toastTimer = setTimeout(() => (toastMsg = null), 1800);
	}

	// ---- navigation ----
	// Back button is context-aware so the player never "falls to home" unexpectedly:
	//   district → back to the map, map → back to the stats hub, hub → leave the feature.
	function goBack() {
		if (mode === 'travel') return; // mid-transition; ignore until the scene settles
		if (mode === 'district') {
			leaveDistrict();
		} else if (mode === 'map') {
			telegram.hapticSelection();
			selectedId = null;
			mode = 'landing';
		} else {
			goto(`${base}/`);
		}
	}

	const backTitle = $derived(
		mode === 'district' && currentDistrict
			? ln(currentDistrict.name, currentDistrict.name_ru)
			: t('city.title')
	);

	function enterCity() {
		telegram.hapticSelection();
		selectedId = null;
		mode = 'map';
	}

	// ---- map interactions ----
	function selectNode(id: string) {
		telegram.hapticSelection();
		selectedId = id;
	}

	function closeCallout() {
		selectedId = null;
	}

	// ---- travel: fade out the map, mount + fade in the district scene ----
	function travelTo(d: DistrictResponse) {
		if (d.status === 'locked') return;
		selectedId = null;
		playerId = d.id;
		telegram.hapticImpact('medium');
		mode = 'travel';
		tween(
			420,
			(p) => (fadeAlpha = p),
			async () => {
				currentId = d.id;
				mode = 'district';
				await tick(); // canvas only mounts in district mode → wait for it
				sizeCanvas();
				startLoop();
				fadeAlpha = 1;
				tween(420, (p) => (fadeAlpha = 1 - p));
			}
		);
	}

	function leaveDistrict() {
		const d = currentDistrict;
		telegram.hapticImpact('light');
		tween(
			380,
			(p) => (fadeAlpha = p),
			() => {
				if (d) playerId = d.id;
				mode = 'map';
				currentId = null;
				selectedId = null;
				ctx = null; // canvas unmounts with district mode; drop the stale context
				tween(380, (p) => (fadeAlpha = 1 - p));
			}
		);
	}

	// ---- quest actions ----
	async function acceptQuest() {
		const d = currentDistrict;
		if (!d || busy) return;
		busy = true;
		try {
			await api.acceptQuest(d.id);
			await cityStore.reloadDistrict(d.id);
			toast(t('city.questAccepted'));
			telegram.hapticNotification('success');
		} catch (e) {
			console.error('[city] acceptQuest failed', e);
			telegram.hapticNotification('error');
			toast(t('city.actionError'));
		} finally {
			busy = false;
		}
	}

	async function abandonQuest() {
		const d = currentDistrict;
		if (!d || busy) return;
		busy = true;
		try {
			await api.abandonQuest(d.id);
			await cityStore.reloadDistrict(d.id);
			toast(t('city.questAbandoned'));
			telegram.hapticNotification('warning');
		} catch (e) {
			console.error('[city] abandonQuest failed', e);
			telegram.hapticNotification('error');
			toast(t('city.actionError'));
		} finally {
			busy = false;
		}
	}

	async function hireMercenary() {
		const d = currentDistrict;
		if (!d || busy) return;
		busy = true;
		try {
			await api.hireMercenary(d.id, 'fire-fox');
			await cityStore.reloadDistrict(d.id);
			toast(t('city.mercenaryHired'));
			telegram.hapticNotification('success');
		} catch (e) {
			console.error('[city] hireMercenary failed', e);
			telegram.hapticNotification('error');
			toast(t('city.actionError'));
		} finally {
			busy = false;
		}
	}

	// ---- co-op: invite a friend (inviter side) ----
	function friendName(f: Friend): string {
		return f.username || f.first_name || `#${f.user_id}`;
	}

	async function openPicker() {
		if (busy) return;
		pickerOpen = true;
		friendsLoading = true;
		telegram.hapticSelection();
		try {
			const all = await api.getFriends();
			friends = all.filter((f) => f.status === 'accepted');
		} catch (e) {
			console.error('[city] getFriends failed', e);
			friends = [];
			toast(t('city.actionError'));
		} finally {
			friendsLoading = false;
		}
	}

	function closePicker() {
		pickerOpen = false;
	}

	async function inviteFriend(friend: Friend) {
		const d = currentDistrict;
		if (!d || busy) return;
		busy = true;
		try {
			// If the quest isn't active yet, accept it first so an instance exists to
			// attach the pending participant to.
			if (d.status !== 'active') {
				await api.acceptQuest(d.id);
			}
			await api.invitePartner(d.id, friend.user_id);
			await cityStore.reloadDistrict(d.id);
			pickerOpen = false;
			toast(t('city.inviteSent'));
			telegram.hapticNotification('success');
		} catch (e) {
			console.error('[city] invitePartner failed', e);
			telegram.hapticNotification('error');
			toast(t('city.actionError'));
		} finally {
			busy = false;
		}
	}

	// ---- co-op: accept / decline an incoming invite (invitee side) ----
	async function acceptInvite() {
		const d = currentDistrict;
		if (!d || busy) return;
		busy = true;
		try {
			await api.acceptInvite(d.id);
			await cityStore.reloadDistrict(d.id);
			toast(t('city.inviteAccepted'));
			telegram.hapticNotification('success');
		} catch (e) {
			console.error('[city] acceptInvite failed', e);
			telegram.hapticNotification('error');
			toast(t('city.actionError'));
		} finally {
			busy = false;
		}
	}

	async function declineInvite() {
		const d = currentDistrict;
		if (!d || busy) return;
		busy = true;
		try {
			await api.declineInvite(d.id);
			await cityStore.reloadDistrict(d.id);
			toast(t('city.inviteDeclined'));
			telegram.hapticNotification('warning');
		} catch (e) {
			console.error('[city] declineInvite failed', e);
			telegram.hapticNotification('error');
			toast(t('city.actionError'));
		} finally {
			busy = false;
		}
	}

	// ---- dialogue advance (district mode) ----
	function advanceDialogue() {
		if (mode !== 'district' || !currentDistrict) return;
		if (incomingInvite) return; // never start a dialogue over an incoming invite

		if (talkPhase === 'idle') {
			telegram.hapticSelection();
			if (currentIsActive || !hasIntro) {
				talkPhase = currentIsActive ? 'intro' : 'offer';
			} else {
				introIndex = 0;
				talkPhase = 'intro';
			}
			return;
		}

		if (talkPhase === 'intro') {
			telegram.hapticSelection();
			if (currentIsActive) {
				talkPhase = 'offer';
				return;
			}
			if (introIndex < introLines.length - 1) {
				introIndex += 1;
			} else {
				talkPhase = 'offer';
			}
		}
	}

	// ---- helpers for overlays ----
	function dlg(d: DistrictResponse | undefined, key: string): string {
		const dict = d?.dialogue;
		if (!dict) return '';
		const en = dict[key];
		const ru = dict[`${key}_ru`];
		return ln(typeof en === 'string' ? en : undefined, typeof ru === 'string' ? ru : undefined);
	}

	function speakerName(d: DistrictResponse | undefined, line: DistrictDialogueLine): string {
		return line.speaker === 'boss' ? bossName(d) : t('city.hero');
	}

	function bossName(d: DistrictResponse | undefined): string {
		return ln(d?.boss?.name, d?.boss?.name_ru);
	}

	function muscle(d: DistrictResponse | undefined): string {
		return ln(d?.muscle, d?.muscle_ru);
	}

	function pct(acc: number, target: number): number {
		if (target <= 0) return 0;
		return Math.max(0, Math.min(100, Math.round((acc / target) * 100)));
	}

	// State → on-map badge glyph and a status label for the hub list.
	function badgeGlyph(s: DistrictStatus): string {
		return s === 'completed' ? '✓' : s === 'active' ? '⚔' : s === 'available' ? '!' : '🔒';
	}
	function statusLabel(s: DistrictStatus): string {
		return s === 'completed'
			? t('city.stCleared')
			: s === 'active'
				? t('city.stActive')
				: s === 'available'
					? t('city.stAvailable')
					: t('city.locked');
	}

	onMount(async () => {
		if (!cityEnabled) {
			// Non-admin during beta: show the stub, don't touch the gated API.
			loading = false;
			return;
		}
		// Parse the player's avatar into a hero head (best-effort; null keeps the fox).
		// 'shadow-wolf' matches the backend/model default when avatar_id is unset.
		loadAvatarHead(base, userStore.user?.avatar_id ?? 'shadow-wolf').then((h) => (heroAv = h));
		await cityStore.load();
		loading = false;
		// Mark the player on the first active/available district, else home.
		const start =
			cityStore.districts.find((d) => d.status === 'active') ??
			cityStore.districts.find((d) => d.status === 'available') ??
			cityStore.districts.find((d) => d.id === 'home') ??
			cityStore.districts[0];
		if (start) playerId = start.id;
		// The scene canvas only mounts in district mode, so there is nothing to size
		// yet. Start the rAF loop only to drive transition tweens (fades).
		if (!reduce) startLoop();
	});

	onDestroy(() => {
		cancelAnimationFrame(rafId);
		if (toastTimer) clearTimeout(toastTimer);
	});
</script>

<div class="city-page">
	<header class="page-header">
		<button class="back-link" onclick={goBack} aria-label={t('city.back')}>
			<PixelIcon name="arrow-left" size="sm" />
		</button>
		<h1>{backTitle}</h1>
	</header>

	{#snippet hubBanner(title: string, tagline?: string)}
		<div class="hub-banner">
			<img class="hub-banner-img" src="{base}/city/citymap_iso_base.png" alt="" aria-hidden="true" />
			<div class="hub-banner-fade"></div>
			<div class="hub-banner-text">
				<div class="hub-title">{title}</div>
				{#if tagline}<div class="hub-tagline">{tagline}</div>{/if}
			</div>
		</div>
	{/snippet}

	{#if loading}
		<div class="loading">{t('city.loading')}</div>
	{:else if !cityEnabled}
		<!-- ===================== BETA STUB (non-admins) ===================== -->
		<div class="landing">
			{@render hubBanner(t('city.comingSoonTitle'))}
			<div class="coming-soon">
				<div class="coming-soon-badge">🚧</div>
				<p class="coming-soon-body">{t('city.comingSoonBody')}</p>
			</div>
		</div>
	{:else if mode === 'landing'}
		<!-- ===================== STATS HUB ===================== -->
		<div class="landing">
			{@render hubBanner(t('city.title'), t('city.hubTagline'))}

			<div class="stat-row">
				<div class="stat">
					<div class="stat-num">{openedCount}/{totalDistricts}</div>
					<div class="stat-lbl">{t('city.statOpened')}</div>
				</div>
				<div class="stat">
					<div class="stat-num">{clearedCount}</div>
					<div class="stat-lbl">{t('city.statCleared')}</div>
				</div>
				<div class="stat">
					<div class="stat-num">{earnedTitles.length}</div>
					<div class="stat-lbl">{t('city.statTitles')}</div>
				</div>
			</div>

			{#if activeDistrict}
				<div class="active-card">
					<div class="active-tag">{t('city.activeQuestLabel')}</div>
					<div class="active-quest">
						{ln(activeDistrict.quest?.title, activeDistrict.quest?.title_ru)}
					</div>
					<div class="active-where">{ln(activeDistrict.name, activeDistrict.name_ru)}</div>
					{#if activeDistrict.quest_progress}
						<div class="active-day">
							{t('city.dayOf', {
								day: activeDistrict.quest_progress.full_days,
								total: activeDistrict.quest_progress.days
							})}
						</div>
					{/if}
				</div>
			{/if}

			<div class="dist-list">
				{#each allDistricts as d (d.id)}
					<div class="dist-row s-{d.status}">
						<span class="dist-badge">{badgeGlyph(d.status)}</span>
						<div class="dist-main">
							<span class="dist-name">{ln(d.name, d.name_ru)}</span>
							<span class="dist-muscle">{muscle(d)}</span>
						</div>
						<span class="dist-pill s-{d.status}">{statusLabel(d.status)}</span>
					</div>
				{/each}
			</div>

			<PixelButton variant="primary" onclick={enterCity}>
				{t('city.goOut')} →
			</PixelButton>
		</div>
	{:else}
		<!-- ===================== MAP / DISTRICT STAGE ===================== -->
		<div class="stage">
			{#if mode === 'district'}
				<canvas
					bind:this={canvasEl}
					class="city-canvas"
					onclick={advanceDialogue}
					aria-label={backTitle}
				></canvas>
			{:else}
				<!-- iso city map: static background art + percentage-anchored overlay -->
				<img class="map-bg" src="{base}/city/citymap_iso_base.png" alt="" aria-hidden="true" />
				<div class="map-overlay">
					{#each overlayNodes as n (n.id)}
						{#if n.isPlayer}
							<div class="here-ring" style="left:{n.cx}%; top:{n.cy}%"></div>
						{/if}
						<!-- The transparent hotspot is the single screen-reader control (name +
						     status); the visible label is a redundant touch target kept out of
						     the a11y tree / tab order so each district is one clean stop. -->
						<button
							class="hotspot"
							class:sel={selectedId === n.id}
							style="left:{n.cx}%; top:{n.cy}%"
							onclick={() => selectNode(n.id)}
							aria-label="{n.name} — {statusLabel(n.status)}"
						></button>
						<div class="dbadge s-{n.status}" style="left:{n.bx}%; top:{n.by}%" aria-hidden="true">
							{badgeGlyph(n.status)}
						</div>
						<button
							class="dlabel s-{n.status}"
							style="left:{n.lx}%; top:{n.ly}%"
							onclick={() => selectNode(n.id)}
							tabindex={-1}
							aria-hidden="true"
						>
							{n.name}
						</button>
					{/each}
				</div>
			{/if}

			<!-- top bar -->
			<div class="topbar">
				{#if mode === 'district' && currentDistrict}
					<span class="tb-title">{ln(currentDistrict.name, currentDistrict.name_ru)}</span>
					{#if !incomingInvite && talkPhase !== 'idle'}
						<button class="tb-leave" onclick={leaveDistrict}>{t('city.leave')}</button>
					{:else}
						<span class="tb-sub">{muscle(currentDistrict)}</span>
					{/if}
				{:else}
					<span class="tb-title">{t('city.title')}</span>
					<span class="tb-sub">{openedCount}/{totalDistricts}</span>
				{/if}
			</div>

			<!-- MAP: tap hint -->
			{#if mode === 'map' && !selectedDistrict}
				<div class="map-hint">{t('city.mapTapHint')}</div>
			{/if}

			<!-- MAP: district callout -->
			{#if mode === 'map' && selectedDistrict}
				<div class="callout">
					<div class="callout-head">
						<div class="callout-name">{ln(selectedDistrict.name, selectedDistrict.name_ru)}</div>
						<div class="callout-meta">
							{#if selectedDistrict.status === 'locked'}
								🔒 {t('city.locked')}
							{:else}
								💪 {muscle(selectedDistrict)} · {bossName(selectedDistrict)}
							{/if}
						</div>
					</div>
					<div class="callout-actions">
						{#if selectedDistrict.status !== 'locked'}
							<PixelButton variant="primary" size="sm" onclick={() => travelTo(selectedDistrict)}>
								{t('city.enter')}
							</PixelButton>
						{:else}
							<PixelButton variant="secondary" size="sm" disabled>
								{t('city.locked')}
							</PixelButton>
						{/if}
						<PixelButton variant="ghost" size="sm" onclick={closeCallout}>✕</PixelButton>
					</div>
				</div>
			{/if}

			<!-- DISTRICT: active quest HUD -->
			{#if mode === 'district' && currentDistrict && currentIsActive && currentProgress}
				<div class="qhud">
					<div class="qhud-title">
						{ln(currentDistrict.quest?.title, currentDistrict.quest?.title_ru)}
					</div>
					<div class="qhud-day">
						{t('city.dayOf', { day: currentProgress.full_days, total: currentProgress.days })}
					</div>
					{#if currentProgress.exercises}
						<div class="qhud-rows">
							{#each currentProgress.exercises as ex (ex.exercise_slug)}
								<div class="qhud-row">
									<div class="qhud-row-top">
										<span class="qhud-ex-name">{ln(ex.name, ex.name_ru)}</span>
										<span class="qhud-ex-num">
											{ex.accumulated}/{ex.daily_target}
											{#if ex.completed}<span class="qhud-check">✓</span>{/if}
										</span>
									</div>
									<div class="qbar">
										<div
											class="qbar-fill"
											class:done={ex.completed}
											style="width: {pct(ex.accumulated, ex.daily_target)}%"
										></div>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}

			<!-- DISTRICT: incoming co-op invite (invitee side) -->
			{#if mode === 'district' && currentDistrict && incomingInvite}
				<div class="invite-box">
					<div class="invite-who">{t('city.inviteReceivedTitle')}</div>
					<div class="invite-line">
						{t('city.inviteReceivedBy', { name: incomingInvite.inviter_name })}
					</div>
					<div class="invite-quest">
						{ln(incomingInvite.quest_title, incomingInvite.quest_title_ru)}
					</div>
					<div class="dbar-actions">
						<PixelButton variant="primary" size="sm" loading={busy} onclick={acceptInvite}>
							{t('city.inviteAccept')}
						</PixelButton>
						<PixelButton variant="danger" size="sm" loading={busy} onclick={declineInvite}>
							{t('city.inviteDecline')}
						</PixelButton>
					</div>
				</div>
			{/if}

			<!-- DISTRICT: slim "tap to talk" hint -->
			{#if mode === 'district' && currentDistrict && !incomingInvite && talkPhase === 'idle'}
				<div class="hint-strip">{t('city.tapToTalk')}</div>
			{/if}

			<!-- DISTRICT: slim JRPG dialogue bar — one line at a time -->
			{#if mode === 'district' && currentDistrict && !incomingInvite && talkPhase === 'intro'}
				<div
					class="talkbar"
					role="button"
					tabindex="0"
					onclick={advanceDialogue}
					onkeydown={(e) => (e.key === 'Enter' || e.key === ' ') && advanceDialogue()}
				>
					{#if currentIsActive}
						<div class="talkbar-who">{bossName(currentDistrict)}</div>
						<div class="talkbar-line">{dlg(currentDistrict, 'progress')}</div>
					{:else if currentLine}
						<div class="talkbar-who" class:hero={currentLine.speaker === 'hero'}>
							{speakerName(currentDistrict, currentLine)}
						</div>
						<div class="talkbar-line">{ln(currentLine.line, currentLine.line_ru)}</div>
					{/if}
					<div class="talkbar-next" aria-hidden="true">{t('city.next')}</div>
				</div>
			{/if}

			<!-- DISTRICT: offer / active-quest action box (shown AFTER the intro) -->
			{#if mode === 'district' && currentDistrict && !incomingInvite && talkPhase === 'offer'}
				<div class="dbar">
					<div class="dbar-who">
						{bossName(currentDistrict)}{#if currentIsActive} · {t('city.statusActive')}{/if}
					</div>

					{#if currentIsActive}
						<div class="dbar-line">{dlg(currentDistrict, 'progress')}</div>
						<div class="dbar-actions">
							<PixelButton variant="danger" size="sm" loading={busy} onclick={abandonQuest}>
								{t('city.abandon')}
							</PixelButton>
							<PixelButton variant="ghost" size="sm" onclick={leaveDistrict}>
								{t('city.leave')}
							</PixelButton>
						</div>
						{#if coopEnabled}
							<div class="dbar-coop">
								<PixelButton variant="secondary" size="sm" loading={busy} onclick={openPicker}>
									{t('city.inviteFriend')}
								</PixelButton>
							</div>
						{/if}
					{:else}
						<div class="dbar-line">{dlg(currentDistrict, 'offer')}</div>

						{#if currentDistrict.quest?.title}
							<div class="quest-info">
								<div class="quest-info-row">
									<PixelIcon name="target" size="sm" color="var(--gold, #e8bf48)" />
									<span class="quest-title">
										{ln(currentDistrict.quest.title, currentDistrict.quest.title_ru)}
									</span>
									{#if currentDistrict.quest.days}
										<span class="quest-days">
											{t('city.days', { days: currentDistrict.quest.days })}
										</span>
									{/if}
								</div>
								{#if currentDistrict.quest.reward}
									<div class="quest-reward">
										<span class="reward-label">{t('city.reward')}:</span>
										{#if currentDistrict.quest.reward.title}
											<span class="reward-title">
												{ln(
													currentDistrict.quest.reward.title,
													currentDistrict.quest.reward.title_ru
												)}
											</span>
										{/if}
										<span class="reward-xp">+{currentDistrict.quest.reward.xp} XP</span>
										<span class="reward-coins">+{currentDistrict.quest.reward.coins} 🪙</span>
									</div>
								{/if}
							</div>
						{/if}

						<div class="dbar-actions">
							<PixelButton variant="primary" size="sm" loading={busy} onclick={acceptQuest}>
								{t('city.acceptQuest')}
							</PixelButton>
							<PixelButton variant="ghost" size="sm" onclick={leaveDistrict}>
								{t('city.leave')}
							</PixelButton>
						</div>

						{#if coopEnabled}
							<div class="dbar-coop">
								<PixelButton variant="secondary" size="sm" loading={busy} onclick={openPicker}>
									{t('city.inviteFriend')}
								</PixelButton>
								<PixelButton variant="secondary" size="sm" loading={busy} onclick={hireMercenary}>
									{t('city.hireMercenary')}
								</PixelButton>
							</div>
						{/if}
					{/if}
				</div>
			{/if}

			<!-- Co-op: friend picker (inviter side) -->
			{#if pickerOpen}
				<div class="picker-backdrop">
					<div class="picker">
						<div class="picker-head">
							<span class="picker-title">{t('city.invitePickTitle')}</span>
							<PixelButton variant="ghost" size="sm" onclick={closePicker}>✕</PixelButton>
						</div>
						{#if friendsLoading}
							<div class="picker-empty">{t('city.loading')}</div>
						{:else if friends.length === 0}
							<div class="picker-empty">{t('city.inviteNoFriends')}</div>
						{:else}
							<div class="picker-list">
								{#each friends as f (f.user_id)}
									<button class="picker-item" disabled={busy} onclick={() => inviteFriend(f)}>
										<span class="picker-item-name">{friendName(f)}</span>
										<span class="picker-item-lvl">lvl {f.level}</span>
									</button>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			{/if}

			<!-- fade overlay for travel transitions -->
			<div class="fade" style="opacity: {fadeAlpha}"></div>

			{#if toastMsg}
				<div class="toast">{toastMsg}</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.city-page {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		padding: var(--spacing-md);
		align-items: center;
	}

	.page-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-sm);
		width: 100%;
	}

	.page-header h1 {
		font-size: var(--font-size-md);
		color: var(--text-primary);
		margin: 0;
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
		cursor: pointer;
	}

	.loading {
		text-align: center;
		color: var(--text-muted);
		padding: var(--spacing-lg);
	}

	/* ===================== STATS HUB ===================== */
	.landing {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-md);
		width: min(380px, 94vw);
	}

	.hub-banner {
		position: relative;
		height: 132px;
		overflow: hidden;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 0 0 0 3px #000, 0 10px 28px rgba(0, 0, 0, 0.55);
		background: #07080c;
	}

	.hub-banner-img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		object-position: 50% 24%;
		image-rendering: pixelated;
		display: block;
	}

	.hub-banner-fade {
		position: absolute;
		inset: 0;
		background: linear-gradient(180deg, rgba(7, 8, 12, 0.1) 0%, rgba(7, 8, 12, 0.88) 100%);
	}

	.hub-banner-text {
		position: absolute;
		left: 12px;
		right: 12px;
		bottom: 10px;
	}

	.hub-title {
		font-family: var(--font-display, monospace);
		font-size: 22px;
		font-weight: 700;
		letter-spacing: 0.08em;
		color: #efe6cf;
		text-shadow: 2px 2px 0 #000;
	}

	.hub-tagline {
		font-size: 10.5px;
		line-height: 1.45;
		color: #d8cbac;
		margin-top: 3px;
		text-shadow: 1px 1px 0 #000;
	}

	/* Beta "coming soon" stub (non-admins). */
	.coming-soon {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-sm);
		text-align: center;
		padding: var(--spacing-md) var(--spacing-sm);
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
	}

	.coming-soon-badge {
		font-size: 30px;
		line-height: 1;
	}

	.coming-soon-body {
		margin: 0;
		font-size: 12px;
		line-height: 1.55;
		color: var(--text-primary);
		max-width: 30ch;
	}

	.stat-row {
		display: flex;
		gap: var(--spacing-sm);
	}

	.stat {
		flex: 1;
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		padding: 10px 6px;
		text-align: center;
	}

	.stat-num {
		font-family: var(--font-data, monospace);
		font-size: 20px;
		font-weight: 700;
		color: var(--gold, #e8bf48);
	}

	.stat-lbl {
		font-size: 9px;
		color: var(--text-muted);
		margin-top: 3px;
		letter-spacing: 0.02em;
	}

	.active-card {
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
		border-left: 4px solid var(--gold, #e8bf48);
		padding: 9px 11px;
	}

	/* Shared gold "speaker / tag" chip (landing tag + the three dialogue name tabs). */
	.active-tag,
	.talkbar-who,
	.dbar-who,
	.invite-who {
		display: inline-block;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #1a1205;
		background: var(--gold, #e8bf48);
		padding: 1px 6px;
	}
	.active-tag {
		font-size: 8.5px;
	}
	.talkbar-who,
	.dbar-who,
	.invite-who {
		font-size: 9px;
		margin-bottom: 6px;
	}

	/* Alternating JRPG dialogue: the boss name tab sits on the RIGHT (gold, the
	   default above); the hero's own tab sits on the LEFT in a cool blue, so the
	   two speakers are told apart at a glance by side AND colour. */
	.talkbar-who {
		display: block;
		width: fit-content;
		margin-left: auto;
	}

	.talkbar-who.hero {
		margin-left: 0;
		color: #eaf2ff;
		background: #3a6ea5;
	}

	.active-quest {
		font-size: 13px;
		font-weight: 700;
		color: var(--text-primary);
		margin-top: 6px;
	}

	.active-where {
		font-size: 10px;
		color: var(--text-muted);
		margin-top: 1px;
	}

	.active-day {
		font-size: 10px;
		color: var(--gold, #c7a24a);
		margin-top: 4px;
		font-family: var(--font-data, monospace);
	}

	.dist-list {
		display: flex;
		flex-direction: column;
		gap: 5px;
	}

	.dist-row {
		display: flex;
		align-items: center;
		gap: 9px;
		padding: 8px 10px;
		background: var(--pixel-card);
		border: var(--border-width) solid var(--border-color);
	}

	.dist-row.s-locked {
		opacity: 0.55;
	}

	.dist-badge {
		font-size: 13px;
		width: 18px;
		text-align: center;
		flex-shrink: 0;
	}

	.dist-main {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-width: 0;
	}

	.dist-name {
		font-size: 12px;
		font-weight: 700;
		color: var(--text-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.dist-muscle {
		font-size: 9px;
		color: var(--text-muted);
	}

	.dist-pill {
		font-size: 8.5px;
		letter-spacing: 0.03em;
		text-transform: uppercase;
		padding: 2px 7px;
		flex-shrink: 0;
		border: 1px solid var(--border-color);
		color: var(--text-muted);
	}

	.dist-pill.s-completed {
		color: #2e7d46;
		border-color: #2e7d46;
	}

	.dist-pill.s-active {
		color: #1a1205;
		background: var(--gold, #e8bf48);
		border-color: var(--gold, #e8bf48);
	}

	.dist-pill.s-available {
		color: var(--gold, #c7a24a);
		border-color: var(--gold, #c7a24a);
	}

	/* ===================== MAP / DISTRICT STAGE ===================== */
	.stage {
		position: relative;
		width: min(380px, 94vw);
		aspect-ratio: 1080 / 1920;
		max-height: 82vh;
		overflow: hidden;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 0 0 0 3px #000, 0 12px 36px rgba(0, 0, 0, 0.6);
		background: #07080c;
	}

	.city-canvas {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		image-rendering: pixelated;
		display: block;
		cursor: pointer;
	}

	/* --- iso map background + overlay --- */
	.map-bg {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: fill;
		image-rendering: pixelated;
		display: block;
	}

	.map-overlay {
		position: absolute;
		inset: 0;
	}

	/* Transparent tap target over each plot (centre-anchored). Sizes are a touch-
	   ergonomic oval (intentionally larger than the drawn diamond), and clip-path
	   restricts the HIT AREA to that oval so the rectangular corners of adjacent
	   plots don't overlap and steal seam taps (border-radius alone doesn't clip
	   pointer hit-testing). */
	.hotspot {
		position: absolute;
		width: 26%;
		height: 15%;
		transform: translate(-50%, -50%);
		background: transparent;
		border: 0;
		padding: 0;
		cursor: pointer;
		border-radius: 50%;
		clip-path: ellipse(50% 50% at 50% 50%);
	}

	.hotspot:focus-visible {
		outline: 2px solid var(--gold, #e8bf48);
		outline-offset: -2px;
	}

	.hotspot.sel {
		background: radial-gradient(
			ellipse at center,
			rgba(232, 191, 72, 0.22) 0%,
			rgba(232, 191, 72, 0) 70%
		);
	}

	/* Name banner above each plot — crisp HTML text, styled per state. */
	.dlabel {
		position: absolute;
		transform: translate(-50%, -50%);
		white-space: nowrap;
		padding: 3px 8px;
		font-family: var(--font-display, monospace);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.02em;
		color: #efe6cf;
		background: #10131f;
		border: 2px solid #3a4150;
		box-shadow: 2px 2px 0 #000;
		cursor: pointer;
		z-index: 2;
	}

	.dlabel.s-active {
		border-color: var(--gold, #e8bf48);
	}

	.dlabel.s-completed {
		border-color: #2e7d46;
	}

	.dlabel.s-available {
		border-color: var(--gold, #c7a24a);
	}

	.dlabel.s-locked {
		color: #9aa0ad;
		border-color: #2a3240;
	}

	/* State badge chip above the banner. */
	.dbadge {
		position: absolute;
		transform: translate(-50%, -50%);
		width: 22px;
		height: 22px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 12px;
		line-height: 1;
		background: #10131f;
		border: 2px solid #3a4150;
		box-shadow: 2px 2px 0 #000;
		pointer-events: none;
		z-index: 2;
	}

	.dbadge.s-completed {
		color: #39d353;
		border-color: #2e7d46;
	}

	.dbadge.s-active {
		color: #1a1205;
		background: var(--gold, #e8bf48);
		border-color: var(--gold, #e8bf48);
	}

	.dbadge.s-available {
		color: var(--gold, #e8bf48);
		border-color: var(--gold, #c7a24a);
	}

	/* "You are here" pulsing ring on the player's current plot. */
	.here-ring {
		position: absolute;
		width: 30%;
		height: 17%;
		transform: translate(-50%, -50%);
		border: 2px solid var(--gold, #e8bf48);
		border-radius: 50%;
		box-shadow: 0 0 10px rgba(232, 191, 72, 0.4);
		pointer-events: none;
		z-index: 1;
		animation: herePulse 1.8s ease-in-out infinite;
	}

	@keyframes herePulse {
		0%,
		100% {
			opacity: 0.45;
			transform: translate(-50%, -50%) scale(1);
		}
		50% {
			opacity: 0.9;
			transform: translate(-50%, -50%) scale(1.06);
		}
	}

	/* Shared slim pulsing hint strip (map "tap a district" + district "tap to talk"). */
	.hint-strip,
	.map-hint {
		position: absolute;
		left: 10px;
		right: 10px;
		bottom: 10px;
		z-index: 2;
		padding: 6px 10px;
		background: rgba(12, 17, 32, 0.92);
		border: 2px solid var(--gold, #e8bf48);
		box-shadow: 3px 3px 0 #000;
		text-align: center;
		font-size: 10px;
		letter-spacing: 0.03em;
		color: #efe6cf;
		pointer-events: none;
		animation: hintPulse 1.8s ease-in-out infinite;
	}

	/* --- overlays (pixel boxes, dark to match the art) --- */
	.topbar {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		padding: 7px 10px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		background: rgba(12, 17, 32, 0.93);
		border-bottom: 2px solid var(--gold, #e8bf48);
		pointer-events: none;
		z-index: 3;
	}

	.tb-title {
		font-family: var(--font-display, monospace);
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: #efe6cf;
	}

	.tb-sub {
		font-size: 9px;
		color: var(--gold, #e8bf48);
		letter-spacing: 0.04em;
		font-family: var(--font-data, monospace);
	}

	/* Shared bottom-docked dark pixel box (district callout, dialogue box, invite). */
	.callout,
	.dbar,
	.invite-box {
		position: absolute;
		left: 10px;
		right: 10px;
		bottom: 10px;
		background: #121826;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 4px 4px 0 #000;
		padding: 10px 11px;
		z-index: 4;
	}

	.dbar {
		max-height: 58%;
		overflow-y: auto;
	}

	.map-hint {
		padding: 7px 10px; /* the map hint is a touch taller than the talk hint */
	}

	@keyframes hintPulse {
		0%,
		100% {
			opacity: 0.78;
		}
		50% {
			opacity: 1;
		}
	}

	.talkbar {
		position: absolute;
		left: 10px;
		right: 10px;
		bottom: 10px;
		z-index: 4;
		max-height: 34%;
		overflow: hidden;
		background: #121826;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 4px 4px 0 #000;
		padding: 8px 11px 10px;
		cursor: pointer;
	}

	.talkbar-line {
		font-size: 11px;
		line-height: 1.5;
		color: #eef0f4;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.talkbar-next {
		position: absolute;
		right: 10px;
		bottom: 5px;
		font-size: 11px;
		color: var(--gold, #e8bf48);
		animation: nextBlink 1s steps(1, end) infinite;
	}

	@keyframes nextBlink {
		0%,
		60% {
			opacity: 1;
		}
		61%,
		100% {
			opacity: 0.25;
		}
	}

	.tb-leave {
		pointer-events: auto;
		padding: 2px 8px;
		background: var(--gold, #e8bf48);
		border: none;
		color: #1a1205;
		font: inherit;
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 0.04em;
		cursor: pointer;
		flex-shrink: 0;
	}

	@media (prefers-reduced-motion: reduce) {
		.hint-strip,
		.map-hint,
		.talkbar-next,
		.here-ring {
			animation: none;
		}
	}

	.callout-name {
		font-size: 13px;
		font-weight: 700;
		color: #efe6cf;
	}

	.callout-meta {
		font-size: 10px;
		color: #9aa0ad;
		margin-top: 2px;
	}

	.callout-actions,
	.dbar-actions {
		display: flex;
		gap: 7px;
		margin-top: 10px;
	}

	.callout-actions :global(.pixel-button),
	.dbar-actions :global(.pixel-button) {
		flex: 1;
	}

	/* Ghost PixelButtons are built for the LIGHT theme (transparent + dark text) and
	   vanished into these dark overlays — give them a dark-overlay skin so they read. */
	.callout :global(.pixel-button.ghost),
	.dbar :global(.pixel-button.ghost),
	.invite-box :global(.pixel-button.ghost),
	.picker :global(.pixel-button.ghost) {
		background: #1b2436;
		border-color: #e8bf48;
		color: #efe6cf;
	}

	.dbar-line {
		font-size: 10.5px;
		line-height: 1.5;
		color: #eef0f4;
		min-height: 20px;
	}

	.quest-info {
		margin-top: 8px;
		padding: 7px 8px;
		background: #0a0d16;
		border: 1px solid #2a3240;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.quest-info-row {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.quest-title {
		font-size: 11px;
		font-weight: 700;
		color: #efe6cf;
		flex: 1;
		min-width: 0;
	}

	.quest-days {
		font-size: 9px;
		color: var(--gold, #e8bf48);
	}

	.quest-reward {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		align-items: baseline;
		font-size: 9.5px;
		color: #c7a24a;
	}

	.reward-label {
		color: #9aa0ad;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.reward-title {
		color: #efe6cf;
	}

	.reward-xp,
	.reward-coins {
		color: var(--gold, #e8bf48);
	}

	.dbar-coop {
		display: flex;
		gap: 7px;
		margin-top: 8px;
	}

	.dbar-coop :global(.pixel-button) {
		flex: 1;
	}

	.invite-line {
		font-size: 10.5px;
		line-height: 1.5;
		color: #eef0f4;
	}

	.invite-quest {
		font-size: 12px;
		font-weight: 700;
		color: #efe6cf;
		margin-top: 3px;
	}

	.picker-backdrop {
		position: absolute;
		inset: 0;
		background: rgba(5, 6, 10, 0.78);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 16px;
		z-index: 5;
	}

	.picker {
		width: 100%;
		max-width: 92%;
		max-height: 80%;
		display: flex;
		flex-direction: column;
		background: #121826;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 4px 4px 0 #000;
		padding: 10px 11px;
	}

	.picker-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		margin-bottom: 8px;
	}

	.picker-title {
		font-family: var(--font-display, monospace);
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: #efe6cf;
	}

	.picker-empty {
		font-size: 10.5px;
		line-height: 1.5;
		color: #9aa0ad;
		padding: 6px 2px;
	}

	.picker-list {
		display: flex;
		flex-direction: column;
		gap: 5px;
		overflow-y: auto;
	}

	.picker-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		padding: 8px 9px;
		background: #0a0d16;
		border: 1px solid #2a3240;
		color: #efe6cf;
		font: inherit;
		cursor: pointer;
		text-align: left;
	}

	.picker-item:disabled {
		opacity: 0.5;
		cursor: default;
	}

	.picker-item-name {
		font-size: 11px;
		font-weight: 700;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.picker-item-lvl {
		font-size: 9px;
		color: var(--gold, #e8bf48);
		flex-shrink: 0;
		font-family: var(--font-data, monospace);
	}

	.qhud {
		position: absolute;
		top: 36px;
		left: 9px;
		right: 9px;
		background: #121826;
		border: 2px solid var(--gold, #e8bf48);
		border-left: 4px solid var(--gold, #e8bf48);
		box-shadow: 3px 3px 0 #000;
		padding: 7px 10px;
		z-index: 2;
	}

	.qhud-title {
		font-size: 11px;
		font-weight: 700;
		color: #efe6cf;
	}

	.qhud-day {
		font-size: 9px;
		color: #c7a24a;
		margin-top: 2px;
	}

	.qhud-rows {
		display: flex;
		flex-direction: column;
		gap: 5px;
		margin-top: 6px;
	}

	.qhud-row-top {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 6px;
	}

	.qhud-ex-name {
		font-size: 9px;
		color: #cfd3dc;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.qhud-ex-num {
		font-size: 9px;
		color: #efe6cf;
		flex-shrink: 0;
		font-family: var(--font-data, monospace);
	}

	.qhud-check {
		color: #39d353;
	}

	.qbar {
		height: 6px;
		background: #0a0d16;
		border: 1px solid #2a3240;
		margin-top: 3px;
		overflow: hidden;
	}

	.qbar-fill {
		height: 100%;
		background: var(--gold, #e8bf48);
		transition: width 0.3s ease;
	}

	.qbar-fill.done {
		background: #39d353;
	}

	.fade {
		position: absolute;
		inset: 0;
		background: #05060a;
		pointer-events: none;
		z-index: 6;
	}

	.toast {
		position: absolute;
		left: 50%;
		top: 44%;
		transform: translate(-50%, -50%);
		background: #121826;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 4px 4px 0 #000;
		color: #efe6cf;
		font-size: 11px;
		padding: 10px 14px;
		text-align: center;
		max-width: 78%;
		z-index: 7;
	}
</style>
