"""Public Python operations owned by the providers capability."""

from .model_config import (
    models,
    search as search_providers,
    routes,
)
from .model_invocation import (
    ask_model,
)
from .provider_transport import (
    post_json,
)

API_PROTOCOL = "iqs.providers-api/1.0.0"

__all__ = (
    "API_PROTOCOL",
    "ask_model",
    "models",
    "post_json",
    "routes",
    "search_providers",
)
