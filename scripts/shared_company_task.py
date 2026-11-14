"""Compatibility entry points for tasks created by the StockQA owner.

The original native identity, input bytes, authorized question set, and route
belong to StockQA. IQS supplies scan intent and delegates task construction
through StockQA's versioned public API; it never reconstructs owner state.
"""

from __future__ import annotations

import sys
from pathlib import Path


COMPANY_SCAN_TASK_PORT_PROTOCOL = "stockqa.company_scan_task_port/1.0.0"


class NativeTaskRejected(ValueError):
    """The StockQA owner rejected the requested task construction."""


def _current_owner_api_protocols():
    scripts = str(Path(__file__).resolve().parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from shared_company_ports import current_owner_api_protocols

    return current_owner_api_protocols()


def _create_owner_task(operation, lifecycle, **kwargs):
    _current_owner_api_protocols()
    import src.utils.quick_scan_company_api as quick_scan_company_api

    advertised = getattr(quick_scan_company_api, "__all__", ())
    factory = getattr(quick_scan_company_api, operation, None)
    if operation not in advertised or not callable(factory):
        raise NativeTaskRejected("stockqa_company_task_factory_unavailable")
    try:
        return factory(lifecycle, **kwargs)
    except (TypeError, ValueError) as error:
        raise NativeTaskRejected(str(error)) from error


def create_native_task(
    lifecycle,
    *,
    experiment_id,
    run_id,
    strategy_id="free_agent",
    question_ids=None,
    evidence_board=None,
    limits=None,
):
    """Delegate native task construction to the owner of its source inputs."""
    return _create_owner_task(
        "create_native_task",
        lifecycle,
        experiment_id=experiment_id,
        run_id=run_id,
        strategy_id=strategy_id,
        question_ids=question_ids,
        evidence_board=evidence_board,
        limits=limits,
    )


def create_company_scan_task(
    lifecycle,
    *,
    experiment_id,
    run_id,
    question_ids=None,
    evidence_board=None,
    limits=None,
    pack_by="module",
    max_questions_per_pack=12,
    search_exposure=None,
):
    """Delegate scan task construction to StockQA's versioned owner facade."""
    return _create_owner_task(
        "create_company_scan_task",
        lifecycle,
        experiment_id=experiment_id,
        run_id=run_id,
        question_ids=question_ids,
        evidence_board=evidence_board,
        limits=limits,
        pack_by=pack_by,
        max_questions_per_pack=max_questions_per_pack,
        search_exposure=search_exposure,
    )
