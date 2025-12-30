<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';

	export let className = 'size-8';
	export let src = `${WEBUI_BASE_URL}/static/HLX-white.png`;
</script>

<img
	aria-hidden="true"
	src={src === ''
		? `${WEBUI_BASE_URL}/static/HLX-white.png`
		: src.startsWith(WEBUI_BASE_URL) ||
			  src.startsWith('https://www.gravatar.com/avatar/') ||
			  src.startsWith('data:') ||
			  src.startsWith('/')
			? src
			: `${WEBUI_BASE_URL}/user.png`}
	class=" {className} object-contain"
	alt="profile"
	draggable="false"
/>
