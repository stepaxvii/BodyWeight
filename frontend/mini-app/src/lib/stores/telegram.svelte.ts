import { browser } from '$app/environment';

// Telegram WebApp state using Svelte 5 runes
class TelegramStore {
	webApp = $state<TelegramWebApp | null>(null);
	initData = $state<string>('');
	user = $state<TelegramUser | null>(null);
	theme = $state<'light' | 'dark'>('dark');
	themeParams = $state<TelegramThemeParams>({});
	isReady = $state(false);
	startParam = $state<string | null>(null);

	constructor() {
		if (browser) {
			this.init();
		}
	}

	private init() {
		if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
			const webApp = window.Telegram.WebApp;

			this.webApp = webApp;
			this.initData = webApp.initData;
			this.user = webApp.initDataUnsafe?.user ?? null;
			this.theme = webApp.colorScheme;
			this.themeParams = webApp.themeParams;
			this.startParam = webApp.initDataUnsafe?.start_param ?? null;

			// Configure WebApp
			webApp.ready();
			webApp.expand();
			webApp.setHeaderColor('#1a1a2e');
			webApp.setBackgroundColor('#1a1a2e');

			// Listen for theme changes
			webApp.onEvent('themeChanged', () => {
				this.theme = webApp.colorScheme;
				this.themeParams = webApp.themeParams;
			});

			this.isReady = true;
		} else {
			// Development mode - use mock data
			this.user = {
				id: 123456789,
				first_name: 'Dev',
				last_name: 'User',
				username: 'devuser',
				language_code: 'ru'
			};
			this.theme = 'dark';
			this.isReady = true;
		}
	}

	// Haptic feedback helpers
	hapticImpact(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft' = 'medium') {
		this.webApp?.HapticFeedback?.impactOccurred(style);
	}

	hapticNotification(type: 'error' | 'success' | 'warning') {
		this.webApp?.HapticFeedback?.notificationOccurred(type);
	}

	hapticSelection() {
		this.webApp?.HapticFeedback?.selectionChanged();
	}

	// Main button helpers
	showMainButton(text: string, onClick: () => void) {
		if (this.webApp?.MainButton) {
			this.webApp.MainButton.setText(text);
			this.webApp.MainButton.onClick(onClick);
			this.webApp.MainButton.show();
		}
	}

	hideMainButton() {
		this.webApp?.MainButton?.hide();
	}

	setMainButtonLoading(loading: boolean) {
		if (this.webApp?.MainButton) {
			if (loading) {
				this.webApp.MainButton.showProgress();
			} else {
				this.webApp.MainButton.hideProgress();
			}
		}
	}

	// Back button helpers
	showBackButton(onClick: () => void) {
		if (this.webApp?.BackButton) {
			this.webApp.BackButton.onClick(onClick);
			this.webApp.BackButton.show();
		}
	}

	hideBackButton() {
		this.webApp?.BackButton?.hide();
	}

	// Close app
	close() {
		this.webApp?.close();
	}
}

export const telegram = new TelegramStore();
