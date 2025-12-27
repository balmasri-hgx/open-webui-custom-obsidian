"""
Webhooks router for n8n and external workflow integrations.
Allows models to be configured with webhook URLs that can be triggered via slash commands.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any
import logging
import httpx
import json
import base64

from open_webui.utils.auth import get_verified_user
from open_webui.models.models import Models

log = logging.getLogger(__name__)

router = APIRouter()


##################################
#
# Webhook Request/Response Models
#
##################################


class WebhookInvokeForm(BaseModel):
    """Form data for invoking a webhook."""
    model_id: str
    """The model ID that has the webhook configuration."""
    
    form_data: dict[str, Any]
    """The form field values collected from the user."""
    
    chat_id: Optional[str] = None
    """Optional chat ID for context."""


class WebhookResponse(BaseModel):
    """Response from a webhook invocation."""
    success: bool
    message: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None


##################################
#
# Webhook Endpoints
#
##################################


@router.get("/config/{model_id}")
async def get_webhook_config(
    model_id: str,
    request: Request,
    user=Depends(get_verified_user)
):
    """
    Get the webhook configuration for a specific model.
    Returns the slash command and form fields if configured.
    """
    model = Models.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Get webhook config from model meta
    webhook_config = model.meta.webhook if model.meta and model.meta.webhook else None
    
    if not webhook_config or not webhook_config.enabled:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"enabled": False}
        )
    
    # Return config without exposing the actual webhook URL to the frontend
    return {
        "enabled": webhook_config.enabled,
        "workflow_only": webhook_config.workflow_only if hasattr(webhook_config, 'workflow_only') else False,
        "slash_command": webhook_config.slash_command,
        "form_title": webhook_config.form_title,
        "form_description": webhook_config.form_description,
        "form_fields": [field.model_dump() for field in webhook_config.form_fields] if webhook_config.form_fields else []
    }


@router.post("/invoke")
async def invoke_webhook(
    form_data: WebhookInvokeForm,
    request: Request,
    user=Depends(get_verified_user)
):
    """
    Invoke the webhook for a model with the provided form data.
    This calls the configured n8n/external webhook URL and returns the response.
    """
    model = Models.get_model_by_id(form_data.model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    webhook_config = model.meta.webhook if model.meta and model.meta.webhook else None
    
    if not webhook_config or not webhook_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook is not enabled for this model"
        )
    
    if not webhook_config.webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL is not configured for this model"
        )
    
    # Validate required fields
    if webhook_config.form_fields:
        for field in webhook_config.form_fields:
            if field.required and field.name not in form_data.form_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Required field '{field.label}' is missing"
                )
    
    # Prepare the payload for the webhook
    payload = {
        "user_id": user.id,
        "user_email": user.email,
        "user_name": user.name,
        "model_id": form_data.model_id,
        "chat_id": form_data.chat_id,
        "form_data": form_data.form_data,
    }
    
    log.info(f"Invoking webhook for model {form_data.model_id} by user {user.email}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                webhook_config.webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Obsidian-User-Id": user.id,
                    "X-Obsidian-Model-Id": form_data.model_id,
                }
            )
            
            log.debug(f"Webhook response status: {response.status_code}")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except Exception:
                response_data = {"raw_response": response.text}
            
            if response.status_code >= 400:
                return JSONResponse(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    content={
                        "success": False,
                        "message": f"Webhook returned error: {response.status_code}",
                        "data": response_data
                    }
                )
            
            # Handle different response formats from n8n
            # n8n can return various formats, we normalize them here
            
            # Check if response contains a file URL
            file_url = None
            file_name = None
            message = None
            
            if isinstance(response_data, dict):
                # Look for common file URL patterns in n8n responses
                file_url = (
                    response_data.get("file_url") or
                    response_data.get("fileUrl") or
                    response_data.get("download_url") or
                    response_data.get("downloadUrl") or
                    response_data.get("url")
                )
                file_name = (
                    response_data.get("file_name") or
                    response_data.get("fileName") or
                    response_data.get("filename") or
                    response_data.get("name")
                )
                message = (
                    response_data.get("message") or
                    response_data.get("text") or
                    response_data.get("response")
                )
            elif isinstance(response_data, list) and len(response_data) > 0:
                # n8n often returns arrays, take first item
                first_item = response_data[0]
                if isinstance(first_item, dict):
                    file_url = (
                        first_item.get("file_url") or
                        first_item.get("fileUrl") or
                        first_item.get("download_url") or
                        first_item.get("downloadUrl") or
                        first_item.get("url")
                    )
                    file_name = (
                        first_item.get("file_name") or
                        first_item.get("fileName") or
                        first_item.get("filename") or
                        first_item.get("name")
                    )
                    message = (
                        first_item.get("message") or
                        first_item.get("text") or
                        first_item.get("response")
                    )
            
            return {
                "success": True,
                "message": message or "Workflow executed successfully",
                "data": response_data,
                "file_url": file_url,
                "file_name": file_name
            }
            
    except httpx.TimeoutException:
        log.error(f"Webhook timeout for model {form_data.model_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Webhook request timed out"
        )
    except httpx.RequestError as e:
        log.error(f"Webhook request error for model {form_data.model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to webhook: {str(e)}"
        )
    except Exception as e:
        log.error(f"Unexpected error invoking webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.post("/invoke-with-files")
async def invoke_webhook_with_files(
    request: Request,
    model_id: str = Form(...),
    form_data_json: str = Form(...),
    chat_id: Optional[str] = Form(None),
    files: list[UploadFile] = File(default=[]),
    user=Depends(get_verified_user)
):
    """
    Invoke the webhook with file uploads.
    Files are sent to n8n as base64-encoded data in the payload.
    """
    model = Models.get_model_by_id(model_id)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    webhook_config = model.meta.webhook if model.meta and model.meta.webhook else None
    
    if not webhook_config or not webhook_config.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook is not enabled for this model"
        )
    
    if not webhook_config.webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL is not configured for this model"
        )
    
    # Parse form data JSON
    try:
        form_data = json.loads(form_data_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid form data JSON"
        )
    
    # Process uploaded files
    file_attachments = []
    for file in files:
        try:
            content = await file.read()
            file_attachments.append({
                "name": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "data": base64.b64encode(content).decode('utf-8')
            })
        except Exception as e:
            log.error(f"Error reading file {file.filename}: {e}")
    
    # Prepare the payload for the webhook
    payload = {
        "user_id": user.id,
        "user_email": user.email,
        "user_name": user.name,
        "model_id": model_id,
        "chat_id": chat_id,
        "form_data": form_data,
        "files": file_attachments
    }
    
    log.info(f"Invoking webhook with files for model {model_id} by user {user.email}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                webhook_config.webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Obsidian-User-Id": user.id,
                    "X-Obsidian-Model-Id": model_id,
                }
            )
            
            try:
                response_data = response.json()
            except Exception:
                response_data = {"raw_response": response.text}
            
            if response.status_code >= 400:
                return JSONResponse(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    content={
                        "success": False,
                        "message": f"Webhook returned error: {response.status_code}",
                        "data": response_data
                    }
                )
            
            # Handle response (same logic as invoke_webhook)
            file_url = None
            file_name = None
            message = None
            
            if isinstance(response_data, dict):
                file_url = (
                    response_data.get("file_url") or
                    response_data.get("fileUrl") or
                    response_data.get("download_url") or
                    response_data.get("downloadUrl") or
                    response_data.get("url")
                )
                file_name = (
                    response_data.get("file_name") or
                    response_data.get("fileName") or
                    response_data.get("filename") or
                    response_data.get("name")
                )
                message = (
                    response_data.get("message") or
                    response_data.get("text") or
                    response_data.get("response")
                )
            elif isinstance(response_data, list) and len(response_data) > 0:
                first_item = response_data[0]
                if isinstance(first_item, dict):
                    file_url = (
                        first_item.get("file_url") or
                        first_item.get("fileUrl") or
                        first_item.get("download_url") or
                        first_item.get("downloadUrl") or
                        first_item.get("url")
                    )
                    file_name = (
                        first_item.get("file_name") or
                        first_item.get("fileName") or
                        first_item.get("filename") or
                        first_item.get("name")
                    )
                    message = (
                        first_item.get("message") or
                        first_item.get("text") or
                        first_item.get("response")
                    )
            
            return {
                "success": True,
                "message": message or "Workflow executed successfully",
                "data": response_data,
                "file_url": file_url,
                "file_name": file_name
            }
            
    except httpx.TimeoutException:
        log.error(f"Webhook timeout for model {model_id}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Webhook request timed out"
        )
    except httpx.RequestError as e:
        log.error(f"Webhook request error for model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to webhook: {str(e)}"
        )
    except Exception as e:
        log.error(f"Unexpected error invoking webhook with files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/models")
async def get_webhook_enabled_models(
    request: Request,
    user=Depends(get_verified_user)
):
    """
    Get all models that have webhook integration enabled.
    Returns a list of model IDs and their slash commands.
    """
    all_models = Models.get_all_models()
    
    webhook_models = []
    for model in all_models:
        if model.meta and model.meta.webhook and model.meta.webhook.enabled:
            webhook_models.append({
                "id": model.id,
                "name": model.name,
                "slash_command": model.meta.webhook.slash_command,
                "form_title": model.meta.webhook.form_title
            })
    
    return webhook_models

