import os
import boto3
from django.conf import settings
    
def upload_folder_to_s3(folder_path, bucket_name, s3_path=''):
        us3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
    
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, folder_path)
                s3_key = os.path.join(s3_path, relative_path)
    
                s3.upload_file(local_path, bucket_name, s3_key)
                print(f"Uploaded {local_path} to s3://{bucket_name}/{s3_key}")