// Curated IANA timezone list for the Settings picker. Not the full ~350-zone
// IANA database — a human-friendly shortlist (Russia/CIS-heavy, plus the major
// world zones) grouped by region. `value` is the IANA name stored on the user;
// `label`/`label_en` are the display name with a rough UTC offset hint (RU/EN).
// DST shifts are handled server-side via zoneinfo, so the offset hint is just
// orientation. Render with `ln(label_en, label)` / `ln(region_en, region)`.

export interface TzOption {
	value: string;
	label: string;
	label_en: string;
}
export interface TzGroup {
	region: string;
	region_en: string;
	zones: TzOption[];
}

export const TIMEZONE_GROUPS: TzGroup[] = [
	{
		region: 'Россия и СНГ',
		region_en: 'Russia & CIS',
		zones: [
			{ value: 'Europe/Kaliningrad', label: 'Калининград (UTC+2)', label_en: 'Kaliningrad (UTC+2)' },
			{ value: 'Europe/Moscow', label: 'Москва (UTC+3)', label_en: 'Moscow (UTC+3)' },
			{ value: 'Europe/Samara', label: 'Самара (UTC+4)', label_en: 'Samara (UTC+4)' },
			{ value: 'Asia/Yekaterinburg', label: 'Екатеринбург (UTC+5)', label_en: 'Yekaterinburg (UTC+5)' },
			{ value: 'Asia/Omsk', label: 'Омск (UTC+6)', label_en: 'Omsk (UTC+6)' },
			{ value: 'Asia/Krasnoyarsk', label: 'Красноярск (UTC+7)', label_en: 'Krasnoyarsk (UTC+7)' },
			{ value: 'Asia/Irkutsk', label: 'Иркутск (UTC+8)', label_en: 'Irkutsk (UTC+8)' },
			{ value: 'Asia/Yakutsk', label: 'Якутск (UTC+9)', label_en: 'Yakutsk (UTC+9)' },
			{ value: 'Asia/Vladivostok', label: 'Владивосток (UTC+10)', label_en: 'Vladivostok (UTC+10)' },
			{ value: 'Asia/Magadan', label: 'Магадан (UTC+11)', label_en: 'Magadan (UTC+11)' },
			{ value: 'Asia/Kamchatka', label: 'Камчатка (UTC+12)', label_en: 'Kamchatka (UTC+12)' },
			{ value: 'Europe/Kyiv', label: 'Киев (UTC+2)', label_en: 'Kyiv (UTC+2)' },
			{ value: 'Europe/Minsk', label: 'Минск (UTC+3)', label_en: 'Minsk (UTC+3)' },
			{ value: 'Asia/Tbilisi', label: 'Тбилиси (UTC+4)', label_en: 'Tbilisi (UTC+4)' },
			{ value: 'Asia/Yerevan', label: 'Ереван (UTC+4)', label_en: 'Yerevan (UTC+4)' },
			{ value: 'Asia/Baku', label: 'Баку (UTC+4)', label_en: 'Baku (UTC+4)' },
			{ value: 'Asia/Almaty', label: 'Алматы (UTC+5)', label_en: 'Almaty (UTC+5)' },
			{ value: 'Asia/Tashkent', label: 'Ташкент (UTC+5)', label_en: 'Tashkent (UTC+5)' }
		]
	},
	{
		region: 'Европа',
		region_en: 'Europe',
		zones: [
			{ value: 'Europe/London', label: 'Лондон (UTC+0)', label_en: 'London (UTC+0)' },
			{ value: 'Europe/Berlin', label: 'Берлин / Париж (UTC+1)', label_en: 'Berlin / Paris (UTC+1)' },
			{ value: 'Europe/Istanbul', label: 'Стамбул (UTC+3)', label_en: 'Istanbul (UTC+3)' }
		]
	},
	{
		region: 'Азия',
		region_en: 'Asia',
		zones: [
			{ value: 'Asia/Dubai', label: 'Дубай (UTC+4)', label_en: 'Dubai (UTC+4)' },
			{ value: 'Asia/Tehran', label: 'Тегеран (UTC+3:30)', label_en: 'Tehran (UTC+3:30)' },
			{ value: 'Asia/Karachi', label: 'Карачи (UTC+5)', label_en: 'Karachi (UTC+5)' },
			{ value: 'Asia/Kolkata', label: 'Дели (UTC+5:30)', label_en: 'Delhi (UTC+5:30)' },
			{ value: 'Asia/Bangkok', label: 'Бангкок (UTC+7)', label_en: 'Bangkok (UTC+7)' },
			{ value: 'Asia/Shanghai', label: 'Шанхай (UTC+8)', label_en: 'Shanghai (UTC+8)' },
			{ value: 'Asia/Tokyo', label: 'Токио (UTC+9)', label_en: 'Tokyo (UTC+9)' },
			{ value: 'Asia/Seoul', label: 'Сеул (UTC+9)', label_en: 'Seoul (UTC+9)' }
		]
	},
	{
		region: 'Америка',
		region_en: 'Americas',
		zones: [
			{ value: 'America/Sao_Paulo', label: 'Сан-Паулу (UTC-3)', label_en: 'São Paulo (UTC-3)' },
			{ value: 'America/New_York', label: 'Нью-Йорк (UTC-5)', label_en: 'New York (UTC-5)' },
			{ value: 'America/Chicago', label: 'Чикаго (UTC-6)', label_en: 'Chicago (UTC-6)' },
			{ value: 'America/Denver', label: 'Денвер (UTC-7)', label_en: 'Denver (UTC-7)' },
			{ value: 'America/Los_Angeles', label: 'Лос-Анджелес (UTC-8)', label_en: 'Los Angeles (UTC-8)' }
		]
	},
	{
		region: 'Австралия и Океания',
		region_en: 'Australia & Oceania',
		zones: [
			{ value: 'Australia/Perth', label: 'Перт (UTC+8)', label_en: 'Perth (UTC+8)' },
			{ value: 'Australia/Sydney', label: 'Сидней (UTC+10)', label_en: 'Sydney (UTC+10)' },
			{ value: 'Pacific/Auckland', label: 'Окленд (UTC+12)', label_en: 'Auckland (UTC+12)' }
		]
	},
	{
		region: 'Африка',
		region_en: 'Africa',
		zones: [
			{ value: 'Africa/Cairo', label: 'Каир (UTC+2)', label_en: 'Cairo (UTC+2)' },
			{ value: 'Africa/Johannesburg', label: 'Йоханнесбург (UTC+2)', label_en: 'Johannesburg (UTC+2)' }
		]
	},
	{
		region: 'Другое',
		region_en: 'Other',
		zones: [{ value: 'UTC', label: 'UTC (по Гринвичу)', label_en: 'UTC (GMT)' }]
	}
];

/** All known values, for validating/falling back the current selection. */
export const TIMEZONE_VALUES = new Set(TIMEZONE_GROUPS.flatMap((g) => g.zones.map((z) => z.value)));

/** The device's IANA timezone, or null if unavailable. */
export function detectTimezone(): string | null {
	try {
		return Intl.DateTimeFormat().resolvedOptions().timeZone || null;
	} catch {
		return null;
	}
}
