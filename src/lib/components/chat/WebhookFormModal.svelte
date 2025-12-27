<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Modal from '../common/Modal.svelte';
	import Spinner from '../common/Spinner.svelte';
	import DocumentArrowUp from '../icons/DocumentArrowUp.svelte';
	import XMark from '../icons/XMark.svelte';
	import { invokeWebhook, invokeWebhookWithFiles, type WebhookFormField } from '$lib/apis/webhooks';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let show = false;
	export let modelId: string;
	export let formTitle = 'Workflow Form';
	export let formDescription = '';
	export let formFields: WebhookFormField[] = [];
	export let chatId: string | null = null;

	let formData: Record<string, string> = {};
	let fileData: Record<string, File[]> = {};
	let loading = false;
	let errors: Record<string, string> = {};

	// Check if form has file fields
	$: hasFileFields = formFields.some((f) => f.type === 'file');

	// Initialize form data with defaults
	$: if (show && formFields) {
		formData = {};
		fileData = {};
		errors = {};
		for (const field of formFields) {
			if (field.type === 'file') {
				fileData[field.name] = [];
			} else {
				formData[field.name] = field.default || '';
			}
		}
	}

	const validateForm = (): boolean => {
		errors = {};
		let isValid = true;

		for (const field of formFields) {
			if (field.required) {
				if (field.type === 'file') {
					if (!fileData[field.name] || fileData[field.name].length === 0) {
						errors[field.name] = `${field.label} is required`;
						isValid = false;
					}
				} else if (!formData[field.name]?.trim()) {
					errors[field.name] = `${field.label} is required`;
					isValid = false;
				}
			}
		}

		return isValid;
	};

	const handleFileChange = (fieldName: string, event: Event, multiple: boolean) => {
		const input = event.target as HTMLInputElement;
		if (input.files) {
			const newFiles = Array.from(input.files);
			if (multiple) {
				fileData[fieldName] = [...(fileData[fieldName] || []), ...newFiles];
			} else {
				fileData[fieldName] = newFiles;
			}
			fileData = fileData; // Trigger reactivity
		}
	};

	const removeFile = (fieldName: string, index: number) => {
		fileData[fieldName] = fileData[fieldName].filter((_, i) => i !== index);
		fileData = fileData;
	};

	const formatFileSize = (bytes: number): string => {
		if (bytes < 1024) return bytes + ' B';
		if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
		return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
	};

	const handleSubmit = async () => {
		if (!validateForm()) {
			return;
		}

		loading = true;

		try {
			let response;

			if (hasFileFields) {
				// Collect all files from all file fields
				const allFiles: File[] = [];
				for (const fieldName in fileData) {
					allFiles.push(...fileData[fieldName]);
				}

				response = await invokeWebhookWithFiles(
					localStorage.token,
					modelId,
					formData,
					allFiles,
					chatId || undefined
				);
			} else {
				response = await invokeWebhook(
					localStorage.token,
					modelId,
					formData,
					chatId || undefined
				);
			}

			if (response.success) {
				dispatch('success', response);
				show = false;
				toast.success(response.message || 'Workflow executed successfully');
			} else {
				toast.error(response.message || 'Workflow failed');
			}
		} catch (error) {
			console.error('Webhook error:', error);
			toast.error(typeof error === 'string' ? error : 'Failed to execute workflow');
		} finally {
			loading = false;
		}
	};

	const handleClose = () => {
		show = false;
		dispatch('close');
	};
</script>

