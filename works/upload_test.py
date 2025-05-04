import os
import boto3
from django.conf import settings

def create_and_upload_file(bucket_name, s3_key, file_content,
                           aws_access_key_id, aws_secret_access_key, aws_region):
    """
    Creates a regular file in the current directory with the provided file_content
    and uploads it to the specified S3 bucket using boto3.
    
    After uploading, the file is removed from the local disk.
    
    Parameters:
      - bucket_name (str): The name of the S3 bucket.
      - s3_key (str): The key (including any folder path) where the file will be stored in the bucket.
      - file_content (str): The content to write into the file.
      - aws_access_key_id (str): Your AWS Access Key ID.
      - aws_secret_access_key (str): Your AWS Secret Access Key.
      - aws_region (str): The AWS region (e.g., 'us-east-2').
      
    Returns:
      None
    """
    # Define a filename for the regular file
    file_path = "upload_test_file.txt"
    
    # Create and write the file content to disk
    with open(file_path, "w") as f:
        f.write(file_content)
    
    # Create an S3 client with the provided credentials and region
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    
    try:
        # Upload the file from the local file system to S3
        s3.upload_file(file_path, bucket_name, s3_key)
        print(f"Successfully uploaded {file_path} to s3://{bucket_name}/{s3_key}")
    except Exception as e:
        print(f"Error uploading file: {e}")
    finally:
        # Remove the local file after upload
        if os.path.exists(file_path):
            os.remove(file_path)

# Example usage (run this from the Django shell):
if __name__ == "__main__":
    bucket = "wyzbucket-works"
    # The S3 key (path) where the file will be stored in the bucket
    key = "test_upload/test.txt"  
    content = "Hello, S3! This is a test file."
    aws_access_key = settings.AWS_ACCESS_KEY_ID
    aws_secret = settings.AWS_SECRET_ACCESS_KEY
    region = settings.AWS_S3_REGION_NAME
    
    create_and_upload_file(bucket, key, content, aws_access_key, aws_secret, region)
