"""Interactions with the Orion Finance protocol contracts."""

import json
import os
from dataclasses import dataclass

import typer
from dotenv import load_dotenv
from web3 import Web3
from web3.types import TxReceipt

from .utils import validate_address, validate_management_fee, validate_performance_fee

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

    # TODO: verify contracts once deployed, potentially in the same cli command, as soon as deployed it,
    # verify with the same input parameters.
    # Skip verification if Etherscan API key is not provided without failing command.

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
    def curator_intent_decimals(self) -> int:
        """Fetch the curator intent decimals from the OrionConfig contract."""
        return self.contract.functions.curatorIntentDecimals().call()

    @property
    def whitelisted_assets(self) -> list[str]:
        """Fetch all whitelisted assets from the OrionConfig contract."""
        return self.contract.functions.getAllWhitelistedAssets().call()

    def is_whitelisted(self, token_address: str) -> bool:
        """Check if a token address is whitelisted."""
        return self.contract.functions.isWhitelisted(
            Web3.to_checksum_address(token_address)
        ).call()

    @property
    def orion_transparent_vaults(self) -> list[str]:
        """Fetch all Orion transparent vault addresses from the OrionConfig contract."""
        return self.contract.functions.getAllOrionVaults(0).call()

    @property
    def orion_encrypted_vaults(self) -> list[str]:
        """Fetch all Orion encrypted vault addresses from the OrionConfig contract."""
        return self.contract.functions.getAllOrionVaults(1).call()

    def is_system_idle(self) -> bool:
        """Check if the system is in idle state, required for vault deployment."""
        return self.contract.functions.isSystemIdle().call()


class VaultFactory(OrionSmartContract):
    """VaultFactory contract."""

    def __init__(
        self,
        vault_type: str,
        contract_address: str | None = None,
        rpc_url: str | None = None,
    ):
        """Initialize the VaultFactory contract."""
        if not contract_address:
            contract_address = os.getenv(f"{vault_type.upper()}_VAULT_FACTORY_ADDRESS")
        super().__init__(
            f"{vault_type.capitalize()}VaultFactory", contract_address, rpc_url
        )

    def create_orion_vault(
        self,
        deployer_private_key: str | None = None,
        curator_address: str | None = None,
        name: str | None = None,
        symbol: str | None = None,
        fee_type: int | None = None,
        performance_fee: int | None = None,
        management_fee: int | None = None,
    ) -> TransactionResult:
        """Create an Orion vault for a given curator address."""
        config = OrionConfig()

        if not curator_address:
            curator_address = os.getenv("CURATOR_ADDRESS")
        validate_address(curator_address)

        if not deployer_private_key:
            # In principle, deployer and curator are different accounts.
            deployer_private_key = os.getenv("VAULT_DEPLOYER_PRIVATE_KEY")
        try:
            account = config.w3.eth.account.from_key(deployer_private_key)
            validate_address(account.address)
        except Exception as e:
            raise typer.BadParameter(f"Invalid VAULT_DEPLOYER_PRIVATE_KEY: {e}")

        validate_performance_fee(performance_fee)
        validate_management_fee(management_fee)

        if not config.is_system_idle():
            raise typer.BadParameter(
                "System is not idle. Cannot deploy vault at this time."
            )

        account = self.w3.eth.account.from_key(deployer_private_key)
        nonce = self.w3.eth.get_transaction_count(account.address)

        # Estimate gas needed for the transaction
        gas_estimate = self.contract.functions.createVault(
            curator_address, name, symbol, fee_type, performance_fee, management_fee
        ).estimate_gas({"from": account.address, "nonce": nonce})

        # Add 20% buffer to gas estimate
        gas_limit = int(gas_estimate * 1.2)

        # TODO: add check to measure deployer ETH balance and raise error if not enough before building tx.

        tx = self.contract.functions.createVault(
            curator_address, name, symbol, fee_type, performance_fee, management_fee
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
            order_intent: Dictionary mapping token addresses to values
            curator_private_key: Private key for signing the transaction

        Returns:
            TransactionResult
        """
        if not curator_private_key:
            curator_private_key = os.getenv("CURATOR_PRIVATE_KEY")

        account = self.w3.eth.account.from_key(curator_private_key)
        nonce = self.w3.eth.get_transaction_count(account.address)

        items = [
            {"token": Web3.to_checksum_address(token), "value": value}
            for token, value in order_intent.items()
        ]

        # Estimate gas needed for the transaction
        gas_estimate = self.contract.functions.submitIntent(items).estimate_gas(
            {"from": account.address, "nonce": nonce}
        )

        # Add 20% buffer to gas estimate
        gas_limit = int(gas_estimate * 1.2)

        tx = self.contract.functions.submitIntent(items).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": gas_limit,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        signed = account.sign_transaction(tx)
        # TODO: use tenacity to retry transaction if it fails with TimeExhausted is not in the chain after 120 seconds. True for all "send_raw_transaction" calls.
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
