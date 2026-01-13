"""
MemoQ AIQE Connector

AI-powered Quality Estimation connector for MemoQ translation management system.
"""

__version__ = "1.0.0"
__author__ = "AIQE Development Team"

from src.memoq_client import MemoQClient
from src.aiqe_engine import AIQEEngine
from src.termbase_manager import TermBaseManager
from src.workflow_handler import WorkflowHandler

__all__ = [
    "MemoQClient",
    "AIQEEngine",
    "TermBaseManager",
    "WorkflowHandler",
]
