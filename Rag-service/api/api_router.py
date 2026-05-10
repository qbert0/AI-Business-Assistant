from fastapi import APIRouter

from api.api_compat import router as compat_router
from api.api_graph import router as graph_router
from api.api_healthcheck import router as health_router
from api.api_ingest import router as ingest_router
from api.api_search import router as search_router
from utils.constants import (
    COMPAT_ROUTE_PREFIX,
    GRAPH_ROUTE_PREFIX,
    HEALTH_ROUTE_PREFIX,
    INGEST_ROUTE_PREFIX,
    SEARCH_ROUTE_PREFIX,
)

router = APIRouter()

ROUTERS = [
    (health_router, "Health", HEALTH_ROUTE_PREFIX),
    (compat_router, "Compat", COMPAT_ROUTE_PREFIX),
    (ingest_router, "Ingest", INGEST_ROUTE_PREFIX),
    (search_router, "Search", SEARCH_ROUTE_PREFIX),
    (graph_router, "Graph", GRAPH_ROUTE_PREFIX),
]

for router_item, tag, prefix in ROUTERS:
    router.include_router(router_item, tags=[tag], prefix=prefix)
