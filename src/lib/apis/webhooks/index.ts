import { WEBUI_API_BASE_URL } from '$lib/constants';

/**
 * Webhook form field definition
 */
export type WebhookFormField = {
	name: string;
	label: string;
	type: 'text' | 'number' | 'date' | 'select' | 'textarea' | 'file';
	required: boolean;
	placeholder?: string;
	options?: string[];
	default?: string;
	accept?: string; // For file fields: accepted MIME types
	multiple?: boolean; // For file fields: allow multiple files
};

/**
 * Webhook configuration for a model
 */
export type WebhookConfig = {
	enabled: boolean;
	workflow_only?: boolean;
	slash_command?: string;
	form_title?: string;
	form_description?: string;
	form_fields?: WebhookFormField[];
};

/**
 * Response from webhook invocation
 */
export type WebhookResponse = {
	success: boolean;
	message?: string;
	data?: Record<string, unknown>;
	file_url?: string;
	file_name?: string;
};

/**
 * Webhook-enabled model info
 */
export type WebhookModel = {
	id: string;
	name: string;
	slash_command?: string;
	form_title?: string;
};

/**
 * Get webhook configuration for a specific model
 */
export const getWebhookConfig = async (token: string, modelId: string): Promise<WebhookConfig> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/webhooks/config/${modelId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Invoke a webhook with form data
 */
export const invokeWebhook = async (
	token: string,
	modelId: string,
	formData: Record<string, unknown>,
	chatId?: string
): Promise<WebhookResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/webhooks/invoke`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			model_id: modelId,
			form_data: formData,
			chat_id: chatId
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || err.message || 'Unknown error';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Invoke a webhook with form data and file uploads
 */
export const invokeWebhookWithFiles = async (
	token: string,
	modelId: string,
	formData: Record<string, unknown>,
	files: File[],
	chatId?: string
): Promise<WebhookResponse> => {
	let error = null;

	const multipartFormData = new FormData();
	multipartFormData.append('model_id', modelId);
	multipartFormData.append('form_data_json', JSON.stringify(formData));
	if (chatId) {
		multipartFormData.append('chat_id', chatId);
	}
	
	// Append files
	for (const file of files) {
		multipartFormData.append('files', file);
	}

	const res = await fetch(`${WEBUI_API_BASE_URL}/webhooks/invoke-with-files`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		},
		body: multipartFormData
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail || err.message || 'Unknown error';
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

/**
 * Get all models that have webhook integration enabled
 */
export const getWebhookEnabledModels = async (token: string): Promise<WebhookModel[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/webhooks/models`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return [];
		});

	if (error) {
		throw error;
	}

	return res;
};

