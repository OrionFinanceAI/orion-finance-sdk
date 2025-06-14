"""Command line interface for the Orion Python SDK."""

import pandas as pd
import typer

from .contracts import OrionConfig, OrionTransparentVault, OrionVaultFactory
from .fhe import run_keygen
from .ipfs import download_public_context, upload_to_ipfs
from .utils import validate_order

app = typer.Typer()

# === Functions associated with protocol Deployer ===


@app.command()
def upload(path: str):
    """Upload a file to IPFS."""
    url, cid = upload_to_ipfs(path)
    print(f"Uploaded to IPFS: {url}")
    print(f"CID: {cid}")


@app.command()
def keygen():
    """Generate FHE keys."""
    run_keygen()


# === Functions associated with Curator ===


@app.command()
def download():
    """Download the public TenSEAL context from a given Lighthouse URL."""
    orion_config = OrionConfig()
    fhe_public_cid = orion_config.fhe_public_cid
    url = "https://gateway.lighthouse.storage/ipfs/" + fhe_public_cid
    download_public_context(url)


@app.command()
def deploy_orion_vault():
    """Deploy the OrionTransparentVault contract."""
    orion_vault_factory = OrionVaultFactory()
    tx_result = orion_vault_factory.create_orion_vault()
    print(f"Transaction hash: {tx_result.tx_hash}")
    print(f"Decoded logs: {tx_result.decoded_logs}")


# TODO: orion subit-order plain --portfoliopath <path>
# TODO: orion submit-order encrypted --portfoliopath <path> --fuzz
# fuzz: bool = typer.Option(False, help="Fuzz the order intent"),
@app.command()
def order_intent(
    portfolio_path: str = typer.Option(..., help="Path to the portfolio parquet file"),
) -> None:
    """Submit an order intent."""
    df = pd.read_parquet(portfolio_path)

    order_intent = df.iloc[-1]
    order_intent = order_intent[order_intent != 0]

    # TODO: specific of current curator portfolio management pipeline.
    # Sdk shall be agnostic of the portfolio management pipeline.
    order_intent.index = order_intent.index.str.lower().str.replace(
        "_1", "", regex=False
    )

    order_intent_dict = order_intent.to_dict()
    validated_order_intent = validate_order(order_intent=order_intent_dict, fuzz=False)

    orion_vault = OrionTransparentVault()
    tx_result = orion_vault.submit_order_intent(order_intent=validated_order_intent)
    print(f"Transaction hash: {tx_result.tx_hash}")
    print(f"Decoded logs: {tx_result.decoded_logs}")
