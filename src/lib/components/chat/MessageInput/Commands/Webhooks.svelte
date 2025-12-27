<script lang="ts">
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { getContext } from 'svelte';
	import type { WebhookModel } from '$lib/apis/webhooks';

	const i18n = getContext('i18n');

	export let query = '';
	export let webhooks: WebhookModel[] = [];
	export let onSelect: (e: { type: string; data: WebhookModel }) => void = () => {};

	let selectedIdx = 0;
	export let filteredItems: WebhookModel[] = [];

	$: filteredItems = webhooks
		.filter((w) => {
			const command = w.slash_command?.toLowerCase() || '';
			const name = w.name?.toLowerCase() || '';
			const q = query.toLowerCase();
			return command.includes(q) || name.includes(q);
		})
		.sort((a, b) => (a.name || '').localeCompare(b.name || ''));

	$: if (query) {
		selectedIdx = 0;
	}

	export const selectUp = () => {
		selectedIdx = Math.max(0, selectedIdx - 1);
	};

	export const selectDown = () => {
		selectedIdx = Math.min(selectedIdx + 1, filteredItems.length - 1);
	};

	export const select = async () => {
		const item = filteredItems[selectedIdx];
		if (item) {
			onSelect({ type: 'webhook', data: item });
		}
	};
</script>

<div class="px-2 text-xs text-gray-500 py-1">
	{$i18n.t('Workflows')}
</div>

{#if filteredItems.length > 0}
	<div class="space-y-0.5 scrollbar-hidden">
		{#each filteredItems as webhookItem, idx}
			<Tooltip content={webhookItem.form_title || webhookItem.name} placement="top-start">
				<button
					class="px-3 py-1 rounded-xl w-full text-left {idx === selectedIdx
						? 'bg-gray-50 dark:bg-gray-800 selected-command-option-button'
						: ''} truncate"
					type="button"
					on:click={() => {
						onSelect({ type: 'webhook', data: webhookItem });
					}}
					on:mousemove={() => {
						selectedIdx = idx;
					}}
					on:focus={() => {}}
					data-selected={idx === selectedIdx}
				>
					<span class="font-medium text-black dark:text-gray-100">
						{webhookItem.slash_command || `/${webhookItem.id}`}
					</span>

					<span class="text-xs text-gray-600 dark:text-gray-100 ml-2">
						{webhookItem.form_title || webhookItem.name}
					</span>

					<span
						class="ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-obsidian-100 text-obsidian-800 dark:bg-obsidian-900 dark:text-obsidian-200"
					>
						workflow
					</span>
				</button>
			</Tooltip>
		{/each}
	</div>
{:else}
	<div class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
		{$i18n.t('No workflows found')}
	</div>
{/if}

<style>
	:global(.bg-obsidian-100) {
		background-color: rgba(91, 73, 101, 0.1);
	}
	:global(.text-obsidian-800) {
		color: #3d354b;
	}
	:global(.dark .bg-obsidian-900) {
		background-color: rgba(91, 73, 101, 0.3);
	}
	:global(.dark .text-obsidian-200) {
		color: #b8a9c0;
	}
</style>

