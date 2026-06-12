from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    file_name: str = Field(alias="fileName")
    file_size: int = Field(alias="fileSize")
    file_type: str = Field(alias="fileType")
