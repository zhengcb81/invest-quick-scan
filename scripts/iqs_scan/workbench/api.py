"""Public entry point for workbench-owned diagnostic replay."""

from .company_result_feedback_cli import main as replay_company_result_feedback

API_PROTOCOL = "iqs.workbench-api/1.0.0"
__all__ = ("API_PROTOCOL", "replay_company_result_feedback")
