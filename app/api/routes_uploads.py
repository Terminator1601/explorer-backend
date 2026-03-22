import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.models.user import User
from app.schemas.media import MediaUploadResponse
from app.services.auth_service import get_current_user
from app.services.cloudinary_service import upload_media

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/media", response_model=MediaUploadResponse)
async def upload_media_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name is required")

    content_type = file.content_type or ""
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    # Use a UUID suffix to keep uploaded asset names unique.
    unique_filename = f"{uuid.uuid4()}-{file.filename}"
    result = upload_media(payload, unique_filename, content_type)

    return MediaUploadResponse(
        url=result["secure_url"],
        public_id=result["public_id"],
        resource_type=result.get("resource_type", "raw"),
        format=result.get("format"),
        bytes=result.get("bytes"),
        width=result.get("width"),
        height=result.get("height"),
        duration=result.get("duration"),
    )
