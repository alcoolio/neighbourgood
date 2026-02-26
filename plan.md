# Plan: Full PWA with Service Worker Caching

## Overview

Transform the NeighbourGood SvelteKit frontend into a fully installable Progressive Web App with offline support via service worker caching. Uses SvelteKit's built-in `src/service-worker.ts` convention (no external libraries like Workbox or vite-plugin-pwa needed).

**Key design decisions:**
- Keep `adapter-node` — the app needs server-side API proxy (`hooks.server.ts`). SvelteKit's service worker works with any adapter.
- Use SvelteKit's `$service-worker` module (`build`, `files`, `version`) for cache management — zero new dependencies.
- No Workbox — the caching logic is simple enough to implement directly, keeping the dependency footprint small.
- SVG icons for the manifest (supported in Chrome 107+, Edge, Firefox) plus a PNG apple-touch-icon for Safari.

## Caching Strategy

| Resource Type | Strategy | Rationale |
|--------------|----------|-----------|
| Build assets (JS/CSS bundles) | **Precache** on install, cache-first on fetch | Immutable hashed filenames; safe to cache forever per version |
| Static files (icons, fonts, manifest) | **Precache** on install, cache-first on fetch | Rarely change; invalidated when SW version changes |
| Page navigations (HTML) | **Network-first** with offline fallback | Always show latest content; fall back to offline page when disconnected |
| API GET requests (`/api/*`) | **Network-first** with stale cache fallback | Show fresh data when possible; serve cached data when offline |
| API mutations (POST/PUT/DELETE) | **Network-only** | Mutations must reach the server; no caching |

## Steps

### Step 1: Create PWA icon assets in `frontend/static/`

Create SVG and PNG icon files based on the existing brand icon (the house+heart SVG already in `+layout.svelte`):

- `static/icon.svg` — scalable vector icon for manifest (any size)
- `static/icon-192.png` — 192×192 PNG (generated via a tiny Node script using SVG → canvas → PNG, or hand-crafted)
- `static/icon-512.png` — 512×512 PNG
- `static/favicon.png` — 32×32 PNG (already referenced in app.html but missing)
- `static/apple-touch-icon.png` — 180×180 PNG for iOS home screen

> **Pragmatic approach**: Since we can't run image generation tools in this environment, we'll create the SVGs directly and use a simple build-time script (`scripts/generate-icons.js`) that can be run with `node` to convert SVGs to PNGs. For now the manifest will reference SVGs which work in all modern PWA-capable browsers.

### Step 2: Update `static/manifest.json`

```json
{
  "name": "NeighbourGood",
  "short_name": "NeighbourGood",
  "description": "Community resource sharing platform with crisis-mode support",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#fdf8f3",
  "theme_color": "#c95d1b",
  "orientation": "any",
  "categories": ["social", "lifestyle"],
  "icons": [
    { "src": "/icon.svg", "sizes": "any", "type": "image/svg+xml" },
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "shortcuts": [
    { "name": "Messages", "url": "/messages", "icons": [{ "src": "/icon-192.png", "sizes": "192x192" }] },
    { "name": "Resources", "url": "/resources", "icons": [{ "src": "/icon-192.png", "sizes": "192x192" }] },
    { "name": "Communities", "url": "/communities", "icons": [{ "src": "/icon-192.png", "sizes": "192x192" }] }
  ]
}
```

Fix `theme_color` to `#c95d1b` (current terracotta primary) and `background_color` to `#fdf8f3` (current cream bg).

### Step 3: Create offline fallback page — `static/offline.html`

A lightweight, self-contained HTML page with inline styles (no external dependencies) that displays:
- NeighbourGood branding
- "You're offline" message
- "Try again" button that calls `location.reload()`
- Uses the same warm terracotta/cream palette

This page gets precached by the service worker and served for failed navigation requests.

### Step 4: Create the service worker — `src/service-worker.ts`

SvelteKit automatically picks up `src/service-worker.ts` and compiles it. Available imports:

