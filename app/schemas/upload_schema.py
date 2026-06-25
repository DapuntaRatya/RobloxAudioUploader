from typing import List

from pydantic import BaseModel, Field, field_validator

from app.config import settings


class UploadOptions(BaseModel):
    parallel: bool = True
    grant_permission: bool = True
    cleanup_temp: bool = True


class UploadRequest(BaseModel):
    source_type: str = Field(min_length=1)
    audio_links: List[str] = Field(min_length=1)
    experience_ids: List[str] = Field(default_factory=list)
    options: UploadOptions = Field(default_factory=UploadOptions)

    @field_validator("audio_links")
    @classmethod
    def validate_audio_links(cls, value: List[str]) -> List[str]:
        clean = [item.strip() for item in value if item and item.strip()]
        if not clean:
            raise ValueError("Minimal 1 audio link harus diisi.")
        if len(clean) > settings.MAX_ITEMS_PER_JOB:
            raise ValueError(f"Maksimal {settings.MAX_ITEMS_PER_JOB} audio per job.")
        return clean

    @field_validator("experience_ids")
    @classmethod
    def validate_experience_ids(cls, value: List[str]) -> List[str]:
        clean = [item.strip() for item in value if item and item.strip()]
        if len(clean) > settings.MAX_EXPERIENCES_PER_JOB:
            raise ValueError(f"Maksimal {settings.MAX_EXPERIENCES_PER_JOB} experience per job.")

        invalid = [item for item in clean if not item.isdigit()]
        if invalid:
            raise ValueError(f"Experience ID harus angka: {invalid}")

        return clean
