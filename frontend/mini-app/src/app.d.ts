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
			query_id?: string;
			user?: TelegramUser;
			auth_date: number;
			hash: string;
		};
		version: string;
		platform: string;
		colorScheme: 'light' | 'dark';
		themeParams: TelegramThemeParams;
		isExpanded: boolean;
		viewportHeight: number;
		viewportStableHeight: number;
		headerColor: string;
		backgroundColor: string;
		isClosingConfirmationEnabled: boolean;
		BackButton: TelegramBackButton;
		MainButton: TelegramMainButton;
		HapticFeedback: TelegramHapticFeedback;
		ready(): void;
		expand(): void;
		close(): void;
		sendData(data: string): void;
		enableClosingConfirmation(): void;
		disableClosingConfirmation(): void;
		onEvent(eventType: string, callback: () => void): void;
		offEvent(eventType: string, callback: () => void): void;
		setHeaderColor(color: string): void;
		setBackgroundColor(color: string): void;
	}

	interface TelegramUser {
		id: number;
		is_bot?: boolean;
		first_name: string;
		last_name?: string;
		username?: string;
		language_code?: string;
		is_premium?: boolean;
		photo_url?: string;
	}

	interface TelegramThemeParams {
		bg_color?: string;
		text_color?: string;
		hint_color?: string;
		link_color?: string;
		button_color?: string;
		button_text_color?: string;
		secondary_bg_color?: string;
	}

	interface TelegramBackButton {
		isVisible: boolean;
		show(): void;
		hide(): void;
		onClick(callback: () => void): void;
		offClick(callback: () => void): void;
	}

	interface TelegramMainButton {
		text: string;
		color: string;
		textColor: string;
		isVisible: boolean;
		isActive: boolean;
		isProgressVisible: boolean;
		setText(text: string): void;
		show(): void;
		hide(): void;
		enable(): void;
		disable(): void;
		showProgress(leaveActive?: boolean): void;
		hideProgress(): void;
		onClick(callback: () => void): void;
		offClick(callback: () => void): void;
	}

	interface TelegramHapticFeedback {
		impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): void;
		notificationOccurred(type: 'error' | 'success' | 'warning'): void;
		selectionChanged(): void;
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
