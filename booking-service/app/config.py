from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- ADD THIS LINE ---
    DATABASE_URL: str
    # This service needs to know the secret to VERIFY tokens
    SECRET_KEY: str
    ALGORITHM: str

    # URL of the property service for validation
    PROPERTY_SERVICE_URL: str = "http://backend:8000"

    # --- NEW KAFKA SETTINGS ---
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_PROPERTY_TOPIC: str = "property_updates"

    REDIS_URL: str

    model_config = SettingsConfigDict(env_file="../.env")


settings = Settings()
