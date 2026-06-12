from pydantic import BaseModel, ConfigDict, Field


class ParseResumeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    raw_text: str = Field(alias="rawText")
