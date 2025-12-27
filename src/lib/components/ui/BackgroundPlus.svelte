<script lang="ts">
	/**
	 * BackgroundPlus - Futuristic plus pattern background
	 * Converted from React component for Svelte
	 */
	
	export let plusSize: number = 60;
	export let plusColor: string = '#7d6c91';  // Obsidian purple
	export let backgroundColor: string = 'transparent';
	export let fade: boolean = true;
	export let className: string = '';
	
	$: encodedPlusColor = encodeURIComponent(plusColor);
	
	$: maskStyle = fade
		? 'mask-image: radial-gradient(circle, white 10%, transparent 90%); -webkit-mask-image: radial-gradient(circle, white 10%, transparent 90%);'
		: '';
	
	$: backgroundStyle = `
		background-color: ${backgroundColor};
		background-image: url("data:image/svg+xml,%3Csvg width='${plusSize}' height='${plusSize}' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='${encodedPlusColor}' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
		${maskStyle}
	`;
</script>

<div 
	class="absolute inset-0 h-full w-full pointer-events-none {className}"
	style={backgroundStyle}
	{...$$restProps}
/>

