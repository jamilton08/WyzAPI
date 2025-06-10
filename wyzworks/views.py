import os
import json
import logging

import uuid

import base64
import boto3
from django.conf import settings
from .models import FolderUpload, Submission, Device
from django.http import JsonResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import re
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


logger = logging.getLogger(__name__)


def upload_nested_files(s3_client, bucket_name, s3_folder_base, structure, base_path=""):
    """
    Recursively uploads files from the nested file structure to S3.
    Supports regular text files (type: "file") and images (type: "img").
    """
    if structure['type'] == 'file':
        relative_path = os.path.join(base_path, structure['name'])
        file_content = structure.get('content', '')
        s3_key = os.path.join(s3_folder_base, relative_path)
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType='text/plain'
            )
            logger.info(f"Uploaded file to s3://{bucket_name}/{s3_key}")
        except Exception as e:
            logger.error(f"Error uploading file {s3_key}: {e}", exc_info=True)
    elif structure['type'] == 'img':
        relative_path = os.path.join(base_path, structure['name'])
        s3_key = os.path.join(s3_folder_base, relative_path)
        try:
            content = structure.get('content', '')
            # If the content is a data URI, remove the prefix.
            if content.startswith("data:"):
                base64_data = content.split(',')[1]
            else:
                base64_data = content
            file_bytes = base64.b64decode(base64_data)
            # Use provided mime_type or default to 'image/png'
            content_type = structure.get('mime_type', 'image/png')
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type
            )
            logger.info(f"Uploaded image to s3://{bucket_name}/{s3_key}")
        except Exception as e:
            logger.error(f"Error uploading image {s3_key}: {e}", exc_info=True)
    elif structure['type'] == 'folder':
        new_base = os.path.join(base_path, structure['name']) if base_path else structure['name']
        for child in structure.get('children', []):
            upload_nested_files(s3_client, bucket_name, s3_folder_base, child, new_base)


import logging

logger = logging.getLogger(__name__)

def clone_s3_prefix(
    s3_client,
    bucket: str,
    source_prefix: str,
    dest_prefix: str,
    exclude_prefixes: list[str] = None    # ← add this parameter
):
    """
    Recursively copy all objects from source_prefix to dest_prefix,
    skipping any keys under the given exclude_prefixes.
    """
    exclude_prefixes = exclude_prefixes or []  # ← ensure it’s a list

    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=source_prefix):
        for obj in page.get("Contents", []):
            src_key = obj["Key"]

            # ← Skip keys that start with any excluded prefix
            if any(src_key.startswith(exc) for exc in exclude_prefixes):
                continue

            suffix   = src_key[len(source_prefix):]
            dest_key = f"{dest_prefix}{suffix}"
            copy_source = {"Bucket": bucket, "Key": src_key}

            try:
                s3_client.copy_object(
                    Bucket=bucket,
                    CopySource=copy_source,
                    Key=dest_key,
                    MetadataDirective="COPY"
                )
            except Exception as e:
                logger.error(f"Failed to copy {src_key} → {dest_key}: {e}", exc_info=True)


logger = logging.getLogger(__name__)

