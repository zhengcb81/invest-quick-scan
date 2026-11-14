"""Public Python operations owned by the execution capability."""

from .thin_scan import (
    main as scan_main,
)
from .shared_company_engine import (
    SharedEngineInterrupted,
    SharedEngineRejected,
    capabilities,
    execute_shared_engine,
    finalize_shared_engine,
    inspect_native_recovery,
    preflight,
    resume_shared_engine,
)
from .shared_company_task import (
    NativeTaskRejected,
    create_company_scan_task,
    create_native_task,
)

API_PROTOCOL = "iqs.execution-api/1.0.0"

__all__ = (
    "API_PROTOCOL",
    "NativeTaskRejected",
    "SharedEngineInterrupted",
    "SharedEngineRejected",
    "capabilities",
    "create_company_scan_task",
    "create_native_task",
    "execute_shared_engine",
    "finalize_shared_engine",
    "inspect_native_recovery",
    "preflight",
    "resume_shared_engine",
    "scan_main",
)
