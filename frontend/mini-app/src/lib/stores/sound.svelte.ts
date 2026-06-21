import { userStore } from './user.svelte';

/** A single 8-bit "note": frequency (Hz), duration (s), optional wave + volume. */
type Note = { f: number; d: number; type?: OscillatorType; v?: number };

/**
 * 8-bit sound effects, synthesized live via the Web Audio API — no audio files.
 * Square waves give the classic chiptune timbre. Respects the user's
 * `sound_enabled` preference. The AudioContext must be unlocked from a user
 * gesture (call `sound.unlock()` when the workout starts).
 */
class SoundService {
	private ctx: AudioContext | null = null;

	private get enabled(): boolean {
		return userStore.user?.sound_enabled ?? true;
	}

	private ctxOrNull(): AudioContext | null {
		if (typeof window === 'undefined') return null;
		try {
			if (!this.ctx) {
				const AC: typeof AudioContext | undefined =
					window.AudioContext ??
					(window as unknown as { webkitAudioContext?: typeof AudioContext })
						.webkitAudioContext;
				if (!AC) return null;
				this.ctx = new AC();
			}
			if (this.ctx.state === 'suspended') void this.ctx.resume();
			return this.ctx;
		} catch {
			return null;
		}
	}

	/** Unlock/resume audio on a user gesture (browsers block audio otherwise). */
	unlock(): void {
		this.ctxOrNull();
	}

	private play(notes: Note[]): void {
		if (!this.enabled) return;
		const ctx = this.ctxOrNull();
		if (!ctx) return;
		let t = ctx.currentTime;
		for (const n of notes) {
			const osc = ctx.createOscillator();
			const gain = ctx.createGain();
			osc.type = n.type ?? 'square'; // square wave = classic 8-bit
			osc.frequency.setValueAtTime(n.f, t);
			const vol = n.v ?? 0.07;
			gain.gain.setValueAtTime(vol, t);
			gain.gain.exponentialRampToValueAtTime(0.0001, t + n.d);
			osc.connect(gain);
			gain.connect(ctx.destination);
			osc.start(t);
			osc.stop(t + n.d);
			t += n.d;
		}
	}

	// ---- named cues ----
	click() {
		this.play([{ f: 660, d: 0.05 }]);
	}
	start() {
		this.play([{ f: 523, d: 0.08 }, { f: 784, d: 0.11 }]);
	}
	exerciseDone() {
		this.play([{ f: 784, d: 0.07 }, { f: 1047, d: 0.13 }]);
	}
	restStart() {
		this.play([{ f: 392, d: 0.09 }, { f: 311, d: 0.12 }]);
	}
	restEnd() {
		this.play([{ f: 659, d: 0.07 }, { f: 880, d: 0.07 }, { f: 1175, d: 0.14 }]);
	}
	complete() {
		this.play([
			{ f: 523, d: 0.1 },
			{ f: 659, d: 0.1 },
			{ f: 784, d: 0.1 },
			{ f: 1047, d: 0.24 }
		]);
	}
	levelUp() {
		this.play([
			{ f: 659, d: 0.09 },
			{ f: 784, d: 0.09 },
			{ f: 988, d: 0.09 },
			{ f: 1319, d: 0.22 }
		]);
	}
	error() {
		this.play([
			{ f: 196, d: 0.13, type: 'sawtooth' },
			{ f: 147, d: 0.2, type: 'sawtooth' }
		]);
	}
}

export const sound = new SoundService();
