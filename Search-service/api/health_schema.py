from pydantic import BaseModel


class SearchBackendHealthRead(BaseModel):
    backend: str
    backend_available: bool
