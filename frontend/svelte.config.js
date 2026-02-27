import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter(),
		// Disable SvelteKit's built-in CSRF origin check.
		// This app authenticates via JWT in the Authorization header, not cookies,
		// so cross-site form submissions cannot carry valid credentials.
		// The check incorrectly blocks multipart/form-data uploads when browsers
		// omit the Origin header for same-origin fetches in production.
		csrf: {
			checkOrigin: false
		}
	}
};

export default config;
