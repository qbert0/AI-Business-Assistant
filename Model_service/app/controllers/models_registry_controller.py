from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_db, get_settings
from app.repositories import RegistryRepository


router = APIRouter(tags=["Registry"])


@router.get("/models", response_model=list[models.ModelRead], summary="Lay danh sach model da dang ky")
def list_models(
    provider_id: str | None = Query(None),
    provider_name: str | None = Query(None, description="Tim theo ten provider"),
    model_name: str | None = Query(None, description="Tim theo model_name hoac display_name"),
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
) -> list[models.ModelRead]:
    return RegistryRepository(db, get_settings()).list_models(
        provider_id=provider_id,
        provider_name=provider_name,
        model_name=model_name,
        is_active=is_active,
    )


@router.post("/models", response_model=models.ModelRead, status_code=status.HTTP_201_CREATED, summary="Dang ky model moi")
def create_model(payload: models.ModelCreate, db: Session = Depends(get_db)) -> models.ModelRead:
    return RegistryRepository(db, get_settings()).create_model(payload)


@router.get("/models/{model_id}", response_model=models.ModelRead, summary="Lay chi tiet model")
def get_model(model_id: str, db: Session = Depends(get_db)) -> models.ModelRead:
    return RegistryRepository(db, get_settings()).get_model(model_id)


@router.patch("/models/{model_id}", response_model=models.ModelRead, summary="Cap nhat model")
def update_model(model_id: str, payload: models.ModelUpdate, db: Session = Depends(get_db)) -> models.ModelRead:
    return RegistryRepository(db, get_settings()).update_model(model_id, payload)


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xoa model")
def delete_model(model_id: str, db: Session = Depends(get_db)) -> Response:
    RegistryRepository(db, get_settings()).delete_model(model_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/models/{model_id}/health", response_model=models.ModelHealthCheckRead, summary="Test ket noi model upstream")
def check_model_health(model_id: str, db: Session = Depends(get_db)) -> models.ModelHealthCheckRead:
    return RegistryRepository(db, get_settings()).run_health_check(model_id)


@router.get("/policies", response_model=list[models.PolicyRead], summary="Lay danh sach model policy")
def list_policies(
    organization_id: str | None = Query(None),
    use_case: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[models.PolicyRead]:
    return RegistryRepository(db, get_settings()).list_policies(organization_id=organization_id, use_case=use_case)


@router.post("/policies", response_model=models.PolicyRead, status_code=status.HTTP_201_CREATED, summary="Tao policy chon model")
def create_policy(payload: models.PolicyCreate, db: Session = Depends(get_db)) -> models.PolicyRead:
    return RegistryRepository(db, get_settings()).create_policy(payload)


@router.get("/policies/{policy_id}", response_model=models.PolicyRead, summary="Lay chi tiet policy")
def get_policy(policy_id: str, db: Session = Depends(get_db)) -> models.PolicyRead:
    return RegistryRepository(db, get_settings()).get_policy(policy_id)


@router.patch("/policies/{policy_id}", response_model=models.PolicyRead, summary="Cap nhat policy")
def update_policy(policy_id: str, payload: models.PolicyUpdate, db: Session = Depends(get_db)) -> models.PolicyRead:
    return RegistryRepository(db, get_settings()).update_policy(policy_id, payload)


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xoa policy")
def delete_policy(policy_id: str, db: Session = Depends(get_db)) -> Response:
    RegistryRepository(db, get_settings()).delete_policy(policy_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

