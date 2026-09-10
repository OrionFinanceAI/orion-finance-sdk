from orion_finance_sdk_py.types import CHAIN_CONFIG, ZERO_ADDRESS


def test_registry_includes_sepolia_and_mainnet():
    assert CHAIN_CONFIG[11155111]["Explorer"] == "https://sepolia.etherscan.io"
    assert CHAIN_CONFIG[11155111]["OrionConfig"] == "0xbDe3025d08681a02a1c6cf70375baBe2152DD06f"
    assert CHAIN_CONFIG[1]["Explorer"] == "https://etherscan.io"
    assert CHAIN_CONFIG[1]["OrionConfig"] == ZERO_ADDRESS
