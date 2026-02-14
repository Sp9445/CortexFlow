from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

env = os.getenv("APP_ENV", "local")
env_file = f".env.{env}"
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv(".env")

class Settings(BaseSettings):
    app_env: str

    # Database
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # JWT (add these to your .env files)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GROK_BASE_URL:str
    GROK_API_KEY: str
    AI_MODEL:str

    class Config:
        env_file = env_file
        case_sensitive = False

settings = Settings()