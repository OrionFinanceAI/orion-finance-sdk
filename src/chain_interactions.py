"""Interactions with the Orion contracts."""

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from web3 import Web3
from web3.types import TxReceipt

load_dotenv()


@dataclass
class TransactionResult:
    """Result of a transaction including receipt and extracted logs."""

    tx_hash: str
    receipt: TxReceipt


def load_contract_abi(contract_name: str) -> list[dict]:
    """Load the ABI for a given contract."""
    # Get directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    abi_path = os.path.join(script_dir, "..", "abis", f"{contract_name}.json")
    with open(abi_path) as f:
        return json.load(f)["abi"]


class OrionSmartContract:
    """Base class for Orion smart contracts."""

    def __init__(
        self, contract_name: str, contract_address: str, rpc_url: str | None = None
    ):
        """Initialize a smart contract."""
        if not rpc_url:
            rpc_url = os.getenv("RPC_URL")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_name = contract_name
        self.contract_address = contract_address
        self.contract = self.w3.eth.contract(
            address=self.contract_address, abi=load_contract_abi(self.contract_name)
        )

    def _wait_for_transaction_receipt(
        self, tx_hash: str, timeout: int = 120
    ) -> TxReceipt:
        """Wait for a transaction to be mined and return the receipt."""
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)


class OrionConfig(OrionSmartContract):
    """OrionConfig contract."""

    def __init__(self, contract_address: str | None = None, rpc_url: str | None = None):
        """Initialize the OrionConfig contract."""
        if not contract_address:
            contract_address = os.getenv("CONFIG_ADDRESS")
        super().__init__("OrionConfig", contract_address, rpc_url)

    @property
    def whitelisted_vaults(self) -> list[str]:
        """Fetch all whitelisted vault addresses from the OrionConfig contract."""
        vault_count = self.contract.functions.whitelistVaultCount().call()
        vaults = []
        for i in range(vault_count):
            vault_address = self.contract.functions.getWhitelistedVaultAt(i).call()
            vaults.append(vault_address.lower())

        return vaults

    def is_whitelisted(self, token_address: str) -> bool:
        """Check if a token address is whitelisted."""
        return self.contract.functions.isWhitelisted(
            Web3.to_checksum_address(token_address)
        ).call()

    @property
    def curator_intent_decimals(self) -> int:
        """Fetch the curator intent decimals from the OrionConfig contract."""
        return self.contract.functions.curatorIntentDecimals().call()

    @property
    def fhe_public_cid(self) -> str:
        """Fetch the FHE public CID from the OrionConfig contract."""
        return self.contract.functions.fhePublicCID().call()


class OrionTransparentVault(OrionSmartContract):
    """OrionTransparentVault contract."""

    def __init__(self, contract_address: str | None = None, rpc_url: str | None = None):
        """Initialize the OrionTransparentVault contract."""
        if not contract_address:
            contract_address = os.getenv("ORION_VAULT_ADDRESS")
        super().__init__("OrionVault", contract_address, rpc_url)
        # TODO: write transparent vault contract and encrypted vault contract as separate contracts, update name here.

    def submit_order_intent(
        self,
        order_intent: dict[str, int],
        curator_private_key: str | None = None,
    ) -> TransactionResult:
        """Submit a portfolio order intent.

        Args:
            order_intent: Dictionary mapping token addresses to amounts
            curator_private_key: Private key for signing the transaction

        Returns:
            TransactionResult
        """
        if not curator_private_key:
            curator_private_key = os.getenv("CURATOR_PRIVATE_KEY")

        account = self.w3.eth.account.from_key(curator_private_key)
        nonce = self.w3.eth.get_transaction_count(account.address)

        items = [
            {"token": Web3.to_checksum_address(token), "amount": amount}
            for token, amount in order_intent.items()
        ]
        tx = self.contract.functions.submitOrderIntentPlain(items).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": 500_000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        signed = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()

        # Wait for transaction to be mined
        receipt = self._wait_for_transaction_receipt(tx_hash_hex)

        # Check if transaction was successful
        if receipt["status"] != 1:
            raise Exception(f"Transaction failed with status: {receipt['status']}")

        return TransactionResult(tx_hash=tx_hash_hex, receipt=receipt)