```typescript
import { build, files, version } from '$service-worker';
// build = hashed JS/CSS chunks from the build
// files = everything in /static
// version = deterministic build hash (changes each build)
```

Implementation:

```typescript
/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

const CACHE_NAME = `ng-cache-${version}`;
const ASSETS = [...build, ...files];

// ── Install: precache all static + build assets ──
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ── Activate: delete old caches ──
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── Fetch: route-based caching strategies ──
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;

  // API requests: network-first with cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Build/static assets: cache-first
  if (ASSETS.includes(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Navigation: network-first with offline fallback
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .catch(() => caches.match('/offline.html'))
    );
    return;
  }
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  return cached ?? fetch(request);
}

async function networkFirst(request) {
  const cache = await caches.open(`ng-api-${version}`);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch {
    return cache.match(request) ?? new Response('Offline', { status: 503 });
  }
}
```

Key behaviors:
- `skipWaiting()` + `clients.claim()` so updates activate immediately
- Separate API cache (`ng-api-*`) from static asset cache
- Old caches cleaned up on activate
- Navigation failures show the branded offline page

### Step 5: Update `src/app.html`

Add `apple-touch-icon` and ensure all PWA meta tags are present:

```html
<link rel="apple-touch-icon" href="%sveltekit.assets%/apple-touch-icon.png" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="NeighbourGood" />
```

### Step 6: Add SW registration + update notification in `+layout.svelte`

In the `onMount`, register the service worker and listen for updates:

```typescript
if ('serviceWorker' in navigator) {
  const reg = await navigator.serviceWorker.register('/service-worker.js');
  reg.addEventListener('updatefound', () => {
    const newWorker = reg.installing;
    newWorker?.addEventListener('statechange', () => {
      if (newWorker.state === 'activated' && navigator.serviceWorker.controller) {
        showUpdateBanner = true;  // reactive state
      }
    });
  });
}
```

Add a small update banner at the top of the page:
```svelte
{#if showUpdateBanner}
  <div class="update-banner">
    New version available.
    <button onclick={() => location.reload()}>Refresh</button>
  </div>
{/if}
```

### Step 7: Add install prompt handling in `+layout.svelte`

Capture the `beforeinstallprompt` event and show an install button in the nav for mobile users:

```typescript
let installPrompt = $state(null);

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  installPrompt = e;
});

function installApp() {
  installPrompt?.prompt();
  installPrompt = null;
}
```

Show a subtle install button in the nav (only when `installPrompt` is non-null):
```svelte
{#if installPrompt}
  <button class="nav-install-btn" onclick={installApp}>Install App</button>
{/if}
```

---

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `frontend/static/icon.svg` | **Create** | SVG app icon (house+heart brand) |
| `frontend/static/icon-192.png` | **Create** | 192×192 PNG icon placeholder |
| `frontend/static/icon-512.png` | **Create** | 512×512 PNG icon placeholder |
| `frontend/static/favicon.png` | **Create** | 32×32 favicon (currently missing) |
| `frontend/static/apple-touch-icon.png` | **Create** | 180×180 iOS icon |
| `frontend/static/manifest.json` | **Edit** | Add icons, shortcuts, fix theme_color |
| `frontend/static/offline.html` | **Create** | Branded offline fallback page |
| `frontend/src/service-worker.ts` | **Create** | Service worker with caching strategies |
| `frontend/src/app.html` | **Edit** | Add apple-touch-icon + iOS meta tags |
| `frontend/src/routes/+layout.svelte` | **Edit** | SW registration, update banner, install prompt |

## No New Dependencies

This implementation uses zero new npm packages. Everything is built on:
- SvelteKit's built-in `$service-worker` module
- Standard Web APIs (Cache API, Service Worker API, `beforeinstallprompt`)

## Testing

- Build the frontend (`npm run build`) to verify the service worker compiles
- Run `npm run check` to verify TypeScript correctness
- Manual testing: open DevTools → Application → Service Workers to verify registration
- Manual testing: go offline in DevTools → Network → Offline and verify cached pages/API responses work
- Lighthouse PWA audit should pass all core criteria after implementation
