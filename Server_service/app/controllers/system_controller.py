from fastapi import APIRouter

from app.constants.openapi import API_CAPABILITIES
from app.constants.permissions import ADMIN_PERMISSIONS, DEFAULT_USER_PERMISSIONS, PERMISSION_DESCRIPTIONS
from app import models

router = APIRouter()


@router.get("/", response_model=models.ApiInfo, tags=["System"], summary="Thong tin API va link Swagger")
def root() -> models.ApiInfo:
    return models.ApiInfo(
        name="AI Business Assistant API",
        version="1.0.0",
        docs_url="/docs",
        health_url="/health",
        capabilities=API_CAPABILITIES,
    )


@router.get("/health", tags=["System"], summary="Kiem tra server dang chay")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/permissions", response_model=models.PermissionCatalog, tags=["Members & RBAC"], summary="Danh muc role va permission")
def permission_catalog() -> models.PermissionCatalog:
    return models.PermissionCatalog(
        roles={"admin": ADMIN_PERMISSIONS, "user": DEFAULT_USER_PERMISSIONS},
        permissions=PERMISSION_DESCRIPTIONS,
    )