@csrf_exempt
def upload_folder_s3(request):
    """
    Expects JSON POST body:
      {
        "folder_name": "...",
        "file_structure": { ... },   # your nested dict
        "rubric": { ... },           # optional JSON rubric
        "assignment_mode": "device"  # optional: "device", "link", or "both"
      }

    Creates FolderUpload (with unique_link, work_link, rubric, assignment_mode),
    uploads each child into S3 under unique_link/,
    and returns both slugs.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    # parse JSON
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        logger.exception("Invalid JSON payload")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    folder_name     = payload.get("folder_name")
    file_structure  = payload.get("file_structure")
    rubric          = payload.get("rubric")
    mode            = payload.get(
        "assignment_mode",
        FolderUpload.ASSIGNMENT_LINK
    )
    editor_states   = payload.get("editor_states") 
    dragX           = payload.get("dragX")
    dragY           = payload.get("dragY")
    prevX           = payload.get("prevX")
    prevY           = payload.get("prevY")
    prevW           = payload.get("prevW")
    prevH           = payload.get("prevH")


    # Validate required fields
    if not folder_name or not file_structure:
        return JsonResponse(
            {"error": "Both folder_name and file_structure are required"},
            status=400
        )

    # Validate mode
    valid_modes = {
        FolderUpload.ASSIGNMENT_DEVICE,
        FolderUpload.ASSIGNMENT_LINK,
        FolderUpload.ASSIGNMENT_BOTH
    }
    if mode not in valid_modes:
        return JsonResponse(
            {"error": f"Invalid assignment_mode. Must be one of {valid_modes}."},
            status=400
        )

    # 1) Create the DB record
    folder = FolderUpload.objects.create(
        folder_name     = folder_name,
        rubric          = rubric,
        assignment_mode = mode,
        file_path       = "" , # placeholder; filled after upload
        editor_states   = editor_states,
        drag_x          = dragX,
        drag_y          = dragY,
        prev_x          = prevX,
        prev_y          = prevY,
        prev_w          = prevW,
        prev_h          = prevH,
    )

    manager_prefix = folder.unique_link
    logger.info(f"S3 manager prefix: {manager_prefix}")

    # 2) Upload nested files under s3://bucket/<manager_prefix>/...
    s3 = boto3.client(
        "s3",
        aws_access_key_id    = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key= settings.AWS_SECRET_ACCESS_KEY,
        region_name          = settings.AWS_S3_REGION_NAME,
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME

    for child in file_structure.get("children", []):
        upload_nested_files(s3, bucket, manager_prefix, child, "")

    # 3) Update file_path & save
    folder.file_path = manager_prefix
    folder.save()

    # 4) Return both slugs (and echo the mode)
    return JsonResponse({
        "unique_link":     folder.unique_link,
        "work_link":       folder.work_link,
        "assignment_mode": folder.assignment_mode,
    }, status=201)



def build_s3_tree(bucket, prefix, s3_client):
    """
    Recursively build a nested folder structure from S3.
    For each file, retrieve its content.
      - If the file is an image, convert it to a Base64 data URL.
      - Otherwise, decode as text.
    Returns a list of children in the format:
      - For files: { "name": filename, "type": "file", "content": file_content }
      - For folders: { "name": folder_name, "type": "folder", "children": [...] }
    """
    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Prefix=prefix,
        Delimiter="/"
    )
    
    children = []

    # Process files in this folder (skip the folder placeholder if present)
    for obj in response.get("Contents", []):
        if obj["Key"] == prefix:
            continue
        filename = obj["Key"].split("/")[-1]
        try:
            file_obj = s3_client.get_object(Bucket=bucket, Key=obj["Key"])
            raw_data = file_obj["Body"].read()
            
            # Check if file is an image by its extension
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                base64_data = base64.b64encode(raw_data).decode("utf-8")
                if filename.lower().endswith('.png'):
                    mime_type = "image/png"
                elif filename.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = "image/jpeg"
                elif filename.lower().endswith('.gif'):
                    mime_type = "image/gif"
                else:
                    mime_type = "application/octet-stream"
                content = f"data:{mime_type};base64,{base64_data}"
            else:
                # Try decoding as UTF-8; if fails, fallback to latin-1
                try:
                    content = raw_data.decode("utf-8")
                except UnicodeDecodeError:
                    content = raw_data.decode("latin-1")
        except Exception as e:
            content = f"Error retrieving content: {str(e)}"
        
        children.append({
            "name": filename,
            "type": "file",
            "content": content
        })

    # Process subfolders (CommonPrefixes)
    for common_prefix in response.get("CommonPrefixes", []):
        sub_prefix = common_prefix["Prefix"]
        folder_name = sub_prefix.rstrip("/").split("/" )[-1]
        folder_children = build_s3_tree(bucket, sub_prefix, s3_client)
        children.append({
            "name": folder_name,
            "type": "folder",
            "children": folder_children
        })

    return children

# views.py

@csrf_exempt
def retrieve_or_submit_folder(request, link):
    # find folder & access mode
    try:
        folder = FolderUpload.objects.get(unique_link=link)
        access = "manager"
    except FolderUpload.DoesNotExist:
        try:
            folder = FolderUpload.objects.get(work_link=link)
            access = "student"
        except FolderUpload.DoesNotExist:
            raise Http404("Folder not found")

    s3 = boto3.client(
        "s3",
        aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        region_name           = settings.AWS_S3_REGION_NAME,
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    original_prefix = folder.file_path.rstrip("/") + "/"

    if access == "manager":
        children = build_s3_tree(bucket, original_prefix, s3)
        structure = {"name": folder.folder_name, "type": "folder", "children": children}
        submissions = [
            {
                "id": str(sub.id),
                "mode": sub.submission_mode,
                "device": str(sub.device.id) if sub.device else None,
                "exchange_uuid": str(sub.exchange_uuid) if sub.exchange_uuid else None,
                "file_path": sub.file_path,
                "created_at": sub.created_at.isoformat(),
            }
            for sub in folder.submissions.all()
        ]
        return JsonResponse({
            "folder_name": folder.folder_name,
            "unique_link": folder.unique_link,
            "structure":   structure,
            "submissions": submissions,
            "editor_states": folder.editor_states,
            "dragX": folder.drag_x,
            "dragY": folder.drag_y,
            "prevX": folder.prev_x,
            "prevY": folder.prev_y,
            "prevW": folder.prev_w,
            "prevH": folder.prev_h,  
        })

    # build exclude list of prior submission prefixes
    existing_prefixes = []
    for sub in folder.submissions.all():
        if sub.submission_mode == Submission.MODE_LINK and sub.exchange_uuid:
            existing_prefixes.append(f"{original_prefix}{sub.exchange_uuid}/")
        elif sub.submission_mode == Submission.MODE_DEVICE and sub.device:
            existing_prefixes.append(f"{original_prefix}{sub.device.id}/")

    # student access: create submission
    mode = folder.assignment_mode
    if mode in (FolderUpload.ASSIGNMENT_LINK, FolderUpload.ASSIGNMENT_BOTH):
        sub = Submission.objects.create(
            folder=folder,
            submission_mode=Submission.MODE_LINK,
            exchange_uuid=uuid.uuid4(),
            file_path=""
        )
        new_prefix = f"{original_prefix}{sub.exchange_uuid}/"
    elif mode in (FolderUpload.ASSIGNMENT_DEVICE, FolderUpload.ASSIGNMENT_BOTH):
        device_id = request.headers.get("X-Device-Id")
        if not device_id:
            return JsonResponse({"error": "Missing X-Device-Id header"}, status=400)
        device, _ = Device.objects.get_or_create(id=device_id)
        sub = Submission.objects.create(
            folder=folder,
            submission_mode=Submission.MODE_DEVICE,
            device=device,
            file_path=""
        )
        new_prefix = f"{original_prefix}{device.id}/"
    else:
        return JsonResponse({"error": f"Assignment not allowed via {mode} mode"}, status=400)

    # clone only original files, skipping previous sub-folders
    try:
        clone_s3_prefix(
            s3_client       = s3,
            bucket          = bucket,
            source_prefix   = original_prefix,
            dest_prefix     = new_prefix,
            exclude_prefixes= existing_prefixes
        )
    except Exception as e:
        logger.exception("Error cloning S3 prefix")
        return JsonResponse({"error": str(e)}, status=500)

    sub.file_path = new_prefix
    sub.save()

    children = build_s3_tree(bucket, new_prefix, s3)
    structure = {"name": folder.folder_name, "type": "folder", "children": children}

    response = {
        "folder_name": folder.folder_name,
        "file_path":   sub.file_path,
        "structure":   structure,
        "editor_states": folder.editor_states,
        "dragX": folder.drag_x,
        "dragY": folder.drag_y,
        "prevX": folder.prev_x,
        "prevY": folder.prev_y,
        "prevW": folder.prev_w,
        "prevH": folder.prev_h,   
    }
    if sub.submission_mode == Submission.MODE_LINK:
        response["exchange_uuid"] = str(sub.exchange_uuid)
    else:
        response["device_id"] = str(sub.device.id)

    return JsonResponse(response, status=200)


# views.py

def camel_to_snake(name):
    """Convert CamelCase or camelCase string to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def convert_keys_camel_to_snake(data):
    """Recursively convert dictionary keys from camelCase to snake_case."""
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            new_key = camel_to_snake(key)
            new_data[new_key] = convert_keys_camel_to_snake(value)
        return new_data
    elif isinstance(data, list):
        return [convert_keys_camel_to_snake(item) for item in data]
    return data


