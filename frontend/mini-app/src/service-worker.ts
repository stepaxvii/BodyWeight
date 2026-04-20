/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

declare const self: ServiceWorkerGlobalScope;

import { build, files, version } from '$service-worker';

const CACHE_NAME = `pixelfit-${version}`;
const API_CACHE = 'pixelfit-api';
const FONT_CACHE = 'pixelfit-fonts';

// App shell: built JS/CSS + static files (sprites, fonts, etc.)
const ASSETS = [...build, ...files];

// Install: cache app shell, skip waiting to activate immediately
self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME)
			.then((cache) => cache.addAll(ASSETS))
			.then(() => self.skipWaiting())
	);
});

// Activate: clean old caches, claim clients immediately
self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys()
			.then((keys) =>
				Promise.all(
					keys
						.filter((k) => k !== CACHE_NAME && k !== API_CACHE && k !== FONT_CACHE)
						.map((k) => caches.delete(k))
				)
			)
			.then(() => self.clients.claim())
	);
});

// Fetch strategy
self.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);

	// Skip non-GET requests (POST workout submissions etc.)
	if (event.request.method !== 'GET') return;

	// Google Fonts & external CDN: cache-first (fonts rarely change)
	if (
		url.hostname === 'fonts.googleapis.com' ||
		url.hostname === 'fonts.gstatic.com'
	) {
		event.respondWith(
			caches.match(event.request).then((cached) => {
				if (cached) return cached;
				return fetch(event.request).then((response) => {
					if (response.ok) {
						const clone = response.clone();
						caches.open(FONT_CACHE).then((cache) => cache.put(event.request, clone));
					}
					return response;
				}).catch(() => new Response('', { status: 503 }));
			})
		);
		return;
	}

	// Skip other external requests (telegram script etc.)
	if (url.origin !== self.location.origin) return;

	// API requests: network-first, fallback to cache
	if (url.pathname.includes('/api/')) {
		event.respondWith(
			fetch(event.request)
				.then((response) => {
					if (response.ok) {
						const clone = response.clone();
						caches.open(API_CACHE).then((cache) => cache.put(event.request, clone));
					}
					return response;
				})
				.catch(() =>
					caches.match(event.request).then((cached) =>
						cached || new Response('{"error":"offline"}', {
							status: 503,
							headers: { 'Content-Type': 'application/json' }
						})
					)
				)
		);
		return;
	}

	// Navigation requests (HTML pages): network-first, fallback to cached index.html (SPA)
	if (event.request.mode === 'navigate') {
		event.respondWith(
			fetch(event.request)
				.then((response) => {
					if (response.ok) {
						const clone = response.clone();
						caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
					}
					return response;
				})
				.catch(() =>
					caches.match(event.request)
						.then((cached) => cached || caches.match('/bodyweight/index.html'))
						.then((cached) => cached || caches.match('/bodyweight/'))
						.then((cached) => cached || new Response('Offline', { status: 503 }))
				)
		);
		return;
	}

	// Static assets: cache-first with offline fallback
	event.respondWith(
		caches.match(event.request).then((cached) => {
			if (cached) return cached;

			return fetch(event.request)
				.then((response) => {
					if (response.ok && url.pathname.startsWith('/bodyweight/')) {
						const clone = response.clone();
						caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
					}
					return response;
				})
				.catch(() => new Response('', { status: 503 }));
		})
	);
});
