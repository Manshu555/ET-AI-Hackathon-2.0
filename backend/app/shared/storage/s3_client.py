import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class S3Client:
    """Lazy-initialized S3/MinIO client. Won't crash the server if MinIO is down."""
    
    def __init__(self):
        self._client = None
        self.bucket = settings.S3_BUCKET
        self._available = False

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name='us-east-1'
            )
            self._ensure_bucket()
        return self._client

    def _ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
            self._available = True
        except Exception:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                self._available = True
                logger.info(f"Created bucket {self.bucket}")
            except Exception as e:
                self._available = False
                logger.warning(f"MinIO unavailable — storage features disabled: {e}")

    def upload_file(self, file_obj, object_name: str) -> str:
        """Upload a file-like object to S3 and return the object path."""
        try:
            self.client.upload_fileobj(file_obj, self.bucket, object_name)
            return object_name
        except ClientError as e:
            logger.error(f"Error uploading file: {e}")
            raise

    def get_presigned_url(self, object_name: str, expiration=3600) -> str:
        """Generate a presigned URL for downloading an object."""
        try:
            response = self.client.generate_presigned_url('get_object',
                                                        Params={'Bucket': self.bucket,
                                                                'Key': object_name},
                                                        ExpiresIn=expiration)
            return response
        except ClientError as e:
            logger.error(e)
            return None
            
    def get_file_content(self, object_name: str) -> bytes:
        """Download file content into memory."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_name)
            return response['Body'].read()
        except ClientError as e:
            logger.error(e)
            raise

# Lazy singleton — no network call at import time
s3_client = S3Client()
