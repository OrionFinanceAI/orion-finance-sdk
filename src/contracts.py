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
    decoded_logs: list[dict] | None = None


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
        """Wait for a transaction to be processed and return the receipt."""
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)

    def _decode_logs(self, receipt: TxReceipt) -> list[dict]:
        """Decode logs from a transaction receipt."""
        decoded_logs = []
        for log in receipt.logs:
            # Only process logs from this contract
            if log.address.lower() != self.contract_address.lower():
                continue

            # Try to decode the log with each event in the contract
            for event in self.contract.events:
                try:
                    decoded_log = event.process_log(log)
                    decoded_logs.append(
                        {
                            "event": decoded_log.event,
                            "args": dict(decoded_log.args),
                            "address": decoded_log.address,
                            "blockHash": decoded_log.blockHash.hex(),
                            "blockNumber": decoded_log.blockNumber,
                            "logIndex": decoded_log.logIndex,
                            "transactionHash": decoded_log.transactionHash.hex(),
                            "transactionIndex": decoded_log.transactionIndex,
                        }
                    )
                    break  # Successfully decoded, move to next log
                except Exception:
                    # This event doesn't match this log, try the next event
                    continue
        return decoded_logs


class OrionConfig(OrionSmartContract):
    """OrionConfig contract."""

    def __init__(self, contract_address: str | None = None, rpc_url: str | None = None):
        """Initialize the OrionConfig contract."""
        if not contract_address:
            contract_address = os.getenv("CONFIG_ADDRESS")
        super().__init__("OrionConfig", contract_address, rpc_url)

    @property
    def whitelisted_assets(self) -> list[str]:
        """Fetch all whitelisted vault addresses from the OrionConfig contract."""
        assets_length = self.contract.functions.whitelistedAssetsLength().call()
        assets = []
        for i in range(assets_length):
            asset_address = self.contract.functions.getWhitelistedAssetAt(i).call()
            assets.append(asset_address.lower())

        return assets

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


class OrionVaultFactory(OrionSmartContract):
    """OrionVaultFactory contract."""

    def __init__(self, contract_address: str | None = None, rpc_url: str | None = None):
        """Initialize the OrionVaultFactory contract."""
        if not contract_address:
            contract_address = os.getenv("FACTORY_ADDRESS")
        super().__init__("OrionVaultFactory", contract_address, rpc_url)

    def create_orion_transparent_vault(
        self,
        curator_address: str | None = None,
        name: str | None = None,
        symbol: str | None = None,
        deployer_private_key: str | None = None,
    ) -> TransactionResult:
        """Create an Orion vault for a given curator address."""
        if not curator_address:
            curator_address = os.getenv("CURATOR_ADDRESS")

        if not deployer_private_key:
            # In principle, deployer and curator are different accounts.
            deployer_private_key = os.getenv("DEPLOYER_PRIVATE_KEY")

        account = self.w3.eth.account.from_key(deployer_private_key)
        nonce = self.w3.eth.get_transaction_count(account.address)

        # Estimate gas needed for the transaction
        gas_estimate = self.contract.functions.createOrionTransparentVault(
            curator_address, name, symbol
        ).estimate_gas({"from": account.address, "nonce": nonce})

        # Add 20% buffer to gas estimate
        gas_limit = int(gas_estimate * 1.2)

        tx = self.contract.functions.createOrionTransparentVault(
            curator_address, name, symbol
        ).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        signed = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()

        receipt = self._wait_for_transaction_receipt(tx_hash_hex)

        # Check if transaction was successful
        if receipt["status"] != 1:
            raise Exception(f"Transaction failed with status: {receipt['status']}")

        # Decode logs from the transaction receipt
        decoded_logs = self._decode_logs(receipt)

        return TransactionResult(
            tx_hash=tx_hash_hex, receipt=receipt, decoded_logs=decoded_logs
        )

    def create_orion_encrypted_vault(
        self,
        curator_address: str | None = None,
        name: str | None = None,
        symbol: str | None = None,
        deployer_private_key: str | None = None,
    ) -> TransactionResult:
        """Create an Orion encrypted vault for a given curator address."""
        raise NotImplementedError

    def get_vault_address_from_result(self, result: TransactionResult) -> str | None:
        """Extract the vault address from OrionVaultCreated event in the transaction result."""
        if not result.decoded_logs:
            return None

        for log in result.decoded_logs:
            if log.get("event") == "OrionVaultCreated":
                return log["args"].get("vault")

        return None


class OrionTransparentVault(OrionSmartContract):
    """OrionTransparentVault contract."""

    def __init__(self, contract_address: str | None = None, rpc_url: str | None = None):
        """Initialize the OrionTransparentVault contract."""
        if not contract_address:
            contract_address = os.getenv("ORION_VAULT_ADDRESS")
        super().__init__("OrionTransparentVault", contract_address, rpc_url)

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

        # Estimate gas needed for the transaction
        gas_estimate = self.contract.functions.submitOrderIntent(items).estimate_gas(
            {"from": account.address, "nonce": nonce}
        )

        # Add 20% buffer to gas estimate
        gas_limit = int(gas_estimate * 1.2)

        tx = self.contract.functions.submitOrderIntent(items).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        signed = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash_hex = tx_hash.hex()

        receipt = self._wait_for_transaction_receipt(tx_hash_hex)

        if receipt["status"] != 1:
            raise Exception(f"Transaction failed with status: {receipt['status']}")

        decoded_logs = self._decode_logs(receipt)

        return TransactionResult(
            tx_hash=tx_hash_hex, receipt=receipt, decoded_logs=decoded_logs
        )


class OrionEncryptedVault(OrionSmartContract):
    """OrionEncryptedVault contract."""

    def __init__(self, contract_address: str | None = None, rpc_url: str | None = None):
        """Initialize the OrionEncryptedVault contract."""
        raise NotImplementedError
