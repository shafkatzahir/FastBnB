from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    REDIS_URL: str

    # --- NEW KAFKA SETTINGS ---
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_PROPERTY_TOPIC: str = "property_updates"

    model_config = SettingsConfigDict(env_file="../../booking-service/.env")

settings = Settings()