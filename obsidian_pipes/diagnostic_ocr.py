"""
title: Diagnostic OCR Document Classifier
author: Bishr
version: 0.2
description: Sends PDF documents to n8n workflow for page classification and accession number extraction
"""

from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import urllib3
import base64
import hashlib
import time

# Suppress SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Track in-progress requests to prevent duplicates
_PROCESSING_FILES = {}  # {file_hash: timestamp}


# Category descriptions mapping (matches n8n workflow classification)
CATEGORY_DESCRIPTIONS = {
    1: "Package Tracking Sheet",
    2: "Patient Demographic Sheet",
    3: "Billing Sheet",
    4: "Patient Result Sheet (not Hematogenix)",
    5: "Patient Result Sheet (Hematogenix)",
}


class Pipe:
    class Valves(BaseModel):
        """Configurable settings - accessible from the Open WebUI admin UI"""

        N8N_WEBHOOK_URL: str = Field(
            default="https://10.1.21.253:5678/webhook/diagnostic-ocr",
            description="Your n8n webhook URL for the Diagnostic OCR workflow",
        )
        ALLOWED_EXTENSIONS: str = Field(
            default=".pdf",
            description="Comma-separated list of allowed file extensions (e.g., .pdf,.PDF)",
        )
        REQUEST_TIMEOUT: int = Field(
            default=1800,
            description="Request timeout in seconds (default: 1800 = 30 minutes for large documents)",
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "diagnostic_ocr"
        self.name = "Diagnostic OCR Classifier"
        self.valves = self.Valves()
        # Enable file handling
        self.file_handler = True

    def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__=None,
        __files__: Optional[list] = None,
    ) -> Union[str, Generator, Iterator]:
        """
        Main pipe function - called when a user sends a message.
        
        Accepts PDF file uploads and sends them to n8n for classification.
        Returns a summary of page classifications and any accession numbers found.
        """
        
        # Get the user's message
        messages = body.get("messages", [])
        user_message = ""
        if messages:
            last_message = messages[-1]
            if last_message.get("role") == "user":
                user_message = last_message.get("content", "")
        
        # Check if user wants to force reprocessing (bypass duplicate check)
        force_reprocess = any(keyword in user_message.lower() for keyword in ["force", "retry", "reprocess", "again"])
        
        # Check for files in various locations
        files = __files__ or []
        
        # Also check metadata for files
        metadata = body.get("metadata", {})
        if not files and metadata.get("files"):
            files = metadata.get("files", [])
        
        # Find PDF files
        pdf_file = self._find_pdf_file(files)
        
        if not pdf_file:
            # DEBUG: Show what we received to diagnose file handling
            return self._debug_file_info(files, __files__, body)
        
        # Process the PDF
        return self._process_document(pdf_file, __user__, force_reprocess)

    def _find_pdf_file(self, files: list) -> Optional[dict]:
        """
        Find the first valid PDF file from the uploaded files.
        
        Returns file info dict with 'name' and 'data' (base64) keys.
        
        Handles Open WebUI's file structure:
        {
            'type': 'file',
            'name': 'document.pdf',
            'file': {
                'path': '/app/backend/data/uploads/...',
                'filename': 'document.pdf',
                ...
            }
        }
        """
        if not files:
            return None
        
        # Parse allowed extensions
        allowed_exts = [
            ext.strip().lower() 
            for ext in self.valves.ALLOWED_EXTENSIONS.split(",")
        ]
        
        for file_info in files:
            if not isinstance(file_info, dict):
                continue
            
            # Get file name - check multiple locations
            file_name = (
                file_info.get("name") 
                or file_info.get("filename")
                or (file_info.get("file", {}).get("filename") if isinstance(file_info.get("file"), dict) else None)
                or ""
            )
            if not file_name:
                continue
            
            # Check extension
            file_ext = "." + file_name.lower().split(".")[-1] if "." in file_name else ""
            if file_ext not in allowed_exts:
                continue
            
            # Get file data as base64
            file_data_b64 = self._extract_file_data(file_info)
            if file_data_b64:
                return {
                    "name": file_name,
                    "data": file_data_b64,
                    "type": file_info.get("content_type", "application/pdf"),
                }
        
        return None

    def _extract_file_data(self, file_info: dict) -> Optional[str]:
        """
        Extract file data and return as base64 string.
        
        Handles various file info formats from Open WebUI, including:
        - Direct path: file_info['path']
        - Nested structure: file_info['file']['path']
        - Base64 data: file_info['data']
        - Content: file_info['content']
        """
        
        # Priority 1: Check for nested 'file' object with 'path' (Open WebUI's format)
        if "file" in file_info and isinstance(file_info["file"], dict):
            nested_file = file_info["file"]
            if "path" in nested_file:
                try:
                    with open(nested_file["path"], "rb") as f:
                        return base64.b64encode(f.read()).decode("utf-8")
                except Exception as e:
                    print(f"Error reading file from nested path: {e}")
        
        # Priority 2: Direct path
        if "path" in file_info:
            try:
                with open(file_info["path"], "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception as e:
                print(f"Error reading file from path: {e}")
        
        # Priority 3: Already base64 encoded data
        if "data" in file_info:
            file_data = file_info["data"]
            # Skip if data is the error dict from text extraction
            if isinstance(file_data, dict):
                pass  # This is the extraction error, not actual data
            elif isinstance(file_data, str):
                # Remove data URL prefix if present
                if "," in file_data and "base64" in file_data:
                    file_data = file_data.split(",", 1)[1]
                return file_data
            elif isinstance(file_data, bytes):
                return base64.b64encode(file_data).decode("utf-8")
        
        # Priority 4: Content field
        if "content" in file_info:
            content = file_info["content"]
            if isinstance(content, str):
                return content
            elif isinstance(content, bytes):
                return base64.b64encode(content).decode("utf-8")
        
        # Priority 5: URL download
        if "url" in file_info:
            url = file_info["url"]
            # Skip if URL is just an ID (not a real URL)
            if url and url.startswith("http"):
                try:
                    response = requests.get(url, timeout=30)
                    return base64.b64encode(response.content).decode("utf-8")
                except Exception:
                    pass
        
        return None

    def _debug_file_info(self, files: list, raw_files: Optional[list], body: dict) -> str:
        """Debug helper to see what file data we're receiving."""
        import json as debug_json
        
        output = "## 🔍 Debug: File Upload Analysis\n\n"
        output += "The pipe couldn't find a valid PDF. Here's what was received:\n\n"
        
        # Check __files__ parameter
        output += "### `__files__` Parameter\n"
        if raw_files:
            output += f"- **Count:** {len(raw_files)}\n"
            for i, f in enumerate(raw_files):
                output += f"\n**File {i+1}:**\n"
                output += f"- Type: `{type(f).__name__}`\n"
                if isinstance(f, dict):
                    output += f"- Keys: `{list(f.keys())}`\n"
                    for key in f:
                        val = f[key]
                        if isinstance(val, str) and len(val) > 100:
                            output += f"- {key}: `{val[:100]}...` (len={len(val)})\n"
                        elif isinstance(val, bytes):
                            output += f"- {key}: `<bytes len={len(val)}>`\n"
                        else:
                            output += f"- {key}: `{val}`\n"
                else:
                    output += f"- Value: `{str(f)[:200]}`\n"
        else:
            output += "- **Empty or None**\n"
        
        # Check metadata
        output += "\n### `body.metadata.files`\n"
        metadata = body.get("metadata", {})
        meta_files = metadata.get("files", [])
        if meta_files:
            output += f"- **Count:** {len(meta_files)}\n"
            for i, f in enumerate(meta_files):
                output += f"\n**File {i+1}:**\n"
                output += f"- Type: `{type(f).__name__}`\n"
                if isinstance(f, dict):
                    output += f"- Keys: `{list(f.keys())}`\n"
                    for key in ['id', 'name', 'filename', 'type', 'path', 'url']:
                        if key in f:
                            output += f"- {key}: `{f[key]}`\n"
                    if 'data' in f:
                        data = f['data']
                        output += f"- data: `<{type(data).__name__} len={len(data) if data else 0}>`\n"
        else:
            output += "- **Empty**\n"
        
        # Check messages for file references
        output += "\n### Message Content\n"
        messages = body.get("messages", [])
        if messages:
            last_msg = messages[-1]
            content = last_msg.get("content", "")
            if isinstance(content, list):
                output += "- Content is a **list** (multimodal message)\n"
                for i, part in enumerate(content):
                    if isinstance(part, dict):
                        output += f"  - Part {i}: type=`{part.get('type')}`, keys=`{list(part.keys())}`\n"
            else:
                output += f"- Content: `{str(content)[:100]}`\n"
        
        # Show other metadata keys
        output += "\n### Other Metadata Keys\n"
        output += f"- Keys: `{list(metadata.keys())}`\n"
        
        return output

    def _no_file_response(self) -> str:
        """Return help message when no PDF file is uploaded."""
        allowed = self.valves.ALLOWED_EXTENSIONS
        return f"""## 📄 Diagnostic OCR Classifier

Please upload a PDF document to analyze.

### How to Use
1. Click the attachment button (📎) in the chat
2. Upload a PDF file
3. Send any message (e.g., "analyze" or just press enter)

### What This Does
- Analyzes each page of your document
- Classifies pages into categories:
  - **1**: Package Tracking Sheet
  - **2**: Patient Demographic Sheet
  - **3**: Billing Sheet
  - **4**: Patient Result Sheet (not Hematogenix)
  - **5**: Patient Result Sheet (Hematogenix)
- Extracts Accession Numbers from Hematogenix result sheets

### Supported File Types
{allowed}
"""

    def _process_document(self, pdf_file: dict, __user__: Optional[dict], force: bool = False) -> str:
        """Process the PDF document through n8n workflow."""
        global _PROCESSING_FILES
        
        file_name = pdf_file["name"]
        
        # Create a hash of the file to detect duplicates
        file_hash = hashlib.md5(pdf_file["data"][:1000].encode() if isinstance(pdf_file["data"], str) else pdf_file["data"][:1000]).hexdigest()
        current_time = time.time()
        
        # Check if this file is already being processed (within last 30 minutes)
        # Skip check if force=True
        if not force and file_hash in _PROCESSING_FILES:
            last_time = _PROCESSING_FILES[file_hash]
            elapsed = current_time - last_time
            if elapsed < 1800:  # 30 minutes
                return f"""## ⏳ Document Already Processing

This document is already being analyzed. Please wait for the current analysis to complete.

**File:** `{file_name}`
**Started:** {int(elapsed)} seconds ago

To force reprocessing, type **"retry"** or **"force"** with your message.
"""
        
        # Mark as processing
        _PROCESSING_FILES[file_hash] = current_time
        
        # Clean up old entries (older than 30 minutes)
        _PROCESSING_FILES = {k: v for k, v in _PROCESSING_FILES.items() if current_time - v < 1800}
        
        # Generate unique request ID
        request_id = f"{file_hash[:8]}-{int(current_time)}"
        
        # Build payload
        payload = {
            "request_id": request_id,
            "user_id": __user__.get("id") if __user__ else None,
            "user_email": __user__.get("email") if __user__ else None,
            "user_name": __user__.get("name") if __user__ else None,
            "file_name": pdf_file["name"],
            "file_data": pdf_file["data"],
            "file_type": pdf_file["type"],
        }
        
        try:
            # Create a session with NO retries
            session = requests.Session()
            adapter = HTTPAdapter(max_retries=Retry(total=0))  # No retries
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Call n8n webhook
            response = session.post(
                self.valves.N8N_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.valves.REQUEST_TIMEOUT,
                verify=False,  # Allow self-signed certificates
            )
            response.raise_for_status()
            
            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError:
                result = {"message": response.text}
            
            # Clear processing flag on success
            if file_hash in _PROCESSING_FILES:
                del _PROCESSING_FILES[file_hash]
            
            return self._format_response(result, file_name)
            
        except requests.exceptions.Timeout:
            # Clear processing flag on timeout
            if file_hash in _PROCESSING_FILES:
                del _PROCESSING_FILES[file_hash]
                
            return f"""## ⚠️ Request Timed Out

The document analysis took too long to complete.

**File:** `{file_name}`
**Timeout:** {self.valves.REQUEST_TIMEOUT} seconds

This may happen with large PDF files. Please try again or contact support if the issue persists.
"""
        
        except requests.exceptions.RequestException as e:
            # Clear processing flag on error
            if file_hash in _PROCESSING_FILES:
                del _PROCESSING_FILES[file_hash]
                
            return f"""## ⚠️ Connection Error

Failed to connect to the OCR workflow.

**File:** `{file_name}`
**Error:** 
```
{str(e)}
```

Please check that the n8n workflow is running and the webhook URL is correct.
"""
        
        except Exception as e:
            # Clear processing flag on error
            if file_hash in _PROCESSING_FILES:
                del _PROCESSING_FILES[file_hash]
                
            return f"""## ⚠️ Unexpected Error

An error occurred while processing the document.

**File:** `{file_name}`
**Error:** `{str(e)}`
"""

    def _format_response(self, result: dict, file_name: str) -> str:
        """Format the n8n response for display in chat."""
        
        # Debug: Log raw response structure
        print(f"[Diagnostic OCR] Raw response type: {type(result)}")
        print(f"[Diagnostic OCR] Raw response keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        # Handle array response (n8n often returns arrays)
        if isinstance(result, list):
            if len(result) > 0 and isinstance(result[0], dict):
                result = result[0]
                print(f"[Diagnostic OCR] Unwrapped array, keys: {result.keys()}")
            else:
                return f"""## ✅ Document Processed

**File:** `{file_name}`

### Raw Response:
```json
{json.dumps(result, indent=2)}
```
"""
        
        # Extract fields from response - try multiple possible field names
        total_pages = result.get("total_pages") or result.get("totalPages") or result.get("pageCount") or 0
        categories_found = result.get("categories_found") or result.get("categoriesFound") or result.get("summary") or {}
        accession_numbers = result.get("accession_numbers") or result.get("accessionNumbers") or []
        pages = result.get("pages") or result.get("results") or result.get("classifications") or []
        
        # Debug: Log extracted data
        if pages:
            print(f"[Diagnostic OCR] First page data: {pages[0] if pages else 'empty'}")
        message = result.get("message", "")
        
        # Build output
        output = "## ✅ Document Analysis Complete\n\n"
        output += f"**File:** `{file_name}`\n"
        
        if total_pages:
            output += f"**Total Pages:** {total_pages}\n"
        
        output += "\n"
        
        # Add message if present
        if message:
            output += f"{message}\n\n"
        
        # Category summary table
        if categories_found:
            output += "### Category Summary\n\n"
            output += "| Category | Description | Count |\n"
            output += "|----------|-------------|-------|\n"
            
            # Sort by category number
            for cat_num in sorted(categories_found.keys(), key=lambda x: int(x) if str(x).isdigit() else 999):
                count = categories_found[cat_num]
                description = CATEGORY_DESCRIPTIONS.get(int(cat_num) if str(cat_num).isdigit() else 0, "Unknown")
                output += f"| {cat_num} | {description} | {count} |\n"
            
            output += "\n"
        
        # Page-by-page breakdown
        if pages:
            output += "### Page-by-Page Classification\n\n"
            output += "| Page | Category | Description | Accession # |\n"
            output += "|------|----------|-------------|-------------|\n"
            
            for idx, page in enumerate(pages):
                # Handle multiple possible field names for page number
                page_num = (
                    page.get("page") or 
                    page.get("page_number") or 
                    page.get("pageNumber") or 
                    page.get("pageNum") or
                    page.get("index") or
                    idx + 1  # Fallback to 1-based index
                )
                
                # Handle category field
                cat = page.get("category") or page.get("classification") or "?"
                
                # Handle description - try multiple sources
                desc = (
                    page.get("category_description") or 
                    page.get("description") or
                    page.get("categoryDescription") or
                    CATEGORY_DESCRIPTIONS.get(int(cat) if str(cat).isdigit() else 0, "Unknown")
                )
                
                # Handle accession number
                acc = page.get("accession_number") or page.get("accessionNumber") or page.get("accession") or ""
                
                # Truncate description if too long
                if len(str(desc)) > 35:
                    desc = str(desc)[:32] + "..."
                
                output += f"| {page_num} | {cat} | {desc} | {acc} |\n"
            
            output += "\n"
        
        # Accession numbers found
        if accession_numbers:
            output += "### Accession Numbers Found\n\n"
            for acc_num in accession_numbers:
                output += f"- `{acc_num}`\n"
            output += "\n"
        
        # If no structured data, show raw response
        if not categories_found and not accession_numbers and not message and not pages:
            output += "### Response Data:\n"
            output += f"```json\n{json.dumps(result, indent=2)}\n```\n"
        
        return output

