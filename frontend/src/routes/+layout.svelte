<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<svelte:head>
	<title>NeighbourGood</title>
	<meta name="description" content="Community resource sharing platform" />
</svelte:head>

{@render children()}
