# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    init_redis()
    await sync_permissions()
    admin_user = await User.filter(email="admin@gmail.com").first()
    if not admin_user:
        await User.create(
            username="admin",
            email="admin@gmail.com",
            password=User.set_password("admin"),
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
    yield
    if redis_client:
        await redis_client.aclose()
    print("Application shutdown complete.")


app = FastAPI(lifespan=lifespan, debug=settings.DEBUG)

@app.get("/", response_class=HTMLResponse)
async def home():
    if settings.DEBUG:
        html_path = Path("templates/development.html")
    else:
        html_path = Path("templates/index.html")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


apps = get_module(base_dir='applications')
routes = get_module(base_dir='routes')

for route_name in routes:
    try:
        routes_module = importlib.import_module(f"routes.{route_name}.routes")
        sub_app = create_sub_app(route_name, routes_module.router)
        app.mount(f"/{route_name}", sub_app)
    except ModuleNotFoundError as e:
        print(f"⚠️ Warning: Could not find routes for '{route_name}'. Skipping. Error: {e}")


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


ALLOWED_HOST = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


os.makedirs(settings.MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")
