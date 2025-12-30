# Obsidian Pipes

This folder contains the source code for custom Pipe functions used in the Obsidian portal.

## What are Pipes?

Pipes are custom Python functions that act as "models" in Open WebUI. When a user selects a Pipe, their messages go through your Python code instead of an LLM. This allows you to:

- Call external APIs (like n8n workflows)
- Process data
- Generate custom responses

## How to Deploy a Pipe

1. **Copy the code** from the `.py` file in this folder
2. **Go to Open WebUI** → Workspace → Functions
3. **Create new** or **Edit existing** function
4. **Paste the code** into the editor
5. **Save** and ensure it's **Active**

## Available Pipes

| Pipe | File | Description |
|------|------|-------------|
| Billing Report | `billing_report.py` | Triggers n8n billing workflow with customizable parameters |
| Diagnostic OCR | `diagnostic_ocr.py` | Classifies PDF document pages and extracts accession numbers |

---

## Billing Report Pipe

Triggers n8n billing workflow with customizable parameters. **All parameters are required** - no default reports are generated.

### Getting Started

When you first open the Billing Report pipe, type `help` or any message to see the usage guide:

```
help
```

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `protocol` | Protocol ID | `MK3543006` |
| `start_date` | Report start date | `2025-01-01` |
| `end_date` | Report end date | `2025-03-31` |

**Optional:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `group_facilities` | Group by facilities | `false` |

### Usage Examples

**Single report with specific dates:**
```
protocol=MK3543006 start_date=2025-01-01 end_date=2025-03-31
```

**With date shortcut (protocol still required):**
```
protocol=MK3543006 this_month
```

**With group facilities:**
```
protocol=MK3543006 start_date=2025-01-01 end_date=2025-03-31 group_facilities=true
```

### Date Shortcuts

Use these shortcuts instead of specifying `start_date` and `end_date`:

| Shortcut | Description |
|----------|-------------|
| `this_month` | Current month (1st to last day) |
| `last_month` | Previous month |
| `this_year` | Current year (Jan 1 - Dec 31) |
| `last_year` | Previous year |
| `q1` | Q1 of current year (Jan-Mar) |
| `q2` | Q2 of current year (Apr-Jun) |
| `q3` | Q3 of current year (Jul-Sep) |
| `q4` | Q4 of current year (Oct-Dec) |

### Batch Processing - Multiple Protocols

**Comma-separated:**
```
protocols=MK1111111,MK2222222,MK3333333 q1
```

**One per line:**
```
MK1111111
MK2222222
MK3333333
```
*(Note: When listing protocols one per line, use date shortcuts or specify dates)*

### Excel/CSV File Upload (Batch Processing)

Upload an Excel file (.xlsx) or CSV file (.csv) with the following columns:

| Protocol | start_date | end_date | group_facilities |
|----------|------------|----------|------------------|
| MK1111111 | 2025-01-01 | 2025-03-31 | false |
| MK2222222 | 2025-04-01 | 2025-06-30 | true |
| MK3333333 | 2025-07-01 | 2025-09-30 | false |

**Column names are flexible:**
- `Protocol`, `protocol`, `PROTOCOL` all work
- `start_date`, `Start Date`, `start-date` all work
- Same for `end_date` and `group_facilities`

**Dates can be in various formats:**
- `2025-01-01` (preferred)
- `01/01/2025`
- `1/1/2025`
- Excel date values

Just upload the file and send any message - the Pipe will detect the Excel file and process each row.

### Configuration (Valves)

After deploying the Pipe, configure these settings in Open WebUI:

| Setting | Description | Default |
|---------|-------------|---------|
| `N8N_WEBHOOK_URL` | Your n8n webhook URL | `https://10.1.21.253:5678/webhook/...` |
| `DEFAULT_GROUP_FACILITIES` | Default group_facilities value | `false` |

### Features

- ✅ **Interactive help** - Type `help` to see usage guide
- ✅ **Parameter validation** - Shows missing required parameters
- ✅ **Date shortcuts** - Use `this_month`, `q1`, etc. instead of dates
- ✅ **Batch processing** - Multiple protocols in one request
- ✅ **Excel/CSV upload** - Upload spreadsheet for bulk reports
- ✅ **Duplicate prevention** - Prevents accidental duplicate n8n calls
- ✅ **Auto time formatting** - Dates automatically get 00:00:00 / 23:59:59

---

## Diagnostic OCR Pipe

Analyzes PDF documents page-by-page using a vision model, classifying each page and extracting accession numbers from Hematogenix result sheets.

### Usage

1. Upload a PDF document using the attachment button (📎)
2. Send any message (e.g., "analyze" or just press Enter)
3. The workflow will process each page and return a classification summary

### Page Categories

| Category | Description |
|----------|-------------|
| 1 | Package Tracking Sheet |
| 2 | Patient Demographic Sheet |
| 3 | Billing Sheet |
| 4 | Patient Result Sheet (not Hematogenix) |
| 5 | Patient Result Sheet (Hematogenix) |

### Expected n8n Response Format

The n8n workflow should return a JSON object with this structure:

```json
{
  "total_pages": 10,
  "categories_found": {
    "1": 2,
    "2": 3,
    "5": 2
  },
  "accession_numbers": ["ABC25-00123", "XYZ25-00456"],
  "message": "Optional status message"
}
```

### Sample Output

```
## ✅ Document Analysis Complete

**File:** diagnostic_example01.pdf
**Total Pages:** 10

### Page Classification Summary

| Category | Description | Count |
|----------|-------------|-------|
| 1 | Package Tracking Sheet | 2 |
| 2 | Patient Demographic Sheet | 3 |
| 5 | Patient Result Sheet (Hematogenix) | 2 |

### Accession Numbers Found
- `ABC25-00123`
- `XYZ25-00456`
```

### Configuration (Valves)

| Setting | Description | Default |
|---------|-------------|---------|
| `N8N_WEBHOOK_URL` | Your n8n webhook URL for the OCR workflow | `https://10.1.21.253:5678/webhook/diagnostic-ocr` |
| `ALLOWED_EXTENSIONS` | Comma-separated allowed file extensions | `.pdf` |
| `REQUEST_TIMEOUT` | Timeout in seconds (large PDFs take longer) | `300` |

### n8n Webhook Payload

The pipe sends the following JSON to your n8n webhook:

```json
{
  "user_id": "user-uuid",
  "user_email": "user@example.com",
  "user_name": "User Name",
  "file_name": "document.pdf",
  "file_data": "<base64-encoded-pdf>",
  "file_type": "application/pdf"
}
```

### n8n Workflow Setup

1. Add a **Webhook** node (POST) to accept the payload
2. Decode the `file_data` from base64
3. Process through your PDF→JPG→Vision classification pipeline
4. Add a **Respond to Webhook** node returning the summary JSON

---

## Development Workflow

1. Edit the `.py` file in this folder
2. Test locally if possible
3. Copy updated code to Open WebUI
4. Test in the Obsidian portal

## Version History

### Billing Report Pipe

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-28 | Initial version with basic parameter support |
| 0.2 | 2025-12-28 | Added date shortcuts, batch processing, auto time formatting |
| 0.3 | 2025-12-29 | Added Excel file upload for batch processing |
| 0.4 | 2025-12-29 | Fixed file reading via Open WebUI storage system |
| 0.5 | 2025-12-29 | Added duplicate prevention (message-level and payload-level) |
| 0.6 | 2025-12-29 | Removed default report, added help command, required parameter validation |

### Diagnostic OCR Pipe

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-29 | Initial version with PDF upload and page classification |

