from pydantic import BaseModel, Field, field_validator


class CameraCreate(BaseModel):
    camera_id: str = Field(min_length=1, max_length=100)
    source_url: str = Field(min_length=1)

    @field_validator("camera_id", "source_url")
    @classmethod
    def validate_not_empty(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value