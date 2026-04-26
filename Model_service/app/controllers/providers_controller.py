from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app import models
from app.api.deps import get_db, get_settings
from app.repositories import RegistryRepository


router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("", response_model=list[models.ProviderRead], summary="Lay danh sach provider")
def list_providers(
    name: str | None = Query(None, description="Tim provider theo ten"),
    db: Session = Depends(get_db),
) -> list[models.ProviderRead]:
    return RegistryRepository(db, get_settings()).list_providers(name=name)


@router.post("", response_model=models.ProviderRead, status_code=status.HTTP_201_CREATED, summary="Tao provider moi")
def create_provider(payload: models.ProviderCreate, db: Session = Depends(get_db)) -> models.ProviderRead:
    return RegistryRepository(db, get_settings()).create_provider(payload)


@router.get("/{provider_id}", response_model=models.ProviderRead, summary="Lay chi tiet provider")
def get_provider(provider_id: str, db: Session = Depends(get_db)) -> models.ProviderRead:
    return RegistryRepository(db, get_settings()).get_provider(provider_id)


@router.patch("/{provider_id}", response_model=models.ProviderRead, summary="Cap nhat provider")
def update_provider(
    provider_id: str,
    payload: models.ProviderUpdate,
    db: Session = Depends(get_db),
) -> models.ProviderRead:
    return RegistryRepository(db, get_settings()).update_provider(provider_id, payload)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xoa provider")
def delete_provider(provider_id: str, db: Session = Depends(get_db)) -> Response:
    RegistryRepository(db, get_settings()).delete_provider(provider_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

