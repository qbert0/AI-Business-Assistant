from fastapi import APIRouter

from api.api_healthcheck import router as health_router
from api.api_search_documents import router as search_documents_router
from utils.constants import HEALTH_ROUTE_PREFIX, SEARCH_DOCUMENTS_ROUTE_PREFIX

router = APIRouter()

ROUTERS = [
    (health_router, "Health", HEALTH_ROUTE_PREFIX),
    (search_documents_router, "Search Documents", SEARCH_DOCUMENTS_ROUTE_PREFIX),
]

for router_item, tag, prefix in ROUTERS:
    router.include_router(
        router_item, tags=[tag], prefix=f"{prefix}"
    )
