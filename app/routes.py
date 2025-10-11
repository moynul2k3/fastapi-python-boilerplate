from fastapi import FastAPI

def create_sub_app(name: str, router):
    app = FastAPI(
        title=f"{name.capitalize()} API",
        description=f"This is the {name.capitalize()} API",
        version="1.0.0",
        docs_url="/docs",      # swagger
        redoc_url="/redoc",    # redoc
        openapi_url="/openapi.json"
    )
    app.include_router(router)
    return app
