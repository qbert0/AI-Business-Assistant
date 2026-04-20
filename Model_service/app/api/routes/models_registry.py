from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_settings
from app.schemas.model import (
    ModelCreate,
    ModelHealthCheckRead,
    ModelRead,
    ModelUpdate,
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
)
from app.services.registry_service import RegistryService


router = APIRouter(tags=["Registry"])


@router.get("/models", response_model=list[ModelRead], summary="Lay danh sach model da dang ky")
def list_models(
    provider_id: str | None = Query(None),
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
) -> list[ModelRead]:
    return RegistryService(db, get_settings()).list_models(provider_id=provider_id, is_active=is_active)


@router.post("/models", response_model=ModelRead, status_code=status.HTTP_201_CREATED, summary="Dang ky model moi")
def create_model(payload: ModelCreate, db: Session = Depends(get_db)) -> ModelRead:
    return RegistryService(db, get_settings()).create_model(payload)


@router.get("/models/{model_id}", response_model=ModelRead, summary="Lay chi tiet model")
def get_model(model_id: str, db: Session = Depends(get_db)) -> ModelRead:
    return RegistryService(db, get_settings()).get_model(model_id)


@router.patch("/models/{model_id}", response_model=ModelRead, summary="Cap nhat model")
def update_model(model_id: str, payload: ModelUpdate, db: Session = Depends(get_db)) -> ModelRead:
    return RegistryService(db, get_settings()).update_model(model_id, payload)


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xoa model")
def delete_model(model_id: str, db: Session = Depends(get_db)) -> Response:
    RegistryService(db, get_settings()).delete_model(model_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/models/{model_id}/health", response_model=ModelHealthCheckRead, summary="Test ket noi model upstream")
def check_model_health(model_id: str, db: Session = Depends(get_db)) -> ModelHealthCheckRead:
    return RegistryService(db, get_settings()).run_health_check(model_id)


@router.get("/policies", response_model=list[PolicyRead], summary="Lay danh sach model policy")
def list_policies(
    organization_id: str | None = Query(None),
    use_case: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[PolicyRead]:
    return RegistryService(db, get_settings()).list_policies(organization_id=organization_id, use_case=use_case)


@router.post("/policies", response_model=PolicyRead, status_code=status.HTTP_201_CREATED, summary="Tao policy chon model")
def create_policy(payload: PolicyCreate, db: Session = Depends(get_db)) -> PolicyRead:
    return RegistryService(db, get_settings()).create_policy(payload)


@router.get("/policies/{policy_id}", response_model=PolicyRead, summary="Lay chi tiet policy")
def get_policy(policy_id: str, db: Session = Depends(get_db)) -> PolicyRead:
    return RegistryService(db, get_settings()).get_policy(policy_id)


@router.patch("/policies/{policy_id}", response_model=PolicyRead, summary="Cap nhat policy")
def update_policy(policy_id: str, payload: PolicyUpdate, db: Session = Depends(get_db)) -> PolicyRead:
    return RegistryService(db, get_settings()).update_policy(policy_id, payload)


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xoa policy")
def delete_policy(policy_id: str, db: Session = Depends(get_db)) -> Response:
    RegistryService(db, get_settings()).delete_policy(policy_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
