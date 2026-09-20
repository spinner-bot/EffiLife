"""
    ====== web/__init__.py ======
    Web UI package for plan-helper.
    Run with: python -m web.server
"""

from .server import run_server

__all__ = ["run_server"]
