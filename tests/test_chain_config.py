from orion_finance_sdk_py.types import CHAIN_CONFIG


def test_registry_includes_sepolia_and_mainnet():
    assert CHAIN_CONFIG[11155111]["Explorer"] == "https://sepolia.etherscan.io"
    assert CHAIN_CONFIG[11155111]["OrionConfig"] == "0xbDe3025d08681a02a1c6cf70375baBe2152DD06f"
    assert CHAIN_CONFIG[1]["Explorer"] == "https://etherscan.io"
    assert CHAIN_CONFIG[1]["OrionConfig"] == "0xAba49f4eb48659fCb1f891b55D7a7b835C05af5E"
