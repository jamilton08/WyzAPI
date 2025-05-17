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
from django.forms.models import model_to_dict
from sendgrid  import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.views.decorators.http import require_http_methods




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
        

        # Get the source URL from the request (if provided).
        source_url = request.POST.get('url', '').strip()
        login_required_value = False

        recordings_json = request.POST.get('recordings', '[]')
        try:
            recordings_list = json.loads(recordings_json)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid recordings JSON'}, status=400)

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
                file_path=video_url,
                url=source_url,
                login_required=login_required_value,
                recordings   = recordings_list,
            )
            video_upload.save()
            
            logger.info(f"Video uploaded successfully: {video_url}")
            return JsonResponse({'unique_link': video_upload.unique_link, 'video_url': video_url, 'shareable_link': video_upload.shareable_link}, status=201)
        
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

        incoming_recs = step_data.get('recordings')
        if isinstance(incoming_recs, list):
            video_upload.recordings = incoming_recs
            video_upload.save(update_fields=['recordings'])

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
def get_steps(request, link):
    """
    GET /screener/get_steps/<link>/
    - If link matches VideoUpload.unique_link → access_type 'm'
      include full model under 'video_upload'.
    - Else if link matches VideoUpload.shareable_link → access_type 'u'
      return only video_upload_url + steps.
    - Otherwise 404.
    """
    # 1) Lookup by unique_link first (manager access)
    try:
        video_upload = VideoUpload.objects.get(unique_link=link)
        access_type  = 'm'
    except VideoUpload.DoesNotExist:
        # 2) Fallback to shareable_link (user access)
        try:
            video_upload = VideoUpload.objects.get(shareable_link=link)
            access_type  = 'u'
        except VideoUpload.DoesNotExist:
            return JsonResponse({'error': 'VideoUpload not found'}, status=404)

    # 3) Build steps payload
    steps_list = [
        {
            'id':            s.id,
            'title':         s.title,
            'description':   s.description,
            'start_time':    s.start_time,
            'end_time':      s.end_time,
            'thumb_start':   s.thumb_start,
            'thumb_end':     s.thumb_end,
            'events':        s.events,
            'order':         s.order,
            'trimmed_video': s.trimmed_video,
        }
        for s in video_upload.steps.all().order_by('order')
    ]

    # 4) Base response
    response_data = {
        'access_type':       access_type,
        'video_upload_url':  video_upload.url,
        'steps':             steps_list,
        'recordings':       video_upload.recordings
    }

    # 5) If manager access, include full model
    if access_type == 'm':
        response_data['video_upload'] = model_to_dict(
            video_upload,
            fields=[ 
                'id',
                'url',
                'unique_link',
                'shareable_link',
                'upload_date',
                # any other fields you want
            ]
        )

    return JsonResponse(response_data)





@csrf_exempt
@require_http_methods(["DELETE"])
def delete_step(request, unique_link, step_id):
    """
    DELETE /screener/step/<unique_link>/<step_id>/
    Body (JSON): { "recordings": [ ... ] }
    """
    # 1) Lookup your VideoUpload by unique_link
    try:
        video_upload = VideoUpload.objects.get(unique_link=unique_link)
    except VideoUpload.DoesNotExist:
        return JsonResponse({'error': 'VideoUpload not found.'}, status=404)

    # 2) Parse the incoming JSON
    try:
        payload    = json.loads(request.body)
        recs       = payload.get('recordings', [])
    except ValueError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    # 3) Delete the Step
    try:
        step = Step.objects.get(pk=step_id)
        step.delete()
    except Step.DoesNotExist:
        # we’ll still update recordings even if the step was already gone
        pass

    # 4) Persist the updated recordings array
    video_upload.recordings = recs
    video_upload.save(update_fields=['recordings'])

    return JsonResponse({'message': 'Step deleted and recordings updated.'})




@csrf_exempt
def email_share(request):
    """
    POST /screener/email-share/

    Expects JSON: { email, unique_link, shareable_link }
    Sends an email via SendGrid dynamic template.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data  = json.loads(request.body)
        email = data['email']
        ulink = data['unique_link']
        slink = data['shareable_link']
    except (ValueError, KeyError):
        return JsonResponse({'error': 'email, unique_link and shareable_link are required.'}, status=400)

    # Build the SendGrid Mail object
    message = Mail(
        from_email = settings.SENDGRID_FROM_EMAIL,
        to_emails  = email,
    )
    message.template_id = settings.SENDGRID_TEMPLATE_ID
    # Pass dynamic template data for your template placeholders
    message.dynamic_template_data = {
        'manage_link': f"{settings.FRONTEND_URL}/manage/{ulink}",
        'share_link':  f"{settings.FRONTEND_URL}/share/{slink}"
    }

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        if 200 <= response.status_code < 300:
            return JsonResponse({'message': 'Email sent successfully.'})
        else:
            return JsonResponse({
                'error': 'SendGrid API error',
                'status_code': response.status_code,
                'body': response.body.decode()
            }, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



