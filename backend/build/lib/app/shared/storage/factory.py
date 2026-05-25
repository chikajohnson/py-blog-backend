from app.config import get_settings
from app.shared.storage.base import StorageProvider
from app.shared.storage.local import LocalFileStorage


def get_storage_provider() -> StorageProvider:
    settings = get_settings()
    if settings.STORAGE_PROVIDER.lower() == "s3":
        from app.shared.storage.s3 import S3Storage
        return S3Storage(settings.AWS_STORAGE_BUCKET_NAME, settings.AWS_S3_REGION, settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    return LocalFileStorage(base_dir=settings.UPLOAD_DIR)
