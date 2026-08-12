from datetime import timedelta

from app.settings import settings
from minio import Minio
from minio.error import S3Error


class StorageService:
    def __init__(self):
        # Extract host and port cleanly from settings
        endpoint = settings.minio_endpoint.replace("http://", "").replace(
            "https://", ""
        )
        self.client = Minio(
            endpoint=endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket_name = "documents"

    def ensure_bucket_exists(self) -> None:
        """Ensure the target bucket exists in MinIO."""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def generate_presigned_upload_url(
        self, object_name: str, expires_seconds: int = 3600
    ) -> str:
        """Generate a presigned PUT URL for direct frontend uploads."""
        self.ensure_bucket_exists()
        return self.client.presigned_put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            expires=timedelta(seconds=expires_seconds),
        )

    def generate_presigned_download_url(
        self, object_name: str, expires_seconds: int = 3600
    ) -> str:
        """Generate a presigned GET URL for document retrieval."""
        return self.client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            expires=timedelta(seconds=expires_seconds),
        )

    def delete_file(self, object_name: str) -> None:
        """Remove a file from MinIO storage."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            raise RuntimeError(f"Failed to delete file from object storage: {e}")


storage_service = StorageService()
