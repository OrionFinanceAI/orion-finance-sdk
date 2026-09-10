"""Chain-specific OrionConfig env. No defaults, no ORION_CONFIG_ADDRESS."""

from __future__ import annotations

import os
from collections.abc import Mapping

from web3 import Web3

from .types import ZERO_ADDRESS

SEPOLIA_ORION_CONFIG = "0xbDe3025d08681a02a1c6cf70375baBe2152DD06f"


def resolve_orion_config_address(
    chain_id: int | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    """Return checksummed OrionConfig for the active chain.

    ``CHAIN_ID=1`` reads ``MAINNET_ORION_CONFIG_ADDRESS``; anything else
    (including unset, Sepolia, and local forks) reads ``SEPOLIA_ORION_CONFIG_ADDRESS``.
    """
    source: Mapping[str, str | None] = env if env is not None else os.environ
    if chain_id is None:
        raw_id = (source.get("CHAIN_ID") or "").strip()
        if not raw_id:
            chain_id = 11155111
        else:
            try:
                chain_id = int(raw_id)
            except ValueError as exc:
                raise ValueError(f"Invalid CHAIN_ID: {raw_id}") from exc

    is_mainnet = chain_id == 1
    name = "MAINNET_ORION_CONFIG_ADDRESS" if is_mainnet else "SEPOLIA_ORION_CONFIG_ADDRESS"
    network = "mainnet" if is_mainnet else "sepolia"
    raw = (source.get(name) or "").strip()
    if not raw:
        raise ValueError(f"{name} is required for network {network}")

    try:
        addr = Web3.to_checksum_address(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{name} is not a valid address") from exc

    if addr.lower() == ZERO_ADDRESS.lower():
        raise ValueError(f"{name} must not be the zero address")

    if is_mainnet and addr.lower() == SEPOLIA_ORION_CONFIG.lower():
        raise ValueError(f"{name} must not be the Sepolia OrionConfig")

    return addr
