from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_settings
from app.schemas.provider import ProviderCreate, ProviderRead, ProviderUpdate
from app.services.registry_service import RegistryService


router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("", response_model=list[ProviderRead], summary="Lay danh sach provider")
def list_providers(db: Session = Depends(get_db)) -> list[ProviderRead]:
    return RegistryService(db, get_settings()).list_providers()


@router.post("", response_model=ProviderRead, status_code=status.HTTP_201_CREATED, summary="Tao provider moi")
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db)) -> ProviderRead:
    return RegistryService(db, get_settings()).create_provider(payload)


@router.get("/{provider_id}", response_model=ProviderRead, summary="Lay chi tiet provider")
def get_provider(provider_id: str, db: Session = Depends(get_db)) -> ProviderRead:
    return RegistryService(db, get_settings()).get_provider(provider_id)


@router.patch("/{provider_id}", response_model=ProviderRead, summary="Cap nhat provider")
def update_provider(provider_id: str, payload: ProviderUpdate, db: Session = Depends(get_db)) -> ProviderRead:
    return RegistryService(db, get_settings()).update_provider(provider_id, payload)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xoa provider")
def delete_provider(provider_id: str, db: Session = Depends(get_db)) -> Response:
    RegistryService(db, get_settings()).delete_provider(provider_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