<Modal bind:show size="sm">
	<div class="px-6 py-5">
		<!-- Header -->
		<div class="mb-6">
			<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
				{formTitle}
			</h2>
			{#if formDescription}
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
					{formDescription}
				</p>
			{/if}
		</div>

		<!-- Form -->
		<form on:submit|preventDefault={handleSubmit} class="space-y-4">
			{#each formFields as field}
				<div>
					<label
						for={field.name}
						class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
					>
						{field.label}
						{#if field.required}
							<span class="text-red-500">*</span>
						{/if}
					</label>

					{#if field.type === 'textarea'}
						<textarea
							id={field.name}
							bind:value={formData[field.name]}
							placeholder={field.placeholder || ''}
							rows="3"
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-obsidian-500 focus:border-transparent
                           placeholder-gray-400 dark:placeholder-gray-500
                           transition-colors duration-200"
							class:border-red-500={errors[field.name]}
						/>
					{:else if field.type === 'select' && field.options}
						<select
							id={field.name}
							bind:value={formData[field.name]}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-obsidian-500 focus:border-transparent
                           transition-colors duration-200"
							class:border-red-500={errors[field.name]}
						>
							<option value="">{field.placeholder || 'Select an option'}</option>
							{#each field.options as option}
								<option value={option}>{option}</option>
							{/each}
						</select>
					{:else if field.type === 'date'}
						<input
							type="date"
							id={field.name}
							bind:value={formData[field.name]}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-obsidian-500 focus:border-transparent
                           transition-colors duration-200"
							class:border-red-500={errors[field.name]}
						/>
					{:else if field.type === 'number'}
						<input
							type="number"
							id={field.name}
							bind:value={formData[field.name]}
							placeholder={field.placeholder || ''}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-obsidian-500 focus:border-transparent
                           placeholder-gray-400 dark:placeholder-gray-500
                           transition-colors duration-200"
							class:border-red-500={errors[field.name]}
						/>
					{:else if field.type === 'file'}
						<div class="space-y-2">
							<label
								class="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed rounded-lg cursor-pointer
                               border-gray-300 dark:border-gray-600 hover:border-obsidian-400 dark:hover:border-obsidian-500
                               bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800
                               transition-colors duration-200"
								class:border-red-500={errors[field.name]}
							>
								<div class="flex flex-col items-center justify-center pt-2 pb-2">
									<DocumentArrowUp className="size-6 text-gray-400 dark:text-gray-500 mb-1" />
									<p class="text-xs text-gray-500 dark:text-gray-400">
										{field.placeholder || $i18n.t('Click to upload')}
									</p>
									{#if field.accept}
										<p class="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
											{field.accept}
										</p>
									{/if}
								</div>
								<input
									type="file"
									id={field.name}
									class="hidden"
									accept={field.accept || ''}
									multiple={field.multiple || false}
									on:change={(e) => handleFileChange(field.name, e, field.multiple || false)}
								/>
							</label>

							{#if fileData[field.name] && fileData[field.name].length > 0}
								<div class="space-y-1">
									{#each fileData[field.name] as file, idx}
										<div
											class="flex items-center justify-between px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm"
										>
											<div class="flex items-center gap-2 min-w-0">
												<DocumentArrowUp className="size-4 text-obsidian-500 flex-shrink-0" />
												<span class="truncate text-gray-700 dark:text-gray-300">{file.name}</span>
												<span class="text-xs text-gray-400 flex-shrink-0">
													({formatFileSize(file.size)})
												</span>
											</div>
											<button
												type="button"
												class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
												on:click={() => removeFile(field.name, idx)}
											>
												<XMark className="size-4 text-gray-500" />
											</button>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{:else}
						<input
							type="text"
							id={field.name}
							bind:value={formData[field.name]}
							placeholder={field.placeholder || ''}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                           bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                           focus:ring-2 focus:ring-obsidian-500 focus:border-transparent
                           placeholder-gray-400 dark:placeholder-gray-500
                           transition-colors duration-200"
							class:border-red-500={errors[field.name]}
						/>
					{/if}

					{#if errors[field.name]}
						<p class="mt-1 text-sm text-red-500">{errors[field.name]}</p>
					{/if}
				</div>
			{/each}

			<!-- Actions -->
			<div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
				<button
					type="button"
					on:click={handleClose}
					disabled={loading}
					class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300
                       bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600
                       rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700
                       focus:outline-none focus:ring-2 focus:ring-obsidian-500
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors duration-200"
				>
					{$i18n.t('Cancel')}
				</button>
				<button
					type="submit"
					disabled={loading}
					class="px-4 py-2 text-sm font-medium text-white
                       bg-obsidian-600 hover:bg-obsidian-700
                       rounded-lg focus:outline-none focus:ring-2 focus:ring-obsidian-500
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors duration-200 flex items-center gap-2"
				>
					{#if loading}
						<Spinner className="w-4 h-4" />
						{$i18n.t('Processing...')}
					{:else}
						{$i18n.t('Submit')}
					{/if}
				</button>
			</div>
		</form>
	</div>
</Modal>

<style>
	/* Custom obsidian focus ring colors */
	:global(.focus\:ring-obsidian-500:focus) {
		--tw-ring-color: #5b4965;
	}

	:global(.bg-obsidian-600) {
		background-color: #5b4965;
	}

	:global(.bg-obsidian-600:hover),
	:global(.hover\:bg-obsidian-700:hover) {
		background-color: #3d354b;
	}
</style>

