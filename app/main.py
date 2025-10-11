# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from tortoise.contrib.fastapi import register_tortoise
from app.routes import create_sub_app
import importlib
from pathlib import Path
from app.utils.sync_permissions import sync_permissions
from app.config import settings, init_db
from applications.user.models import User
from app.redis import init_redis, redis_client
from app.utils.auto_routing import get_module

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await sync_permissions()
    await init_db()
    init_redis()
    admin_user = await User.filter(username="admin").first()
    if not admin_user:
        await User.create(
            username="admin",
            email="admin@gmail.com",
            password=User.hash_password("admin"),
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        print("✅ Default superuser created: username=admin, password=admin")
    else:
        print("ℹ️ Default superuser already exists.")

    yield
    if redis_client:
        await redis_client.aclose()
    print("Application shutdown complete.")

# --- FastAPI app ---
app = FastAPI(lifespan=lifespan, debug=settings.DEBUG)

# --- Auto-mount routes ---
apps = get_module(base_dir='applications')
routes = get_module(base_dir='routes')

for route_name in routes:
    try:
        routes_module = importlib.import_module(f"routes.{route_name}.routes")
        sub_app = create_sub_app(route_name, routes_module.router)
        app.mount(f"/{route_name}", sub_app)
    except ModuleNotFoundError as e:
        print(f"⚠️ Warning: Could not find routes for '{route_name}'. Skipping. Error: {e}")

# --- Register Tortoise ORM models ---
def get_model_modules(apps):
    modules = []
    for app_name in apps:
        module_path = Path(f"applications/{app_name}/models.py")
        if module_path.exists():
            modules.append(f"applications.{app_name}.models")
    return modules

register_tortoise(
    app,
    db_url=settings.DATABASE_URL,
    modules={"models": get_model_modules(apps)},
    generate_schemas=not settings.DEBUG,
    add_exception_handlers=True,
)

# --- CORS ---
ALLOWED_HOST = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Media ---
MEDIA_DIR = "media"
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
