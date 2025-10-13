from typing import Optional
from pydantic_settings import BaseSettings
from tortoise import Tortoise
from app.utils.auto_routing import get_module
from pathlib import Path
import os

class Settings(BaseSettings):
    DEBUG: bool = True
    MEDIA_DIR: str = "media"
    ENV: str = "development"
    DATABASE_URL: str
    SECRET_KEY: Optional[str]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
settings = Settings()


apps = get_module(base_dir='applications')
def get_model_modules(apps):
    modules = []
    for app_name in apps:
        module_path = Path(f"applications/{app_name}/models.py")
        if module_path.exists():
            modules.append(f"applications.{app_name}.models")
    return modules


TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": get_model_modules(apps) + ["aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "Asia/Dhaka",
}

async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    if os.environ.get("ENV") != "production":
        await Tortoise.generate_schemas()
