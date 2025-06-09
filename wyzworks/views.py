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

def clone_s3_prefix(s3_client, bucket: str, source_prefix: str, dest_prefix: str):
    """
    Recursively copy all objects from source_prefix to dest_prefix
    within the same bucket.

    :param s3_client: a boto3 client for S3
    :param bucket:     the S3 bucket name
    :param source_prefix: e.g. "folder123/"
    :param dest_prefix:   e.g. "folder123/<submission_id>/"
    """
    paginator = s3_client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=source_prefix)

    copied = 0
    for page in page_iterator:
        for obj in page.get("Contents", []):
            src_key = obj["Key"]
            # compute the "suffix" under source_prefix
            suffix = src_key[len(source_prefix):]
            dest_key = f"{dest_prefix}{suffix}"

            copy_source = {"Bucket": bucket, "Key": src_key}
            try:
                s3_client.copy_object(
                    Bucket=bucket,
                    CopySource=copy_source,
                    Key=dest_key,
                    MetadataDirective="COPY"  # preserve metadata
                )
                copied += 1
            except Exception as e:
                logger.error(
                    f"Failed to copy {src_key} → {dest_key}: {e}",
                    exc_info=True
                )

    if copied == 0:
        logger.warning(f"No objects found under prefix {source_prefix}")
    else:
        logger.info(f"Cloned {copied} objects from {source_prefix} to {dest_prefix}")


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
        file_path       = ""  # placeholder; filled after upload
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
        folder_name = sub_prefix.rstrip("/").split("/")[-1]
        folder_children = build_s3_tree(bucket, sub_prefix, s3_client)
        children.append({
            "name": folder_name,
            "type": "folder",
            "children": folder_children
        })

    return children

@csrf_exempt
def retrieve_or_submit_folder(request, link):
    print(f"Received link: {link}")
    """
    If link matches unique_link (manager mode), return folder + all its submissions.
    If link matches work_link (student mode), then:
      • If folder.assignment_mode allows LINK, create a new Submission in link mode:
          - clone S3 prefix under submission.exchange_uuid
          - return folder metadata, new exchange_uuid, new file_path, and structure
      • Else if allows DEVICE, extract X-Device-Id header, get/create Device, create Submission:
          - clone S3 prefix under submission.exchange_uuid (or device.id)
          - return folder metadata, device id, file_path, and structure
    """
    # 1) find folder and determine access type
    try:
        folder = FolderUpload.objects.get(unique_link=link)
        access = "manager"
    except FolderUpload.DoesNotExist:
        try:
            folder = FolderUpload.objects.get(work_link=link)
            access = "student"
        except FolderUpload.DoesNotExist:
            raise Http404("Folder not found")

    # set up S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id     = settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        region_name           = settings.AWS_S3_REGION_NAME,
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    original_prefix = folder.file_path.rstrip("/") + "/"
    print(f"Original S3 prefix: {original_prefix}")
    if access == "manager":
        # return the tree + list of submissions
        children = build_s3_tree(bucket, original_prefix, s3)
        structure = {
            "name": folder.folder_name,
            "type": "folder",
            "children": children,
        }
        submissions = []
        for sub in folder.submissions.all():
            submissions.append({
                "id": str(sub.id),
                "mode": sub.submission_mode,
                "device": str(sub.device.id) if sub.device else None,
                "exchange_uuid": str(sub.exchange_uuid) if sub.exchange_uuid else None,
                "file_path": sub.file_path,
                "created_at": sub.created_at.isoformat(),
            })
        return JsonResponse({
            "folder_name": folder.folder_name,
            "unique_link": folder.unique_link,
            "structure": structure,
            "submissions": submissions,
        })

    # STUDENT access: create or retrieve a Submission, clone S3, and return its view
    mode = folder.assignment_mode
    if mode in (FolderUpload.ASSIGNMENT_LINK, FolderUpload.ASSIGNMENT_BOTH):
        # LINK-mode submission
        sub = Submission.objects.create(
            folder=folder,
            submission_mode=Submission.MODE_LINK,
            exchange_uuid=uuid.uuid4(),
            file_path=""  # we'll set it below
        )
        new_prefix = f"{folder.file_path.rstrip('/')}/{sub.exchange_uuid}/"
    elif mode in (FolderUpload.ASSIGNMENT_DEVICE, FolderUpload.ASSIGNMENT_BOTH):
        # DEVICE-mode submission
        device_id = request.headers.get("X-Device-Id")
        if not device_id:
            return JsonResponse({"error": "Missing X-Device-Id header"}, status=400)
        device, _ = Device.objects.get_or_create(id=device_id)
        sub = Submission.objects.create(
            folder=folder,
            submission_mode=Submission.MODE_DEVICE,
            device=device,
            file_path=""  # set below
        )
        new_prefix = f"{folder.file_path.rstrip('/')}/{device.id}/"
    else:
        return JsonResponse({
            "error": f"Assignment not allowed via {mode} mode"
        }, status=400)

    # clone original folder tree into the submission-specific prefix
    try:
        clone_s3_prefix(s3, bucket, original_prefix, new_prefix)
    except Exception as e:
        logger.exception("Error cloning S3 prefix")
        return JsonResponse({"error": str(e)}, status=500)

    # update submission.file_path and save
    sub.file_path = new_prefix
    sub.save()

    # build tree from the new prefix
    children = build_s3_tree(bucket, new_prefix, s3)
    structure = {
        "name": folder.folder_name,
        "type": "folder",
        "children": children,
    }

    # return folder metadata + submission info
    response = {
        "folder_name": folder.folder_name,
        "file_path":   sub.file_path,
        "structure":   structure,
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
