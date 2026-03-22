from typing import Any

import cloudinary
import cloudinary.uploader
from fastapi import HTTPException, status

from app.config import settings


def _validate_configuration() -> None:
    if not settings.CLOUDINARY_CLOUD_NAME or not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary is not configured on the server",
        )


def upload_media(file_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
    _validate_configuration()

    if not content_type.startswith("image/") and not content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image and video uploads are supported",
        )

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

    upload_result = cloudinary.uploader.upload(
        file=file_bytes,
        resource_type="auto",
        public_id=filename.rsplit(".", 1)[0] if "." in filename else filename,
        folder=settings.CLOUDINARY_UPLOAD_FOLDER,
        use_filename=True,
        unique_filename=True,
        overwrite=False,
    )
    return upload_result
