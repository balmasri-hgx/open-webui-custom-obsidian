<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { getContext, onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { flyAndScale } from '$lib/utils/transitions';

	import { getWebhookEnabledModels, getWebhookConfig, type WebhookModel, type WebhookFormField } from '$lib/apis/webhooks';

	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import Bolt from '$lib/components/icons/Bolt.svelte';

	const i18n = getContext('i18n');

	export let onWorkflowSelect: (webhook: { modelId: string; formTitle: string; formDescription: string; formFields: WebhookFormField[] }) => void = () => {};
	export let onClose: () => void = () => {};

	let show = false;
	let loading = false;
	let workflows: WebhookModel[] = [];

	$: if (show) {
		loadWorkflows();
	}

	const loadWorkflows = async () => {
		if (workflows.length > 0) return; // Already loaded
		
		loading = true;
		try {
			workflows = await getWebhookEnabledModels(localStorage.token);
		} catch (e) {
			console.error('Failed to load workflows:', e);
			workflows = [];
		}
		loading = false;
	};

	const selectWorkflow = async (workflow: WebhookModel) => {
		try {
			const config = await getWebhookConfig(localStorage.token, workflow.id);
			
			if (!config.enabled) {
				return;
			}
			
			onWorkflowSelect({
				modelId: workflow.id,
				formTitle: config.form_title || workflow.name || 'Workflow Form',
				formDescription: config.form_description || '',
				formFields: config.form_fields || []
			});
			
			show = false;
		} catch (error) {
			console.error('Failed to load workflow config:', error);
		}
	};
</script>

<Dropdown
	bind:show
	on:change={(e) => {
		if (e.detail === false) {
			onClose();
		}
	}}
>
	<Tooltip content={$i18n.t('Workflows')} placement="top">
		<slot />
	</Tooltip>
	<div slot="content">
		<DropdownMenu.Content
			class="w-full max-w-64 rounded-2xl px-1 py-1 border border-gray-100 dark:border-gray-800 z-50 bg-white dark:bg-gray-850 dark:text-white shadow-lg max-h-72 overflow-y-auto overflow-x-hidden scrollbar-thin"
			sideOffset={4}
			alignOffset={-6}
			side="top"
			align="start"
			transition={flyAndScale}
		>
			<div class="px-2 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
				{$i18n.t('Workflows')}
			</div>

			{#if loading}
				<div class="py-6 flex justify-center">
					<Spinner className="size-4" />
				</div>
			{:else if workflows.length === 0}
				<div class="px-3 py-4 text-sm text-gray-500 dark:text-gray-400 text-center">
					<p>{$i18n.t('No workflows available')}</p>
					<p class="text-xs mt-1 opacity-70">{$i18n.t('Configure workflows in model settings')}</p>
				</div>
			{:else}
				<div in:fly={{ y: -10, duration: 150 }}>
					{#each workflows as workflow (workflow.id)}
						<button
							class="flex w-full gap-2 items-center px-3 py-2 text-sm cursor-pointer rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
							on:click={() => selectWorkflow(workflow)}
						>
							<div class="flex-shrink-0 size-8 rounded-lg bg-obsidian-100 dark:bg-obsidian-900/50 flex items-center justify-center">
								<Bolt className="size-4 text-obsidian-600 dark:text-obsidian-300" />
							</div>
							<div class="flex-1 text-left min-w-0">
								<div class="font-medium text-gray-900 dark:text-white truncate">
									{workflow.form_title || workflow.name}
								</div>
								{#if workflow.slash_command}
									<div class="text-xs text-gray-500 dark:text-gray-400 truncate">
										{workflow.slash_command}
									</div>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</DropdownMenu.Content>
	</div>
</Dropdown>

<style>
	:global(.bg-obsidian-100) {
		background-color: rgba(91, 73, 101, 0.1);
	}
	:global(.dark .bg-obsidian-900\/50) {
		background-color: rgba(91, 73, 101, 0.25);
	}
	:global(.text-obsidian-600) {
		color: #5b4965;
	}
	:global(.dark .text-obsidian-300) {
		color: #b8a9c0;
	}
</style>

