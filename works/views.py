import os
import json
import logging
import base64
import boto3
from django.conf import settings
from .models import FolderUpload
from django.http import JsonResponse, Http404
from rest_framework.views import APIView

from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import re
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Form, CompletedField
from .serializers import FormInitSerializer, FormDetailSerializer
from rest_framework.decorators import api_view, permission_classes



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

@csrf_exempt
def upload_folder_s3(request):
    """
    Expects JSON POST body:
      {
        "folder_name": "...",
        "file_structure": { ... },   # your nested dict
        "rubric": { ... }            # optional JSON rubric
      }

    Creates FolderUpload (with both unique_link & work_link + rubric),
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

    folder_name    = payload.get("folder_name")
    file_structure = payload.get("file_structure")
    rubric         = payload.get("rubric")  # optional

    if not folder_name or not file_structure:
        return JsonResponse(
            {"error": "Both folder_name and file_structure are required"},
            status=400
        )

    # 1) Create the DB record (rubric will be NULL if not provided)
    folder = FolderUpload.objects.create(
        folder_name=folder_name,
        rubric=rubric,
        file_path=""   # placeholder; we'll fill this after upload
    )

    # now folder.unique_link and folder.work_link are both set
    manager_prefix = folder.unique_link
    logger.info(f"S3 manager prefix: {manager_prefix}")

    # 2) Upload nested files under s3://bucket/<manager_prefix>/...
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME

    for child in file_structure.get("children", []):
        upload_nested_files(s3, bucket, manager_prefix, child, "")

    # 3) Update the file_path and save
    folder.file_path = manager_prefix
    folder.save()

    # 4) Return both slugs
    return JsonResponse({
        "unique_link": folder.unique_link,  # manager URL slug
        "work_link":   folder.work_link,    # student URL slug
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
def retrieve_folder_from_s3(request, unique_link):
    """
    Retrieve the folder contents from S3 based on the FolderUpload record's file_path.
    Returns a nested JSON structure preserving the folder tree with file contents.
    For image files, the content is returned as a Base64-encoded data URL.
    """
    try:
        folder = FolderUpload.objects.get(unique_link=unique_link)
    except FolderUpload.DoesNotExist:
        raise Http404("Folder not found")

    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    # Ensure the prefix ends with a slash
    prefix = folder.file_path.rstrip("/") + "/"

    try:
        children = build_s3_tree(bucket_name, prefix, s3_client)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    # Wrap the children in a root node that reflects the folder record.
    structure = {
        "name": folder.folder_name,
        "type": "folder",
        "children": children,
    }

    data = {
        "folder_name": folder.folder_name,
        "unique_link": folder.unique_link,
        "structure": structure,
    }
    return JsonResponse(data)


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
    


def get_form_by_token(token, manage=False):
    lookup = {"manage_token": token} if manage else {"access_token": token}
    return Form.objects.filter(**lookup).first()

@csrf_exempt
@api_view(["POST"])
def init_form(request):
    """
    Called as soon as the user opens the form-builder.
    Always returns (id, manage_token, access_token).
    """
    form = Form.objects.create()
    return Response(FormInitSerializer(form).data, status=status.HTTP_201_CREATED)


@csrf_exempt
@api_view(["GET"])
def view_form(request):
    """
    Read‐only view, accepts either manage_token or access_token
    via “X-Form-Token” header.
    """
    token = request.headers.get("X-Form-Token")
    form = Form.objects.filter(
      models.Q(manage_token=token) | models.Q(access_token=token)
    ).first()
    if not form:
        return Response({"detail":"Invalid token"}, status=401)
    return Response(FormDetailSerializer(form).data)
