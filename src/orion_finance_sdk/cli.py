"""Command line interface for the Orion Finance Python SDK."""

import json
import os

import typer

from .contracts import (
    OrionEncryptedVault,
    OrionTransparentVault,
    VaultFactory,
)
from .encrypt import encrypt_order_intent
from .types import (
    FeeType,
    VaultType,
    fee_type_to_int,
)
from .utils import format_transaction_logs, validate_order

app = typer.Typer()


@app.command()
def deploy_vault(
    vault_type: VaultType = typer.Option(
        ..., help="Type of the vault (encrypted or transparent)"
    ),
    name: str = typer.Option(..., help="Name of the vault"),
    symbol: str = typer.Option(..., help="Symbol of the vault"),
    fee_type: FeeType = typer.Option(..., help="Type of the fee"),
    performance_fee: int = typer.Option(..., help="Performance fee in basis points"),
    management_fee: int = typer.Option(..., help="Management fee in basis points"),
):
    """Deploy an Orion vault with customizable fee structure, name, and symbol. The vault can be either transparent or encrypted."""
    fee_type = fee_type_to_int[fee_type.value]

    vault_factory = VaultFactory(vault_type=vault_type.value)

    tx_result = vault_factory.create_orion_vault(
        name=name,
        symbol=symbol,
        fee_type=fee_type,
        performance_fee=performance_fee,
        management_fee=management_fee,
    )

    # Format transaction logs
    format_transaction_logs(tx_result, "Vault deployment transaction completed!")

    # Extract vault address if available
    vault_address = vault_factory.get_vault_address_from_result(tx_result)
    if vault_address:
        print(
            f"\n📍 Vault address: {vault_address} <------------------- ADD THIS TO YOUR .env FILE TO INTERACT WITH THE VAULT."
        )
    else:
        print("\n❌ Could not extract vault address from transaction")


@app.command()
def submit_order(
    order_intent_path: str = typer.Option(
        ..., help="Path to JSON file containing order intent"
    ),
    vault_address: str | None = typer.Option(None, help="Address of the Orion vault"),
    fuzz: bool = typer.Option(False, help="Fuzz the order intent"),
) -> None:
    """Submit an order intent to an Orion vault. The order intent can be either transparent or encrypted."""
    if not vault_address:
        vault_address = os.getenv("ORION_VAULT_ADDRESS")
        if not vault_address:
            raise ValueError(
                "Vault address must be provided either as parameter or ORION_VAULT_ADDRESS environment variable."
            )

    from .contracts import OrionConfig

    config = OrionConfig()

    if vault_address in config.orion_transparent_vaults:
        encrypt = False
        fuzz = False
        vault = OrionTransparentVault()
    elif vault_address in config.orion_encrypted_vaults:
        encrypt = True
        vault = OrionEncryptedVault()
    else:
        raise ValueError(
            f"Vault address {vault_address} not found in OrionConfig contract."
        )

    # JSON file input
    with open(order_intent_path, "r") as f:
        order_intent = json.load(f)

    validated_order_intent = validate_order(order_intent=order_intent, fuzz=fuzz)

    if encrypt:
        validated_order_intent = encrypt_order_intent(
            order_intent=validated_order_intent
        )

    tx_result = vault.submit_order_intent(order_intent=validated_order_intent)

    # Format transaction logs
    format_transaction_logs(tx_result, "Order intent submitted successfully!")
