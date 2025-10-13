from fastapi import FastAPI
from app.config import settings

# def create_sub_app(name: str, router):
#     app = FastAPI(
#         title=f"{name.capitalize()} API",
#         description=f"This is the {name.capitalize()} API",
#         version="1.0.0",
#         docs_url="/docs" if settings.DEBUG else False,      # swagger
#         redoc_url="/redoc" if settings.DEBUG else False,    # redoc
#         openapi_url="/openapi.json" if settings.DEBUG else False
#     )
#     app.include_router(router)
#     return app


def create_sub_app(name: str, router, lifespan=None, middlewares=None):
    app = FastAPI(
        title=f"{name.capitalize()} API",
        description=f"This is the {name.capitalize()} API",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else False,
        redoc_url="/redoc" if settings.DEBUG else False,
        openapi_url="/openapi.json" if settings.DEBUG else False,
        lifespan=lifespan,
    )
    app.include_router(router)
    if middlewares:
        for m in middlewares:
            app.middleware("http")(m)

    return app