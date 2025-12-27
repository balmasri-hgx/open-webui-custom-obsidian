# n8n Workflow Integration Guide

This document describes how to integrate Obsidian with n8n workflows, enabling users to trigger automated workflows directly from the chat interface.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setting Up a Workflow Model](#setting-up-a-workflow-model)
4. [Trigger Methods](#trigger-methods)
5. [Form Fields](#form-fields)
6. [n8n Webhook Configuration](#n8n-webhook-configuration)
7. [Response Handling](#response-handling)
8. [File Uploads](#file-uploads)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The n8n integration allows you to:

- **Trigger n8n workflows** from the chat interface using slash commands, a dedicated button, or by selecting a workflow-only model
- **Collect user input** through dynamic forms before triggering workflows
- **Upload files** to workflows for processing (e.g., Excel files for data analysis)
- **Display structured responses** including tables, key-value data, and file downloads

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Obsidian Frontend                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │ Slash Cmd   │  │  Workflow   │  │   Workflow-Only Model       │  │
│  │   /report   │  │   Button    │  │   Auto-triggers form        │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────────┘  │
│         │                │                        │                 │
│         └────────────────┼────────────────────────┘                 │
│                          ▼                                          │
│              ┌───────────────────────┐                              │
│              │  WebhookFormModal     │                              │
│              │  - Renders form fields│                              │
│              │  - Validates input    │                              │
│              │  - Handles file upload│                              │
│              └───────────┬───────────┘                              │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Obsidian Backend                            │
├─────────────────────────────────────────────────────────────────────┤
│  POST /api/v1/webhooks/invoke                                       │
│  POST /api/v1/webhooks/invoke-with-files                            │
│                                                                     │
│  - Authenticates user                                               │
│  - Validates form data                                              │
│  - Adds user context (id, email, name)                              │
│  - Forwards to n8n webhook                                          │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           n8n Workflow                              │
├─────────────────────────────────────────────────────────────────────┤
│  Webhook Trigger Node                                               │
│         │                                                           │
│         ▼                                                           │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │
│  │ Process     │──▶│ Generate    │──▶│ Return      │               │
│  │ Data        │   │ Report      │   │ Response    │               │
│  └─────────────┘   └─────────────┘   └─────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Setting Up a Workflow Model

### Step 1: Create or Edit a Model

1. Navigate to **Workspace → Models**
2. Click **Create a Model** or edit an existing one
3. Scroll down to **Workflow Integration (n8n)**

### Step 2: Configure Webhook Settings

| Field | Description | Example |
|-------|-------------|---------|
| **Enable** | Toggle to enable webhook integration | ✓ |
| **Webhook URL** | Your n8n webhook URL (kept secret, never exposed to frontend) | `https://n8n.example.com/webhook/abc123` |
| **Workflow Only Mode** | When enabled, selecting this model auto-triggers the form instead of sending to LLM | ✓ |
| **Slash Command** | Command users type to trigger the workflow | `/report` |
| **Form Title** | Title shown on the form modal | `Generate Sales Report` |
| **Form Description** | Description/instructions for users | `Enter the date range and department` |

### Step 3: Add Form Fields

Click **+ Add Field** to create input fields:

| Property | Description |
|----------|-------------|
| **Name** | Field identifier (used in payload) |
| **Label** | Human-readable label |
| **Type** | `text`, `number`, `date`, `select`, `textarea`, `file` |
| **Required** | Whether the field must be filled |
| **Placeholder** | Hint text in the input |
| **Default Value** | Pre-filled value |
| **Options** | For `select` type: comma-separated list |
| **Accepted File Types** | For `file` type: e.g., `.xlsx,.csv,.pdf` |
| **Allow Multiple** | For `file` type: allow multiple file selection |

### Step 4: Save the Model

Click **Save & Create** or **Save & Update**.

---

## Trigger Methods

### 1. Slash Commands

Users can type a slash command in the chat input to trigger workflows:

```
/report
```

A dropdown will show matching workflows. Selecting one opens the form modal.

### 2. Workflow Button

A **bolt icon** (⚡) appears in the chat input bar when workflows are available. Clicking it shows a dropdown menu of all configured workflows.

### 3. Workflow-Only Models

When a model has **Workflow Only Mode** enabled:
- Selecting the model from the model dropdown
- Typing any message and pressing Enter
- The form modal opens automatically instead of sending to the LLM

This is ideal for dedicated workflow agents like "Report Generator" or "Data Analyzer".

---

## Form Fields

### Text Field
```json
{
  "name": "customer_name",
  "label": "Customer Name",
  "type": "text",
  "required": true,
  "placeholder": "Enter customer name"
}
```

### Number Field
```json
{
  "name": "quantity",
  "label": "Quantity",
  "type": "number",
  "required": true,
  "default": "1"
}
```

### Date Field
```json
{
  "name": "report_date",
  "label": "Report Date",
  "type": "date",
  "required": true
}
```

### Select Field
```json
{
  "name": "department",
  "label": "Department",
  "type": "select",
  "required": true,
  "options": ["Sales", "Marketing", "Engineering", "HR"]
}
```

### Textarea Field
```json
{
  "name": "notes",
  "label": "Additional Notes",
  "type": "textarea",
  "placeholder": "Enter any additional information..."
}
```

### File Upload Field
```json
{
  "name": "data_file",
  "label": "Upload Data File",
  "type": "file",
  "required": true,
  "accept": ".xlsx,.csv",
  "multiple": false
}
```

---

## n8n Webhook Configuration

### Setting Up the Webhook Node

1. In n8n, add a **Webhook** node as the trigger
2. Set **HTTP Method** to `POST`
3. Copy the webhook URL and paste it into the Obsidian model configuration

### Incoming Payload Structure

Obsidian sends the following JSON payload to your n8n webhook:

```json
{
  "user_id": "user-uuid-here",
  "user_email": "user@example.com",
  "user_name": "John Doe",
  "model_id": "sales-report-generator",
  "chat_id": "chat-uuid-here",
  "form_data": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "department": "Sales"
  },
  "files": [
    {
      "name": "data.xlsx",
      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "size": 15234,
      "data": "base64-encoded-content..."
    }
  ]
}
```

### HTTP Headers

| Header | Description |
|--------|-------------|
| `Content-Type` | `application/json` |
| `X-Obsidian-User-Id` | The authenticated user's ID |
| `X-Obsidian-Model-Id` | The model ID that triggered the workflow |

---

## Response Handling

### Expected Response Format

Your n8n workflow should return a JSON response:

```json
{
  "message": "Report generated successfully!",
  "file_url": "https://storage.example.com/reports/report-123.xlsx",
  "file_name": "Sales_Report_Jan_2025.xlsx",
  "data": [
    {"region": "North", "sales": 150000, "growth": "12%"},
    {"region": "South", "sales": 120000, "growth": "8%"},
    {"region": "East", "sales": 180000, "growth": "15%"}
  ]
}
```

### Response Field Mapping

Obsidian recognizes these response fields (case-insensitive, multiple naming conventions supported):

| Purpose | Recognized Fields |
|---------|-------------------|
| Message | `message`, `text`, `response` |
| File URL | `file_url`, `fileUrl`, `download_url`, `downloadUrl`, `url` |
| File Name | `file_name`, `fileName`, `filename`, `name` |
| Structured Data | `data` (array or object) |

### How Responses Are Displayed

1. **Message**: Rendered as markdown in the chat
2. **Tables**: Arrays of objects are rendered as markdown tables
3. **Key-Value**: Objects are rendered as two-column tables
4. **Files**: Download link with button is displayed

---

## File Uploads

### How Files Are Sent to n8n

Files are encoded as **base64** and included in the `files` array:

```json
{
  "files": [
    {
      "name": "report.xlsx",
      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "size": 15234,
      "data": "UEsDBBQAAAAIAKxiV1..."
    }
  ]
}
```

### Processing Files in n8n

Use the **Code** node or **Spreadsheet File** node to process:

```javascript
// In a Code node
const files = $input.first().json.files;

for (const file of files) {
  const buffer = Buffer.from(file.data, 'base64');
  // Process the file...
}
```

### File Size Considerations

- Files are base64 encoded (increases size by ~33%)
- The backend has a 120-second timeout for webhook requests
- For very large files, consider using a separate file upload endpoint

---

## API Reference

### GET `/api/v1/webhooks/config/{model_id}`

Returns the webhook configuration for a model (excluding the webhook URL).

**Response:**
```json
{
  "enabled": true,
  "workflow_only": false,
  "slash_command": "/report",
  "form_title": "Generate Report",
  "form_description": "Enter report parameters",
  "form_fields": [...]
}
```

### POST `/api/v1/webhooks/invoke`

Invokes a webhook with form data (no files).

**Request Body:**
```json
{
  "model_id": "report-generator",
  "form_data": {"field1": "value1"},
  "chat_id": "optional-chat-id"
}
```

### POST `/api/v1/webhooks/invoke-with-files`

Invokes a webhook with form data and file uploads.

**Request:** `multipart/form-data`
- `model_id`: string
- `form_data_json`: JSON string of form data
- `chat_id`: optional string
- `files`: file(s)

### GET `/api/v1/webhooks/models`

Returns all models with webhook integration enabled.

**Response:**
```json
[
  {
    "id": "report-generator",
    "name": "Report Generator",
    "slash_command": "/report",
    "form_title": "Generate Report"
  }
]
```

---

## Troubleshooting

### Workflow Not Appearing

1. **Check webhook is enabled**: Model → Workflow Integration → Enable toggle
2. **Check slash command**: Must start with `/`
3. **Refresh the page**: Workflow list is cached on page load

### Form Not Opening

1. **Check browser console**: Look for API errors
2. **Verify model ID**: The model must exist and have valid webhook config

### Webhook Timeout

- Default timeout is **120 seconds**
- For long-running workflows, consider:
  - Returning immediately with a "processing" message
  - Using n8n's async execution features
  - Implementing a polling mechanism

### Files Not Received

1. **Check file size**: Very large files may fail
2. **Verify content type**: Ensure n8n is parsing JSON body correctly
3. **Check n8n logs**: Look for parsing errors

### Response Not Displaying Correctly

1. **Verify JSON format**: Response must be valid JSON
2. **Check field names**: Use recognized field names (see Response Handling)
3. **Test with simple response**: Start with `{"message": "Hello"}` and build up

---

## Example: Sales Report Workflow

### Model Configuration

| Setting | Value |
|---------|-------|
| Name | Sales Report Generator |
| Slash Command | `/sales-report` |
| Form Title | Generate Sales Report |
| Workflow Only | ✓ (enabled) |

### Form Fields

1. **Start Date** (date, required)
2. **End Date** (date, required)
3. **Region** (select: North, South, East, West)
4. **Format** (select: PDF, Excel, CSV)

### n8n Workflow

1. **Webhook** trigger
2. **MySQL** node - Query sales data
3. **Spreadsheet File** node - Generate Excel
4. **S3** node - Upload file
5. **Respond to Webhook** node - Return download URL

### n8n Response

```json
{
  "message": "Sales report for North region generated successfully.",
  "file_url": "https://s3.example.com/reports/sales-north-2025-01.xlsx",
  "file_name": "Sales_Report_North_Jan_2025.xlsx",
  "data": {
    "total_sales": "$450,000",
    "total_orders": 1234,
    "average_order": "$365"
  }
}
```

---

## Security Considerations

1. **Webhook URLs are never exposed** to the frontend - only the backend makes requests to n8n
2. **User context is always included** in webhook payloads for audit trails
3. **Authentication is required** - only logged-in users can trigger webhooks
4. **Model access control** applies - users can only access workflows they have permission to use

---

*Last Updated: December 27, 2025*

