from collections.abc import Mapping

import pytest
from orion_finance_sdk_py.orion_config_env import (
    MAINNET_CHAIN_ID,
    SEPOLIA_CHAIN_ID,
    SEPOLIA_ORION_CONFIG,
    parse_chain_name,
    resolve_active_chain_id,
    resolve_orion_config_address,
)
from orion_finance_sdk_py.types import ZERO_ADDRESS
from web3 import Web3

OTHER = "0x1111111111111111111111111111111111111111"


def test_sepolia_checksums():
    assert resolve_orion_config_address(
        11155111, {"SEPOLIA_ORION_CONFIG_ADDRESS": SEPOLIA_ORION_CONFIG.lower()}
    ) == Web3.to_checksum_address(SEPOLIA_ORION_CONFIG)


def test_hardhat_and_localhost_use_sepolia_var():
    env: Mapping[str, str] = {"SEPOLIA_ORION_CONFIG_ADDRESS": SEPOLIA_ORION_CONFIG}
    assert resolve_orion_config_address(31337, env) == Web3.to_checksum_address(
        SEPOLIA_ORION_CONFIG
    )


def test_mainnet_checksums():
    assert resolve_orion_config_address(1, {"MAINNET_ORION_CONFIG_ADDRESS": OTHER}) == (
        Web3.to_checksum_address(OTHER)
    )


def test_does_not_read_the_other_chain_var():
    with pytest.raises(ValueError, match="SEPOLIA_ORION_CONFIG_ADDRESS is required"):
        resolve_orion_config_address(11155111, {"MAINNET_ORION_CONFIG_ADDRESS": OTHER})
    with pytest.raises(ValueError, match="MAINNET_ORION_CONFIG_ADDRESS is required"):
        resolve_orion_config_address(1, {"SEPOLIA_ORION_CONFIG_ADDRESS": SEPOLIA_ORION_CONFIG})


def test_unset_or_blank_throws():
    with pytest.raises(ValueError, match="SEPOLIA_ORION_CONFIG_ADDRESS is required"):
        resolve_orion_config_address(11155111, {})
    with pytest.raises(ValueError, match="MAINNET_ORION_CONFIG_ADDRESS is required"):
        resolve_orion_config_address(1, {"MAINNET_ORION_CONFIG_ADDRESS": "   "})


def test_zero_address_throws():
    with pytest.raises(ValueError, match="must not be the zero address"):
        resolve_orion_config_address(
            11155111, {"SEPOLIA_ORION_CONFIG_ADDRESS": ZERO_ADDRESS}
        )


def test_mainnet_rejects_sepolia_config():
    with pytest.raises(ValueError, match="must not be the Sepolia OrionConfig"):
        resolve_orion_config_address(
            1, {"MAINNET_ORION_CONFIG_ADDRESS": SEPOLIA_ORION_CONFIG}
        )


def test_ignores_orion_config_address():
    with pytest.raises(ValueError, match="SEPOLIA_ORION_CONFIG_ADDRESS is required"):
        resolve_orion_config_address(
            11155111, {"ORION_CONFIG_ADDRESS": SEPOLIA_ORION_CONFIG}
        )


def test_chain_id_from_env():
    env = {
        "CHAIN_ID": "1",
        "MAINNET_ORION_CONFIG_ADDRESS": OTHER,
    }
    assert resolve_orion_config_address(env=env) == Web3.to_checksum_address(OTHER)


def test_chain_env_name_selects_mainnet():
    env = {
        "CHAIN": "mainnet",
        "MAINNET_ORION_CONFIG_ADDRESS": OTHER,
    }
    assert resolve_orion_config_address(env=env) == Web3.to_checksum_address(OTHER)


def test_parse_and_resolve_active_chain():
    assert parse_chain_name("Sepolia") == SEPOLIA_CHAIN_ID
    assert parse_chain_name("mainnet") == MAINNET_CHAIN_ID
    assert resolve_active_chain_id("mainnet") == MAINNET_CHAIN_ID
    assert resolve_active_chain_id(env={}) == SEPOLIA_CHAIN_ID
    assert resolve_active_chain_id(env={"CHAIN": "mainnet"}) == MAINNET_CHAIN_ID
    assert resolve_active_chain_id(env={"CHAIN_ID": "1"}) == MAINNET_CHAIN_ID
    # --chain wins over CHAIN env
    assert resolve_active_chain_id("sepolia", {"CHAIN": "mainnet"}) == SEPOLIA_CHAIN_ID
    with pytest.raises(ValueError, match="Unsupported chain"):
        parse_chain_name("base")
