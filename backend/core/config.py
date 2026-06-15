from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "ResumeTailor AI"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    ALLOWED_METHODS: list[str] = ["GET", "POST", "OPTIONS"]
    ALLOWED_HEADERS: list[str] = ["Content-Type"]
    TEMP_UPLOAD_DIR: str = "./tmp/uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024
    MAX_REQUEST_BODY_BYTES: int = 2 * 1024 * 1024
    RATE_LIMIT_LLM: str = "10/minute"
    LOG_FORMAT: str = "json"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MAX_RETRIES: int = 2
    LLM_TIMEOUT_SECONDS: int = 30

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"


settings = Settings()
