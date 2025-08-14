"""Command line interface for the Orion Python SDK."""

import json

import typer

from .contracts import (
    OrionEncryptedVault,
    OrionTransparentVault,
    OrionVaultFactory,
)
from .cryptography import encrypt_order_intent
from .utils import validate_order

app = typer.Typer()
submit_order_app = typer.Typer()
app.add_typer(submit_order_app, name="submit-order")


@app.command()
def deploy_orion_transparent_vault(
    name: str = typer.Option(..., help="Name of the vault"),
    symbol: str = typer.Option(..., help="Symbol of the vault"),
):
    """Deploy the OrionTransparentVault contract."""
    orion_vault_factory = OrionVaultFactory()
    tx_result = orion_vault_factory.create_orion_transparent_vault(
        name=name, symbol=symbol
    )
    print(f"Transaction hash: {tx_result.tx_hash}")
    print(f"Decoded logs: {tx_result.decoded_logs}")


@submit_order_app.command()
def plain(
    order_intent_path: str = typer.Option(
        ..., help="Path to JSON file containing order intent"
    ),
) -> None:
    """Submit a plain order intent."""
    # JSON file input
    with open(order_intent_path, "r") as f:
        order_intent_dict = json.load(f)

    validated_order_intent = validate_order(order_intent=order_intent_dict, fuzz=False)

    orion_vault = OrionTransparentVault()
    tx_result = orion_vault.submit_order_intent(order_intent=validated_order_intent)
    print(f"Transaction hash: {tx_result.tx_hash}")
    print(f"Decoded logs: {tx_result.decoded_logs}")


@submit_order_app.command()
def encrypted(
    portfolio_path: str = typer.Option(..., help="Path to the portfolio parquet file"),
    fuzz: bool = typer.Option(False, help="Fuzz the order intent"),
) -> None:
    """Submit an encrypted order intent."""
    # Mock to test fuzzer.
    order_intent_dict = {"0xd81eaae8e6195e67695be9ac447c9d6214cb717a": 1}

    validated_order_intent = validate_order(order_intent=order_intent_dict, fuzz=fuzz)

    encrypted_order_intent = encrypt_order_intent(order_intent=validated_order_intent)

    orion_vault = OrionEncryptedVault()

    raise NotImplementedError