@csrf_exempt
def update_submission_name(request, exchange_uuid):
    """
    POST JSON:
      {
        "first_name": "...",
        "last_name": "..."
      }
    Finds the Submission with that exchange_uuid, updates the names,
    and returns the updated submission data.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in update_submission_name")
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    first_name = payload.get("first_name", "").strip()
    last_name  = payload.get("last_name", "").strip()
    if not first_name or not last_name:
        return JsonResponse(
            {"error": "Both first_name and last_name are required."},
            status=400
        )

    try:
        sub = Submission.objects.get(exchange_uuid=exchange_uuid)
    except Submission.DoesNotExist:
        raise Http404("Submission not found")

    sub.first_name = first_name
    sub.last_name  = last_name
    # optional: run full_clean() to re-validate
    try:
        sub.full_clean()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    sub.save()

    return JsonResponse({
        "submission_id": str(sub.id),
        "exchange_uuid": str(sub.exchange_uuid),
        "first_name":    sub.first_name,
        "last_name":     sub.last_name,
        "file_path":     sub.file_path,
    })
"""
@method_decorator(csrf_exempt, name='dispatch')
class SaveEditorStateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data

        # Get the folder identifier from the payload.
        folder_id = data.get("folder_id")
        if not folder_id:
            return Response(
                {"error": "folder_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Assuming folder_id corresponds to FolderUpload.unique_link.
            folder_upload = FolderUpload.objects.get(unique_link=folder_id)
        except FolderUpload.DoesNotExist:
            return Response(
                {"error": "Folder not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Extract and convert the global CodeEditor state.
        code_editor_data = data.get("codeEditor")
        if code_editor_data is None:
            return Response(
                {"error": "codeEditor data is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        code_editor_data = convert_keys_camel_to_snake(code_editor_data)

        # Update or create the global CodeEditorState record.
        code_editor_state, created = CodeEditorState.objects.update_or_create(
            folder_upload=folder_upload,
            defaults=code_editor_data
        )

        # Process the list of CodeEntry states.
        code_entries_data = data.get("codeEntries", [])
        # Remove any existing CodeEntryState records.
        code_editor_state.code_entries.all().delete()

        for entry in code_entries_data:
            # Convert keys from camelCase to snake_case.
            entry = convert_keys_camel_to_snake(entry)
            CodeEntryState.objects.create(
                code_editor_state=code_editor_state,
                **entry
            )

        return Response(
            {"status": "success", "created": created},
            status=status.HTTP_200_OK
        )


class RetrieveEditorStateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        folder_id = kwargs.get("folder_id")
        if not folder_id:
            return Response(
                {"error": "folder_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            folder_upload = FolderUpload.objects.get(unique_link=folder_id)
        except FolderUpload.DoesNotExist:
            return Response(
                {"error": "Folder not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            editor_state = folder_upload.code_editor_state
        except CodeEditorState.DoesNotExist:
            return Response(
                {"error": "Editor state not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Build a response payload (using camelCase keys if desired)
        code_editor_data = {
            "tabsOrientation": editor_state.tabs_orientation,
            "openMenu": editor_state.open_menu,
            "language": editor_state.language,
            "previewModal": editor_state.preview_modal,
            "selectedEditor": editor_state.selected_editor,
            "selectedItem": editor_state.selected_item,
            "activeComponent": editor_state.active_component,
            "zIndices": editor_state.z_indices,
        }
        
        # Build list of code entries from the related code_entries
        code_entries_data = []
        for entry in editor_state.code_entries.all().order_by("editor_id"):
            code_entries_data.append({
                "editorId": entry.editor_id,
                "language": entry.language,
                "code": entry.code,
                "pathTo": entry.path_to,
                "showLines": entry.show_lines,
                "selectedLanguage": entry.selected_language,
                "size": entry.size,
                "fontSize": entry.font_size,
                "tabState": entry.tab_state,
                "scrollTop": entry.scroll_top,
                "position": entry.position,
                "activeHandle": entry.active_handle,
            })
        
        payload = {
            "folder_id": folder_id,
            "codeEditor": code_editor_data,
            "codeEntries": code_entries_data,
        }
        
        return Response(payload, status=status.HTTP_200_OK)
"""
