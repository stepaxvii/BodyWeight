<script lang="ts">
	import { PixelIcon } from '$lib/components/ui';
	import { api } from '$lib/api/client';
	import { userStore } from '$lib/stores/user.svelte';
	import { telegram } from '$lib/stores/telegram.svelte';
	import type { ShopItem } from '$lib/types';

	interface Props {
		open: boolean;
		onclose: () => void;
	}

	let { open, onclose }: Props = $props();

	let titles = $state<ShopItem[]>([]);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let busyId = $state<number | null>(null);

	async function load() {
		loading = true;
		error = null;
		try {
			titles = await api.getShopItems('title');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Не удалось загрузить';
		} finally {
			loading = false;
		}
	}

	// (Re)load the catalog each time the sheet opens.
	$effect(() => {
		if (open) load();
	});

	const level = $derived(userStore.level);
	const coins = $derived(userStore.coins);

	type TitleState = 'equipped' | 'owned' | 'locked' | 'buy' | 'free';
	function statusOf(t: ShopItem): TitleState {
		if (t.equipped) return 'equipped';
		if (t.owned) return 'owned';
		if (level < t.required_level) return 'locked';
		return t.price_coins > 0 ? 'buy' : 'free';
	}

	async function choose(t: ShopItem) {
		const st = statusOf(t);
		if (busyId !== null || st === 'equipped' || st === 'locked') {
			if (st === 'locked') telegram.hapticNotification('error');
			return;
		}
		busyId = t.id;
		error = null;
		try {
			// Acquire first if not owned (free titles cost 0 coins).
			if (!t.owned) {
				if (coins < t.price_coins) {
					error = 'Недостаточно монет';
					telegram.hapticNotification('error');
					return;
				}
				await api.purchaseShopItem(t.id);
			}
			await api.equipShopItem(t.id);
			await userStore.loadUser(); // refresh equipped_title + coins
			await load(); // refresh owned/equipped flags
			telegram.hapticNotification('success');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Ошибка';
			telegram.hapticNotification('error');
		} finally {
			busyId = null;
		}
	}
</script>

{#if open}
	<div class="tp-overlay" onclick={onclose} role="presentation">
		<div class="tp-sheet" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
			<span class="tp-grip"></span>
			<div class="tp-head">
				<span class="tp-title">Титулы</span>
				<button class="tp-close" onclick={onclose} aria-label="Закрыть">
					<PixelIcon name="close" size="sm" />
				</button>
			</div>

			<p class="tp-sub">Звание под ником. Часть открывается по уровню, часть — за монеты.</p>

			{#if loading}
				<p class="tp-msg">Загрузка…</p>
			{:else if error}
				<p class="tp-msg tp-msg--err">{error}</p>
			{/if}

			<div class="tp-list">
				{#each titles as t (t.id)}
					{@const st = statusOf(t)}
					<button
						class="tp-row"
						class:is-equipped={st === 'equipped'}
						class:is-locked={st === 'locked'}
						disabled={busyId !== null || st === 'equipped' || st === 'locked'}
						onclick={() => choose(t)}
					>
						<span class="slot slot--sm tp-slot">
							<PixelIcon
								name="crown"
								size="sm"
								color={st === 'equipped' ? 'var(--on-accent)' : 'var(--gold)'}
							/>
						</span>
						<span class="tp-name">{t.name_ru}</span>
						<span class="tp-status">
							{#if busyId === t.id}
								…
							{:else if st === 'equipped'}
								<PixelIcon name="check" size="sm" color="var(--on-accent)" /> Надет
							{:else if st === 'owned'}
								Надеть
							{:else if st === 'locked'}
								<PixelIcon name="lock" size="sm" color="var(--muted)" /> Ур.{t.required_level}
							{:else if st === 'buy'}
								{t.price_coins} <PixelIcon name="coin" size="sm" color="var(--gold)" />
							{:else}
								Получить
							{/if}
						</span>
					</button>
				{/each}
			</div>
		</div>
	</div>
{/if}

<style>
	.tp-overlay {
		position: fixed;
		inset: 0;
		z-index: 1000;
		background: rgba(0, 0, 0, 0.55);
		display: flex;
		align-items: flex-end;
		animation: fadein 0.2s both;
	}
	.tp-sheet {
		width: 100%;
		max-height: 86%;
		overflow-y: auto;
		background: var(--bg);
		border-top: var(--bw) solid var(--line);
		box-shadow: 0 -4px 0 var(--ink);
		padding: 14px;
		display: flex;
		flex-direction: column;
		gap: 12px;
		animation: sheetUp 0.28s cubic-bezier(0.2, 1.2, 0.4, 1) both;
	}
	.tp-sheet::-webkit-scrollbar {
		width: 0;
	}
	.tp-grip {
		width: 44px;
		height: 5px;
		background: var(--line2);
		align-self: center;
	}
	.tp-head {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.tp-title {
		flex: 1;
		font-family: var(--font-display);
		font-size: 13px;
		color: var(--text);
	}
	.tp-close {
		width: 36px;
		height: 36px;
		display: grid;
		place-items: center;
		background: var(--bg3);
		border: 2px solid var(--line);
		cursor: pointer;
	}
	.tp-sub {
		font-size: 12px;
		color: var(--muted);
		line-height: 1.5;
		margin: 0;
	}
	.tp-msg {
		font-size: 12px;
		color: var(--muted);
		text-align: center;
		margin: 0;
	}
	.tp-msg--err {
		color: var(--danger);
	}
	.tp-list {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.tp-row {
		display: flex;
		align-items: center;
		gap: 11px;
		width: 100%;
		padding: 9px 11px;
		text-align: left;
		background: var(--bg2);
		border: var(--bw) solid var(--line);
		box-shadow: var(--shadow);
		cursor: pointer;
		transition: transform 0.08s;
	}
	.tp-row:active {
		transform: translate(2px, 2px);
		box-shadow: none;
	}
	.tp-row:disabled {
		cursor: default;
	}
	.tp-row.is-equipped {
		background: var(--accent);
		border-color: var(--line);
		color: var(--on-accent);
	}
	.tp-row.is-equipped:active {
		transform: none;
		box-shadow: var(--shadow);
	}
	.tp-row.is-locked {
		opacity: 0.6;
	}
	.tp-slot {
		flex: 0 0 auto;
	}
	.tp-name {
		flex: 1;
		font-family: var(--font-ui);
		font-weight: 600;
		font-size: 14px;
		color: inherit;
	}
	.tp-status {
		flex: 0 0 auto;
		display: inline-flex;
		align-items: center;
		gap: 5px;
		font-family: var(--font-data);
		font-size: 12px;
		color: var(--muted);
	}
	.tp-row.is-equipped .tp-status {
		color: var(--on-accent);
	}
</style>
