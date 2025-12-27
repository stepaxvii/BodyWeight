/// <reference types="@sveltejs/kit" />

declare global {
	interface Window {
		Telegram: {
			WebApp: TelegramWebApp;
		};
	}

	interface TelegramWebApp {
		initData: string;
		initDataUnsafe: {
			user?: {
				id: number;
				first_name: string;
				last_name?: string;
				username?: string;
				language_code?: string;
			};
		};
		ready: () => void;
		expand: () => void;
		close: () => void;
		MainButton: {
			text: string;
			color: string;
			textColor: string;
			isVisible: boolean;
			isActive: boolean;
			show: () => void;
			hide: () => void;
			onClick: (callback: () => void) => void;
			offClick: (callback: () => void) => void;
			enable: () => void;
			disable: () => void;
			showProgress: (leaveActive?: boolean) => void;
			hideProgress: () => void;
		};
		BackButton: {
			isVisible: boolean;
			show: () => void;
			hide: () => void;
			onClick: (callback: () => void) => void;
			offClick: (callback: () => void) => void;
		};
		HapticFeedback: {
			impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
			notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
			selectionChanged: () => void;
		};
		themeParams: {
			bg_color?: string;
			text_color?: string;
			hint_color?: string;
			link_color?: string;
			button_color?: string;
			button_text_color?: string;
			secondary_bg_color?: string;
		};
		colorScheme: 'light' | 'dark';
		setHeaderColor: (color: string) => void;
		setBackgroundColor: (color: string) => void;
	}

	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
