/**
 * Shared strings used across many screens. Namespace: `common`.
 * Reference as t('common.save'), t('common.cancel'), ...
 *
 * TEMPLATE for the string-extraction phase: every namespace file is a default
 * export with matching `ru` and `en` key trees. English is the fallback, so no
 * key may exist in `ru` without an `en` counterpart.
 */
export default {
	ru: {
		save: 'Сохранить',
		cancel: 'Отмена',
		close: 'Закрыть',
		back: 'Назад',
		loading: 'Загрузка…',
		error: 'Ошибка',
		retry: 'Повторить',
	},
	en: {
		save: 'Save',
		cancel: 'Cancel',
		close: 'Close',
		back: 'Back',
		loading: 'Loading…',
		error: 'Error',
		retry: 'Retry',
	},
};
