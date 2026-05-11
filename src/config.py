from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    llm_model: str = Field(default="mistralai/mistral-7b-instruct:free", alias="LLM_MODEL")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")
    request_timeout: int = Field(default=30, alias="REQUEST_TIMEOUT")

    model_config = {"env_file": ".env", "populate_by_name": True}

    @field_validator("openrouter_api_key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        if not v.startswith("sk-"):
            raise ValueError("OPENROUTER_API_KEY должен начинаться с 'sk-'")
        return v