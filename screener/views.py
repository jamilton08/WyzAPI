# views.py
import os
import uuid
import json
import boto3
import base64
import tempfile
import subprocess
from io import BytesIO
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from .models import VideoUpload, Step
import logging



logger = logging.getLogger(__name__)

# Import your login detection utility.
from .utilities.web_limits import require_login

@csrf_exempt
def upload_video(request):
    """
    Expects a POST request with:
      - 'video': the video file (multipart/form-data)
      - Optionally, 'type': either "M" or "N" (defaults to "M")
      - Optionally, 'url': the URL of the source page that should be scanned for login restrictions.
    The view uploads the file to the S3 bucket, creates a VideoUpload record,
    and returns the unique_link and video URL in JSON.
    """
    if request.method == 'POST':
        video_file = request.FILES.get('video')
        if not video_file:
            return JsonResponse({'error': 'No video file provided'}, status=400)
        
        # Use the provided type or default to "M"
        user_type = request.POST.get('type', 'M')

        # Get the source URL from the request (if provided).
        source_url = request.POST.get('url', '').strip()
        login_required_value = False

        # If a source URL is provided, use the require_login utility to check it.
        if source_url:
            try:
                detection_result = require_login(source_url)
                login_required_value = detection_result.get('login_required', False)
            except Exception as e:
                logger.error(f"Error processing login detection for URL {source_url}: {e}")
                # Proceed with default value (False) in case of error.

        try:
            # Generate a unique filename for S3.
            unique_filename = f"{uuid.uuid4().hex}.webm"
            s3_key = os.path.join("video_uploads", unique_filename)
            
            # Set up the boto3 S3 client using your AWS credentials.
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            
            # Upload the file object to S3.
            s3.upload_fileobj(
                video_file,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs={'ContentType': video_file.content_type}
            )
            
            # Construct the public URL for the uploaded video.
            video_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            
            # Create and save the VideoUpload model record, including the source URL and login_required flag.
            video_upload = VideoUpload.objects.create(
                user_type=user_type,  # Defaults to "M" if not provided.
                file_path=video_url,
                url=source_url,
                login_required=login_required_value
            )
            video_upload.save()
            
            logger.info(f"Video uploaded successfully: {video_url}")
            return JsonResponse({'unique_link': video_upload.unique_link, 'video_url': video_url})
        
        except Exception as e:
            logger.error(f"Error uploading video: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)



logger = logging.getLogger(__name__)


def upload_image_to_s3(image_data, s3_client, bucket_name, prefix):
    """
    Decodes a base64-encoded data URL (if provided) and uploads the image to S3.
    Returns the S3 public URL if successful, or None otherwise.
    """
    if image_data and image_data.startswith("data:"):
        try:
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            # Determine file extension from header.
            if "image/png" in header:
                ext = "png"
            elif "image/jpeg" in header:
                ext = "jpg"
            else:
                ext = "png"  # default to PNG if unknown

            filename = f"{uuid.uuid4().hex}.{ext}"
            s3_key = os.path.join(prefix, filename)
            file_obj = BytesIO(image_bytes)
            s3_client.upload_fileobj(
                file_obj,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs={'ContentType': f"image/{ext}"}
            )
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            return s3_url
        except Exception as e:
            logger.error(f"Error uploading image: {e}", exc_info=True)
            return None
    return None


@csrf_exempt
def trim_single_step(request, unique_link):
    """
    Expects a POST request with a JSON body containing a single step object:
      - title (string)
      - description (string, optional)
      - startTime (timestamp in ms)
      - endTime (timestamp in ms)
      - thumbStart (data URL, e.g. "data:image/png;base64,...")
      - thumbEnd (data URL, e.g. "data:image/png;base64,...")
      - events (JSON object or array, optional)
      - order (integer)
    
    Workflow:
      1. Retrieve VideoUpload by its unique link.
      2. Download the original video from S3.
      3. Trim the video using FFmpeg based on startTime and endTime.
      4. Upload the trimmed video back to S3.
      5. Upload the thumbStart and thumbEnd images to S3.
      6. Create a Step instance with URLs for the trimmed video and thumbnails.
      7. Associate the step with the VideoUpload.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        video_upload = VideoUpload.objects.get(unique_link=unique_link)
    except VideoUpload.DoesNotExist:
        return JsonResponse({'error': 'Video not found'}, status=404)

    try:
        step_data = json.loads(request.body)
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}", exc_info=True)
        return JsonResponse({'error': 'Invalid JSON provided.'}, status=400)

    if not step_data:
        return JsonResponse({'error': 'No step data provided.'}, status=400)

    # Set up the S3 client.
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    # Download the original video from S3 to a temporary file.
    try:
        # Extract the S3 key from the stored file_path.
        s3_key = video_upload.file_path.split('.com/')[-1]
        temp_dir = tempfile.gettempdir()
        local_video_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}.webm")
        s3.download_file(bucket_name, s3_key, local_video_path)
    except Exception as e:
        logger.error(f"Error downloading video for trimming: {e}", exc_info=True)
        return JsonResponse({'error': f'Error downloading video: {str(e)}'}, status=500)

    try:
        # Extract step parameters.
        title = step_data.get('title', '')
        description = step_data.get('description', '')
        start_time = int(step_data.get('startTime', 0))
        end_time = int(step_data.get('endTime', 0))
        thumb_start_data = step_data.get('thumbStart', '')
        thumb_end_data = step_data.get('thumbEnd', '')
        events = step_data.get('events', None)
        order = step_data.get('order', 0)

        adjusted_start_ms = max(start_time - 1000, 0)
        adjusted_end_ms   = end_time + 1000

        # Convert to seconds for ffmpeg:
        start_sec = adjusted_start_ms / 1000.0
        duration  = (adjusted_end_ms - adjusted_start_ms) / 1000.0
        # ────────────────────────────────────────────────────────────────────────

        # Now build your ffmpeg command exactly as before, using start_sec & duration:


        # Prepare a local file path for the trimmed video.
        trimmed_filename = f"{uuid.uuid4().hex}.webm"
        local_trimmed_path = os.path.join(temp_dir, trimmed_filename)

        # Invoke FFmpeg to trim the video clip.
        command = [
            'ffmpeg', '-y',
            '-ss', str(start_sec),
            '-t',  str(duration),
            '-i',  local_video_path,
            '-c:v', 'libvpx-vp9',
            '-b:v', '1M',
            '-c:a', 'libopus',
            local_trimmed_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Upload the trimmed video to S3.
        s3_trimmed_key = os.path.join("video_uploads/trimmed", trimmed_filename)
        with open(local_trimmed_path, 'rb') as trimmed_file:
            s3.upload_fileobj(
                trimmed_file,
                Bucket=bucket_name,
                Key=s3_trimmed_key,
                ExtraArgs={'ContentType': 'video/webm'}
            )
        trimmed_video_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_trimmed_key}"

        # Process thumbnail images.
        thumb_prefix = "video_uploads/thumbs"
        thumb_start_url = upload_image_to_s3(thumb_start_data, s3, bucket_name, os.path.join(thumb_prefix, "start"))
        thumb_end_url = upload_image_to_s3(thumb_end_data, s3, bucket_name, os.path.join(thumb_prefix, "end"))

        # Create the Step instance with the processed URLs.
        step_instance = Step.objects.create(
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            thumb_start=thumb_start_url if thumb_start_url else thumb_start_data,
            thumb_end=thumb_end_url if thumb_end_url else thumb_end_data,
            events=events,
            order=order,
            trimmed_video=trimmed_video_url
        )
        # Associate the step with the VideoUpload.
        video_upload.steps.add(step_instance)

        # Clean up temporary files.
        if os.path.exists(local_trimmed_path):
            os.remove(local_trimmed_path)
        if os.path.exists(local_video_path):
            os.remove(local_video_path)

        return JsonResponse({
            'message': 'Video trimmed and step created successfully',
            'step': {
                'id': step_instance.id,
                'trimmed_video_url': trimmed_video_url,
                'thumb_start_url': thumb_start_url,
                'thumb_end_url': thumb_end_url,
            }
        })

    except Exception as e:
        logger.error(f"Error processing step: {e}", exc_info=True)
        if os.path.exists(local_video_path):
            os.remove(local_video_path)
        return JsonResponse({'error': f'Error processing step: {str(e)}'}, status=500)



@require_GET
def get_steps(request, unique_link):
    """
    Return a JSON response with details of the VideoUpload and all its associated steps.
    Each step contains details such as title, description, start and end times, thumbnails, 
    events, order, and the trimmed video URL. The response also includes the website URL 
    stored in the VideoUpload instance.
    """
    try:
        video_upload = VideoUpload.objects.get(unique_link=unique_link)
    except VideoUpload.DoesNotExist:
        return JsonResponse({'error': 'VideoUpload not found'}, status=404)

    # Retrieve all related steps and order them.
    steps_qs = video_upload.steps.all().order_by('order')
    steps_list = []
    for step in steps_qs:
        steps_list.append({
            'id': step.id,
            'title': step.title,
            'description': step.description,
            'start_time': step.start_time,
            'end_time': step.end_time,
            'thumb_start': step.thumb_start,
            'thumb_end': step.thumb_end,
            'events': step.events,    # JSONField; assumed serializable.
            'order': step.order,
            'trimmed_video': step.trimmed_video,
        })

    # Include the website link (VideoUpload.url) along with the steps.
    response_data = {
        'video_upload_url': video_upload.url,
        'steps': steps_list
    }
    return JsonResponse(response_data)
