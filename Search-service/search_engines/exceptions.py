class SearchEngineError(Exception):
    """Base exception for all search engine integration errors."""


class SearchEngineConnectionError(SearchEngineError):
    """Raised when the configured search backend cannot be reached."""


class UnsupportedSearchBackendError(SearchEngineError):
    """Raised when the configured backend is not supported."""


class SearchDocumentNotFoundError(SearchEngineError):
    """Raised when a document cannot be found."""


class SearchDocumentAlreadyExistsError(SearchEngineError):
    """Raised when a create operation conflicts with an existing document."""
