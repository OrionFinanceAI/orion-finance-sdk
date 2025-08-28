"""Orion Finance Python SDK."""

import importlib.metadata

from orion_finance_sdk.cli import deploy_vault, submit_order

__version__ = importlib.metadata.version("orion-finance-sdk")

__all__ = ["deploy_vault", "submit_order"]
