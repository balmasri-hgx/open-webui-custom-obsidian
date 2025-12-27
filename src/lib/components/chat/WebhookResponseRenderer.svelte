<script lang="ts">
	import { getContext } from 'svelte';
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	const i18n = getContext('i18n');

	export let data: unknown;
	export let message: string = '';
	export let fileUrl: string | null = null;
	export let fileName: string | null = null;

	// Detect data type for rendering
	type DataType = 'table' | 'key-value' | 'list' | 'raw' | 'empty';

	function detectDataType(data: unknown): DataType {
		if (!data) return 'empty';

		// Check for array of objects (table)
		if (Array.isArray(data) && data.length > 0) {
			if (typeof data[0] === 'object' && data[0] !== null) {
				return 'table';
			}
			return 'list';
		}

		// Check for single object (key-value pairs)
		if (typeof data === 'object' && data !== null && !Array.isArray(data)) {
			return 'key-value';
		}

		return 'raw';
	}

	function getTableHeaders(data: Record<string, unknown>[]): string[] {
		if (!data || data.length === 0) return [];
		const allKeys = new Set<string>();
		data.forEach((item) => {
			Object.keys(item).forEach((key) => allKeys.add(key));
		});
		return Array.from(allKeys);
	}

	function formatValue(value: unknown): string {
		if (value === null || value === undefined) return '-';
		if (typeof value === 'boolean') return value ? '✓' : '✗';
		if (typeof value === 'object') return JSON.stringify(value);
		return String(value);
	}

	function renderMarkdown(text: string): string {
		return DOMPurify.sanitize(marked.parse(text) as string);
	}

	$: dataType = detectDataType(data);
	$: tableHeaders = dataType === 'table' ? getTableHeaders(data as Record<string, unknown>[]) : [];
</script>

<div class="webhook-response space-y-4">
	<!-- Message -->
	{#if message}
		<div class="prose dark:prose-invert prose-sm max-w-none">
			{@html renderMarkdown(message)}
		</div>
	{/if}

	<!-- File Download -->
	{#if fileUrl}
		<div class="flex items-center gap-3 p-3 rounded-lg bg-obsidian-50 dark:bg-obsidian-900/30 border border-obsidian-200 dark:border-obsidian-800">
			<div class="flex-shrink-0">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="size-6 text-obsidian-600 dark:text-obsidian-400"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3"
					/>
				</svg>
			</div>
			<div class="flex-1 min-w-0">
				<a
					href={fileUrl}
					target="_blank"
					rel="noopener noreferrer"
					class="text-sm font-medium text-obsidian-600 dark:text-obsidian-400 hover:underline truncate block"
				>
					{fileName || $i18n.t('Download File')}
				</a>
			</div>
			<a
				href={fileUrl}
				download={fileName || 'download'}
				class="flex-shrink-0 px-3 py-1.5 text-xs font-medium rounded-lg bg-obsidian-600 text-white hover:bg-obsidian-700 transition-colors"
			>
				{$i18n.t('Download')}
			</a>
		</div>
	{/if}

	<!-- Data Display -->
	{#if dataType === 'table' && Array.isArray(data)}
		<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
			<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
				<thead class="bg-gray-50 dark:bg-gray-800">
					<tr>
						{#each tableHeaders as header}
							<th
								class="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
							>
								{header}
							</th>
						{/each}
					</tr>
				</thead>
				<tbody class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
					{#each data as row, idx}
						<tr class={idx % 2 === 0 ? '' : 'bg-gray-50 dark:bg-gray-800/50'}>
							{#each tableHeaders as header}
								<td class="px-4 py-2 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap">
									{formatValue(row[header])}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="text-xs text-gray-500 dark:text-gray-400">
			{data.length} {data.length === 1 ? $i18n.t('row') : $i18n.t('rows')}
		</p>
	{:else if dataType === 'key-value' && typeof data === 'object' && data !== null}
		<div class="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
			<dl class="divide-y divide-gray-200 dark:divide-gray-700">
				{#each Object.entries(data) as [key, value], idx}
					<div
						class="px-4 py-3 flex justify-between gap-4 {idx % 2 === 0
							? 'bg-white dark:bg-gray-900'
							: 'bg-gray-50 dark:bg-gray-800/50'}"
					>
						<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">{key}</dt>
						<dd class="text-sm text-gray-900 dark:text-gray-100 text-right">
							{formatValue(value)}
						</dd>
					</div>
				{/each}
			</dl>
		</div>
	{:else if dataType === 'list' && Array.isArray(data)}
		<ul class="space-y-1">
			{#each data as item}
				<li class="text-sm text-gray-900 dark:text-gray-100 flex items-start gap-2">
					<span class="text-obsidian-500">•</span>
					<span>{formatValue(item)}</span>
				</li>
			{/each}
		</ul>
	{:else if dataType === 'raw' && data}
		<pre
			class="p-3 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">{typeof data ===
		'string'
			? data
			: JSON.stringify(data, null, 2)}</pre>
	{/if}
</div>

<style>
	:global(.bg-obsidian-50) {
		background-color: rgba(91, 73, 101, 0.05);
	}
	:global(.dark .bg-obsidian-900\/30) {
		background-color: rgba(91, 73, 101, 0.15);
	}
	:global(.border-obsidian-200) {
		border-color: rgba(91, 73, 101, 0.2);
	}
	:global(.dark .border-obsidian-800) {
		border-color: rgba(91, 73, 101, 0.3);
	}
	:global(.text-obsidian-600) {
		color: #5b4965;
	}
	:global(.dark .text-obsidian-400) {
		color: #b8a9c0;
	}
	:global(.text-obsidian-500) {
		color: #7d6c91;
	}
	:global(.bg-obsidian-600) {
		background-color: #5b4965;
	}
	:global(.hover\:bg-obsidian-700:hover) {
		background-color: #3d354b;
	}
</style>

