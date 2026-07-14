import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging
import os
import shutil

logger = logging.getLogger(__name__)

# Local uploads directory — used as fallback when MinIO is unavailable
_UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads")


class S3Client:
    """Lazy-initialized S3/MinIO client with local filesystem fallback."""
    
    def __init__(self):
        self._client = None
        self.bucket = settings.S3_BUCKET
        self._available = False
        self._checked = False

    @property
    def client(self):
        if self._client is None:
            from botocore.config import Config
            self._client = boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name='us-east-1',
                config=Config(connect_timeout=2, read_timeout=2, retries={'max_attempts': 0})
            )
            self._ensure_bucket()
        return self._client

    def _ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
            self._available = True
            self._checked = True
        except Exception:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                self._available = True
                self._checked = True
                logger.info(f"Created bucket {self.bucket}")
            except Exception as e:
                self._available = False
                self._checked = True
                logger.warning(f"MinIO unavailable -- falling back to local filesystem storage: {e}")
                os.makedirs(_UPLOADS_DIR, exist_ok=True)

    def _ensure_local_dir(self, object_name: str):
        """Create subdirectories under uploads/ to match the object_name path."""
        full_path = os.path.join(_UPLOADS_DIR, object_name)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

    def upload_file(self, file_obj, object_name: str) -> str:
        """Upload a file-like object. Uses S3 if available, else local filesystem."""
        # Try S3 first if we haven't checked yet
        if not self._checked:
            try:
                _ = self.client  # triggers _ensure_bucket
            except Exception:
                self._available = False
                self._checked = True

        if self._available:
            try:
                self.client.upload_fileobj(file_obj, self.bucket, object_name)
                return object_name
            except ClientError as e:
                logger.error(f"S3 upload failed: {e}")
                raise
        else:
            # Local filesystem fallback
            local_path = self._ensure_local_dir(object_name)
            with open(local_path, "wb") as f:
                # file_obj may be a SpooledTemporaryFile — read in chunks
                while True:
                    chunk = file_obj.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
            logger.info(f"Saved file locally: {local_path}")
            return object_name

    def get_presigned_url(self, object_name: str, expiration=3600) -> str:
        """Generate a presigned URL for downloading an object."""
        if not self._available:
            return None
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
        """Download file content. Uses S3 if available, else reads from local filesystem."""
        if self._available:
            try:
                response = self.client.get_object(Bucket=self.bucket, Key=object_name)
                return response['Body'].read()
            except ClientError as e:
                logger.error(e)
                raise
        else:
            # Local filesystem fallback
            local_path = os.path.join(_UPLOADS_DIR, object_name)
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"File not found in local storage: {local_path}")
            with open(local_path, "rb") as f:
                return f.read()

# Lazy singleton — no network call at import time
s3_client = S3Client()
