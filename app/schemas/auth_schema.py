from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    api_key: str = Field(alias="x-api-key", min_length=10)
