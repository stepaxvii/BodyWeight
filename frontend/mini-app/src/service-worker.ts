/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

declare const self: ServiceWorkerGlobalScope;

import { build, files, version } from '$service-worker';

const CACHE_NAME = `pixelfit-${version}`;
const API_CACHE = 'pixelfit-api';

// App shell: built JS/CSS + static files (sprites, fonts, etc.)
const ASSETS = [...build, ...files];

// Install: cache app shell
self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
	);
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((keys) =>
			Promise.all(
				keys
					.filter((k) => k !== CACHE_NAME && k !== API_CACHE)
					.map((k) => caches.delete(k))
			)
		)
	);
});

// Fetch strategy
self.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);

	// Skip non-GET requests
	if (event.request.method !== 'GET') return;

	// Skip external requests (telegram script, google fonts CDN, etc.)
	if (url.origin !== self.location.origin) return;

	// API requests: network-first, fallback to cache
	if (url.pathname.includes('/api/')) {
		event.respondWith(
			fetch(event.request)
				.then((response) => {
					// Cache successful GET responses
					if (response.ok) {
						const clone = response.clone();
						caches.open(API_CACHE).then((cache) => cache.put(event.request, clone));
					}
					return response;
				})
				.catch(() => {
					return caches.match(event.request).then((cached) => {
						return cached || new Response('{"error":"offline"}', {
							status: 503,
							headers: { 'Content-Type': 'application/json' }
						});
					});
				})
		);
		return;
	}

	// Static assets: cache-first
	event.respondWith(
		caches.match(event.request).then((cached) => {
			if (cached) return cached;

			return fetch(event.request).then((response) => {
				// Cache new static assets
				if (response.ok && url.pathname.startsWith('/bodyweight/')) {
					const clone = response.clone();
					caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
				}
				return response;
			});
		})
	);
});
