<script lang="ts">
	import { base } from '$app/paths';
	import { onMount, onDestroy, tick } from 'svelte';
	import { PixelButton, PixelIcon } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { telegram } from '$lib/stores/telegram.svelte';
	import { cityStore } from '$lib/city/city.svelte';
	import { t, ln } from '$lib/i18n/index.svelte';
	import type { DistrictResponse, DistrictDialogueLine, Friend } from '$lib/types';
	import type { MapNode } from '$lib/city/render/map';
	import { drawCityMap } from '$lib/city/render/map';
	import { drawYard } from '$lib/city/render/scenes/yard';
	import { drawFrench } from '$lib/city/render/scenes/french';
	import { drawCossack } from '$lib/city/render/scenes/cossack';

	// ---- canvas buffer sizes (low-res; CSS upscales with pixelated) ----
	const MAP_W = 200,
		MAP_H = 300;
	const DISTRICT_W = 200,
		DISTRICT_H = 356;

	type Mode = 'map' | 'travel' | 'district';

	// Scene key → detailed renderer. downtown/port have no scene (locked stubs).
	const SCENE_RENDERERS: Record<string, (ctx: CanvasRenderingContext2D, t: number) => void> = {
		yard: drawYard,
		french: drawFrench,
		cossack: drawCossack
	};

	let canvasEl = $state<HTMLCanvasElement | null>(null);
	let ctx: CanvasRenderingContext2D | null = null;
	let rafId = 0;
	const reduce = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;

	let mode = $state<Mode>('map');
	let loading = $state(true);
	// id of the district the player token currently sits on / is travelling to.
	let playerId = $state<string>('home');
	// id of the district whose scene is being shown (district mode).
	let currentId = $state<string | null>(null);
	// id of the district the callout is open for (map mode).
	let selectedId = $state<string | null>(null);

	let fadeAlpha = $state(0);
	let busy = $state(false);
	let toastMsg = $state<string | null>(null);
	let toastTimer: ReturnType<typeof setTimeout> | null = null;

	// ---- co-op friend invite (inviter side) ----
	let pickerOpen = $state(false);
	let friendsLoading = $state(false);
	let friends = $state<Friend[]>([]);

	// Player token live position in the 200-wide map space (tweened on travel).
	let playerPos = { x: 100, y: 252 };

	// ---- derived views ----
	const nodes = $derived<MapNode[]>(
		cityStore.districts
			.filter((d) => Array.isArray(d.map_pos) && d.map_pos.length >= 2)
			.map((d) => ({
				id: d.id,
				x: d.map_pos![0],
				y: d.map_pos![1],
				state: d.status === 'locked' ? ('lock' as const) : ('open' as const),
				vign: (d.scene ?? 'home') as MapNode['vign']
			}))
	);

	const selectedDistrict = $derived<DistrictResponse | undefined>(cityStore.get(selectedId));
	const currentDistrict = $derived<DistrictResponse | undefined>(cityStore.get(currentId));
	const currentProgress = $derived(currentDistrict?.quest_progress ?? null);
	const currentIsActive = $derived(currentDistrict?.status === 'active');
	const incomingInvite = $derived(currentDistrict?.incoming_invite ?? null);

	// ---- JRPG dialogue state machine ----
	// 'idle'  : scene visible, only the slim hint strip ("tap the boss") is shown.
	// 'intro' : one dialogue line at a time in the slim bottom bar (JRPG text box).
	// 'offer' : the quest offer / active-quest action box (the end state).
	// On entry we always start at 'idle' so the boss stays visible (see $effect below).
	type TalkPhase = 'idle' | 'intro' | 'offer';
	let talkPhase = $state<TalkPhase>('idle');
	let introIndex = $state(0);

	// The authored intro lines for the current district (may be empty/missing).
	const introLines = $derived<DistrictDialogueLine[]>(
		Array.isArray(currentDistrict?.dialogue?.intro)
			? (currentDistrict.dialogue.intro as DistrictDialogueLine[])
			: []
	);
	const currentLine = $derived<DistrictDialogueLine | null>(introLines[introIndex] ?? null);
	const hasIntro = $derived(introLines.length > 0);

	// Reset the dialogue machine to 'idle' whenever we land on a new district
	// (or leave). This keeps the scene/boss visible on entry — no auto-popup.
	$effect(() => {
		void currentId;
		talkPhase = 'idle';
		introIndex = 0;
	});

	// ---- tween engine (ported from the prototype) ----
	type Tween = { t0: number | null; dur: number; upd: (p: number) => void; done?: () => void };
	let tweens: Tween[] = [];
	const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
	const lerp = (a: number, b: number, p: number) => a + (b - a) * p;
	const ease = (p: number) => (p < 0.5 ? 2 * p * p : 1 - (-2 * p + 2) ** 2 / 2);

	function tween(dur: number, upd: (p: number) => void, done?: () => void) {
		if (reduce) {
			// No animation: jump to the end immediately.
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

	// ---- canvas sizing per mode ----
	function sizeCanvas(forMode: Mode) {
		if (!canvasEl) return;
		if (forMode === 'district') {
			canvasEl.width = DISTRICT_W;
			canvasEl.height = DISTRICT_H;
		} else {
			canvasEl.width = MAP_W;
			canvasEl.height = MAP_H;
		}
		ctx = canvasEl.getContext('2d');
		if (ctx) ctx.imageSmoothingEnabled = false;
	}

	// ---- render loop ----
	function render(now: number) {
		stepTweens(now);
		if (!ctx) return;
		try {
			if (mode === 'district' && currentId) {
				const scene = currentDistrict?.scene ?? '';
				const renderer = SCENE_RENDERERS[scene];
				if (renderer) renderer(ctx, now);
			} else {
				// map / travel both render the map; player token follows playerPos.
				drawCityMapWithPlayer(now);
			}
		} catch (e) {
			console.error('[city] render error', e);
		}
	}

	// The map module positions the token at the node with id === playerId. During
	// a travel tween we need the token to slide between nodes, so we hand the map
	// a shallow copy in which the travelling node's coords are overridden with the
	// live tweened playerPos (never mutating the reactive `nodes` array).
	function drawCityMapWithPlayer(now: number) {
		if (!ctx) return;
		let drawNodes = nodes;
		if (mode === 'travel') {
			drawNodes = nodes.map((n) =>
				n.id === playerId
					? { ...n, x: Math.round(playerPos.x), y: Math.round(playerPos.y) }
					: n
			);
		}
		drawCityMap(ctx, now, drawNodes, playerId);
	}

	function loop(now: number) {
		render(now);
		if (!reduce) rafId = requestAnimationFrame(loop);
	}

	function startLoop() {
		cancelAnimationFrame(rafId);
		if (reduce) {
			// Draw a single fixed frame.
			render(9000);
		} else {
			rafId = requestAnimationFrame(loop);
		}
	}

	// Under prefers-reduced-motion there is no rAF loop, so redraw a single fixed
	// frame whenever the mode / shown district changes (map ⇄ district).
	$effect(() => {
		// Track the deps that change what should be on-screen.
		void mode;
		void currentId;
		void selectedId;
		if (reduce && ctx) render(9000);
	});

	// ---- toast ----
	function toast(msg: string) {
		toastMsg = msg;
		if (toastTimer) clearTimeout(toastTimer);
		toastTimer = setTimeout(() => (toastMsg = null), 1800);
	}

	// ---- dialogue advance (district mode) ----
	// Advances the JRPG dialogue machine. Called when the player taps the scene
	// (the boss) or the dialogue bar while in a district with no open box.
	function advanceDialogue() {
		if (mode !== 'district' || !currentDistrict) return;
		// Invitee flow is unchanged: never start a dialogue over an incoming invite.
		if (incomingInvite) return;

		if (talkPhase === 'idle') {
			telegram.hapticSelection();
			// Active quest: a single progress line, then the action box. No intro.
			// Quest offer: play the authored intro (or skip straight to the offer).
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
			// Active quest has just the one progress line; advancing reveals the box.
			if (currentIsActive) {
				talkPhase = 'offer';
				return;
			}
			if (introIndex < introLines.length - 1) {
				introIndex += 1;
			} else {
				// Last intro line consumed → reveal the offer box.
				talkPhase = 'offer';
			}
		}
	}

	// ---- map interactions ----
	function onCanvasClick(e: MouseEvent) {
		if (mode === 'district') {
			advanceDialogue();
			return;
		}
		if (mode !== 'map' || !canvasEl) return;
		const r = canvasEl.getBoundingClientRect();
		const x = ((e.clientX - r.left) / r.width) * MAP_W;
		const y = ((e.clientY - r.top) / r.height) * MAP_H;
		let best: MapNode | null = null;
		let bd = Infinity;
		for (const n of nodes) {
			const dd = (n.x - x) ** 2 + (n.y - y) ** 2;
			if (dd < bd) {
				bd = dd;
				best = n;
			}
		}
		if (best && bd < 24 * 24) {
			telegram.hapticSelection();
			selectedId = best.id;
		}
	}

	function closeCallout() {
		selectedId = null;
	}

	// ---- travel: walk the token + fade, then enter the district scene ----
	function travelTo(d: DistrictResponse) {
		if (!Array.isArray(d.map_pos) || d.map_pos.length < 2) return;
		selectedId = null;
		telegram.hapticImpact('medium');
		const from = { ...playerPos };
		const to = { x: d.map_pos[0], y: d.map_pos[1] };
		playerId = d.id;
		mode = 'travel';
		tween(
			1150,
			(p) => {
				playerPos.x = lerp(from.x, to.x, p);
				playerPos.y = lerp(from.y, to.y, p);
				fadeAlpha = p > 0.58 ? clamp((p - 0.58) / 0.42, 0, 1) : 0;
			},
			() => {
				playerPos = { ...to };
				currentId = d.id;
				mode = 'district';
				sizeCanvas('district');
				fadeAlpha = 1;
				tween(480, (p) => (fadeAlpha = 1 - p));
			}
		);
	}

	function leaveDistrict() {
		const d = currentDistrict;
		telegram.hapticImpact('light');
		tween(
			440,
			(p) => (fadeAlpha = p),
			() => {
				mode = 'map';
				sizeCanvas('map');
				if (d && Array.isArray(d.map_pos) && d.map_pos.length >= 2) {
					playerPos = { x: d.map_pos[0], y: d.map_pos[1] };
					playerId = d.id;
				}
				currentId = null;
				selectedId = null;
				tween(440, (p) => (fadeAlpha = 1 - p));
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
			// Only accepted friends can be invited.
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
			// If the quest isn't active yet, the inviter must accept it first so an
			// instance exists to attach the pending participant to.
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

	// ---- helpers for overlays ----
	function dlg(d: DistrictResponse | undefined, key: string): string {
		const dict = d?.dialogue;
		if (!dict) return '';
		const en = dict[key];
		const ru = dict[`${key}_ru`];
		return ln(typeof en === 'string' ? en : undefined, typeof ru === 'string' ? ru : undefined);
	}

	// Speaker name tab for a dialogue line: the boss's name, or "You" for the hero.
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

	onMount(async () => {
		await cityStore.load();
		loading = false;
		// Start the player at the first active/available district, else home.
		const start =
			cityStore.districts.find((d) => d.status === 'active') ??
			cityStore.districts.find((d) => d.status === 'available') ??
			cityStore.districts.find((d) => d.id === 'home') ??
			cityStore.districts[0];
		if (start && Array.isArray(start.map_pos) && start.map_pos.length >= 2) {
			playerId = start.id;
			playerPos = { x: start.map_pos[0], y: start.map_pos[1] };
		}
		// The <canvas> lives behind {#if loading}, so it only mounts AFTER
		// loading=false. Wait for that DOM update so canvasEl is bound before we
		// grab its 2D context — otherwise ctx stays null and the render loop
		// silently draws nothing (the black screen we hit on first deploy).
		await tick();
		sizeCanvas('map');
		startLoop();
	});

	onDestroy(() => {
		cancelAnimationFrame(rafId);
		if (toastTimer) clearTimeout(toastTimer);
	});
</script>

<div class="city-page">
	<header class="page-header">
		<a href="{base}/" class="back-link" aria-label={t('city.title')}>
			<PixelIcon name="arrow-left" size="sm" />
		</a>
		<h1>{t('city.title')}</h1>
	</header>

	{#if loading}
		<div class="loading">{t('city.loading')}</div>
	{:else}
		<div class="stage" class:district={mode === 'district'}>
			<canvas
				bind:this={canvasEl}
				class="city-canvas"
				onclick={onCanvasClick}
				aria-label={t('city.title')}
			></canvas>

			<!-- top bar -->
			<div class="topbar">
				{#if mode === 'district' && currentDistrict}
					<span class="tb-title">{ln(currentDistrict.name, currentDistrict.name_ru)}</span>
					{#if !incomingInvite && talkPhase !== 'idle'}
						<!-- Always-available escape hatch during intro/offer. -->
						<button class="tb-leave" onclick={leaveDistrict}>{t('city.leave')}</button>
					{:else}
						<span class="tb-sub">{muscle(currentDistrict)}</span>
					{/if}
				{:else}
					<span class="tb-title">{t('city.title')}</span>
					<span class="tb-sub">{t('city.mapHint')}</span>
				{/if}
			</div>

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

			<!-- DISTRICT: slim "tap to talk" hint (scene + boss stay fully visible) -->
			{#if mode === 'district' && currentDistrict && !incomingInvite && talkPhase === 'idle'}
				<div class="hint-strip">{t('city.tapToTalk')}</div>
			{/if}

			<!-- DISTRICT: slim JRPG dialogue bar — ONE line at a time, short height -->
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
						<div class="talkbar-who">{speakerName(currentDistrict, currentLine)}</div>
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
							<PixelButton
								variant="danger"
								size="sm"
								loading={busy}
								onclick={abandonQuest}
							>
								{t('city.abandon')}
							</PixelButton>
							<PixelButton variant="ghost" size="sm" onclick={leaveDistrict}>
								{t('city.leave')}
							</PixelButton>
						</div>
						<!-- Co-op: invite a friend to an already-active quest. -->
						<div class="dbar-coop">
							<PixelButton variant="secondary" size="sm" loading={busy} onclick={openPicker}>
								{t('city.inviteFriend')}
							</PixelButton>
						</div>
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
												{ln(currentDistrict.quest.reward.title, currentDistrict.quest.reward.title_ru)}
											</span>
										{/if}
										<span class="reward-xp">+{currentDistrict.quest.reward.xp} XP</span>
										<span class="reward-coins">+{currentDistrict.quest.reward.coins} 🪙</span>
									</div>
								{/if}
							</div>
						{/if}

						<div class="dbar-actions">
							<PixelButton
								variant="primary"
								size="sm"
								loading={busy}
								onclick={acceptQuest}
							>
								{t('city.acceptQuest')}
							</PixelButton>
							<PixelButton variant="ghost" size="sm" onclick={leaveDistrict}>
								{t('city.leave')}
							</PixelButton>
						</div>

						<!-- Co-op: invite a friend (social/flavor; no reward difference). -->
						<div class="dbar-coop">
							<PixelButton variant="secondary" size="sm" loading={busy} onclick={openPicker}>
								{t('city.inviteFriend')}
							</PixelButton>
							<PixelButton variant="secondary" size="sm" loading={busy} onclick={hireMercenary}>
								{t('city.hireMercenary')}
							</PixelButton>
						</div>
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
									<button
										class="picker-item"
										disabled={busy}
										onclick={() => inviteFriend(f)}
									>
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
	}

	.loading {
		text-align: center;
		color: var(--text-muted);
		padding: var(--spacing-lg);
	}

	/* The stage is the dark, immersive pixel frame holding the canvas art. */
	.stage {
		position: relative;
		width: min(380px, 94vw);
		aspect-ratio: 200 / 300;
		max-height: 80vh;
		overflow: hidden;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 0 0 0 3px #000, 0 12px 36px rgba(0, 0, 0, 0.6);
		background: #07080c;
	}

	.stage.district {
		aspect-ratio: 200 / 356;
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

	/* --- overlays (pixel boxes in the app style, dark to match the art) --- */
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
	}

	.callout,
	.dbar {
		position: absolute;
		left: 10px;
		right: 10px;
		bottom: 10px;
		background: #121826;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 4px 4px 0 #000;
		padding: 10px 11px;
		z-index: 2;
	}

	/* The offer box is the end state (player has already seen the scene), but keep
	   it from swallowing the whole stage: cap its height and scroll if needed. */
	.dbar {
		max-height: 58%;
		overflow-y: auto;
	}

	/* Slim "tap the boss to talk" hint — tiny strip, never covers the boss. */
	.hint-strip {
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

	@keyframes hintPulse {
		0%,
		100% {
			opacity: 0.78;
		}
		50% {
			opacity: 1;
		}
	}

	/* Slim JRPG dialogue bar: one line + name tab + advance hint. Compact height
	   (≤ ~34% of the stage) so the boss in the lower scene stays visible. */
	.talkbar {
		position: absolute;
		left: 10px;
		right: 10px;
		bottom: 10px;
		z-index: 2;
		max-height: 34%;
		overflow: hidden;
		background: #121826;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 4px 4px 0 #000;
		padding: 8px 11px 10px;
		cursor: pointer;
	}

	.talkbar-who {
		display: inline-block;
		font-size: 9px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #1a1205;
		background: var(--gold, #e8bf48);
		padding: 1px 6px;
		margin-bottom: 6px;
	}

	.talkbar-line {
		font-size: 11px;
		line-height: 1.5;
		color: #eef0f4;
		/* Keep the bar to ~two lines of text so it never grows tall. */
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

	/* Always-available escape hatch, docked in the top bar during intro/offer so
	   it never overlaps the boss, the quest HUD, or the bottom dialogue bars.
	   The top bar is pointer-events:none, so the button re-enables its own. */
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

	/* Respect reduced-motion: no pulsing hint / blinking advance affordance. */
	@media (prefers-reduced-motion: reduce) {
		.hint-strip,
		.talkbar-next {
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

	.dbar-who {
		display: inline-block;
		font-size: 9px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #1a1205;
		background: var(--gold, #e8bf48);
		padding: 1px 6px;
		margin-bottom: 6px;
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

	/* Co-op action row (invite friend + mercenary). */
	.dbar-coop {
		display: flex;
		gap: 7px;
		margin-top: 8px;
	}

	.dbar-coop :global(.pixel-button) {
		flex: 1;
	}

	/* Incoming co-op invite box (invitee side). */
	.invite-box {
		position: absolute;
		left: 10px;
		right: 10px;
		bottom: 10px;
		background: #121826;
		border: 3px solid var(--gold, #e8bf48);
		box-shadow: 4px 4px 0 #000;
		padding: 10px 11px;
		z-index: 2;
	}

	.invite-who {
		display: inline-block;
		font-size: 9px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #1a1205;
		background: var(--gold, #e8bf48);
		padding: 1px 6px;
		margin-bottom: 6px;
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

	/* Friend picker modal (inviter side). */
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

	/* quest HUD panel (active quest) */
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
		z-index: 1;
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
		z-index: 3;
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
		z-index: 4;
	}
</style>
