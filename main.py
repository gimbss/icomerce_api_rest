from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from api.routers.auth_router import router as auth_router
from api.routers.product_router import router as product_router
from api.routers.order_router import router as order_router

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="eCommerce API",
    description="RESTful API for the eCommerce e-commerce platform",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1")
app.include_router(order_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "eCommerce API", "version": "1.0.0", "message": "API feita em python usando FastAPI para o exercício de e-commerce. Acesse /docs para a documentação interativa. Feito por: Gilberto Neto - 2026."}


PUBLIC_PATH_PREFIXES = ("/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/auth/validate", "/api/v1/auth/resend-verification", "/")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    if "components" not in schema:
        schema["components"] = {}
    if "securitySchemes" not in schema["components"]:
        schema["components"]["securitySchemes"] = {}
    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for path, path_item in schema["paths"].items():
        is_public = any(path.startswith(p) for p in PUBLIC_PATH_PREFIXES)
        for method in path_item.values():
            if not isinstance(method, dict):
                continue
            if "security" in method:
                method["security"] = [
                    {"BearerAuth": []} if "HTTPBearer" in sec else sec
                    for sec in method["security"]
                ]
            elif not is_public:
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
