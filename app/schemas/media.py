from pydantic import BaseModel, HttpUrl


class MediaUploadResponse(BaseModel):
    url: HttpUrl
    public_id: str
    resource_type: str
    format: str | None = None
    bytes: int | None = None
    width: int | None = None
    height: int | None = None
    duration: float | None = None
