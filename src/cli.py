"""Command line interface for the Orion Python SDK."""

import json

import typer

from .contracts import (
    # OrionEncryptedVault,
    # OrionTransparentVault,
    VaultFactory,
)
from .cryptography import encrypt_order_intent
from .types import (
    FeeType,
    VaultType,
    fee_type_to_int,
)
from .utils import validate_order

app = typer.Typer()
submit_order_app = typer.Typer()
app.add_typer(submit_order_app, name="submit-order")


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
    """Deploy an Orion vault."""
    fee_type = fee_type_to_int[fee_type.value]

    vault_factory = VaultFactory(vault_type=vault_type.value)

    tx_result = vault_factory.create_orion_vault(
        name=name,
        symbol=symbol,
        fee_type=fee_type,
        performance_fee=performance_fee,
        management_fee=management_fee,
    )

    print(f"✅ Transaction hash: {tx_result.tx_hash}")
    print("=" * 60)

    if tx_result.decoded_logs:
        print("📋 Transaction Events:")
        for i, log in enumerate(tx_result.decoded_logs, 1):
            print(f"\n{i}. Event: {log.get('event', 'Unknown')}")

            if log.get("args"):
                args = log["args"]
                print("   Arguments:")
                for key, value in args.items():
                    if key == "vaultType":
                        vault_type_name = "Transparent" if value == 0 else "Encrypted"
                        print(f"     {key}: {value} ({vault_type_name})")
                    else:
                        print(f"     {key}: {value}")

            print(f"   Contract: {log.get('address', 'Unknown')}")
            print(f"   Block: {log.get('blockNumber', 'Unknown')}")
    else:
        print("⚠️  No events found in transaction logs")

    print("=" * 60)

    # Extract vault address if available
    vault_address = vault_factory.get_vault_address_from_result(tx_result)
    if vault_address:
        print("\n🎉 Vault deployed successfully!")
        print(
            f"📍 Vault address: {vault_address} <------------------- ADD THIS TO YOUR .env FILE TO INTERACT WITH THE VAULT."
        )
    else:
        print("\n❌ Could not extract vault address from transaction")


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

    orion_vault = TransparentVault()
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

    orion_vault = EncryptedVault()

    raise NotImplementedError
