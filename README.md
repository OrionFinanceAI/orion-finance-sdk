# orion-finance-sdk [![Github Actions][gha-badge]][gha]

[gha]: https://github.com/OrionFinanceAI/orion-finance-sdk/actions
[gha-badge]: https://github.com/OrionFinanceAI/orion-finance-sdk/actions/workflows/build.yml/badge.svg

## About

A Python Software Development Kit (SDK) to ease interactions with the Orion Finance protocol and its Vaults. This repository provides tools and utilities for quants and developers to seamlessly integrate with Orion's [portfolio management on-chain infrastructure](https://github.com/OrionFinanceAI/protocol).

For additional information, please refer to the [Orion documentation](https://docs.orionfinance.ai), and the curator section in particular.

## Licence

This software is distributed under the BSD-3-Clause license. See the [`LICENSE`](./LICENSE) file for the full text.

## Installation

### From PyPI (Recommended)

Install the latest stable version from PyPI:

```bash
pip install orion-finance-sdk
```

### From Source

For development or to install the latest development version:

```bash
# Clone the repository
git clone https://github.com/OrionFinanceAI/orion-finance-sdk.git
cd orion-finance-sdk

# Using uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -e .
```

Or using make:

```bash
make uv-download
make venv
source .venv/bin/activate
make install
```

## Environment Variables Setup

The SDK requires the user to specify an `RPC_URL` environment variable in the `.env` file of the project. Follow the [SDK Installation](https://docs.orionfinance.ai/curator/orion_sdk/install) to get one.

Based on the usage, additional environment variables may be required, e.g.:
- `CURATOR_ADDRESS`: The address of the curator account.
- `VAULT_DEPLOYER_PRIVATE_KEY`: The private key of the vault deployer account.
- `CURATOR_PRIVATE_KEY`: The private key of the curator account.
- `ORION_VAULT_ADDRESS`: The address of the Orion vault.

## Examples of Usage

### List available commands

```bash
orion --help
orion deploy-vault --help
orion submit-order --help
```

### Deploy a new Transparent Orion vault

```bash
orion deploy-vault --vault-type transparent --name "Algorithmic Liquidity Provision & Hedging Agent" --symbol "ALPHA" --fee-type hard_hurdle --performance-fee 10 --management-fee 1
```

### Deploy a new Encrypted Orion vault

```bash
orion deploy-vault --vault-type encrypted --name "Quantitative Uncertainty Analysis of Network Topologies" --symbol "QUANT" --fee-type high_water_mark --performance-fee 0 --management-fee 2
```

### Submit an order intent to a vault

```bash
# Use off-chain stack to generate an order intent
echo '{"0x5BA134aBc8BA11Cf7868F4Dfb02497A3f1544Eb5": 0.25, "0x490a81a1939762E6AA87C68C346A0be5E21B466c": 0.02, "0x8A359aAfbf0DF440B34bb97445d981C1944CD053": 0.015, "0xbD39EeAd46c3f28EB8309A74641ab9Ef947FFc83": 0.0255, "0x6b2741F97Ea3EA9C5bFeEa33575d1E73c4481010": 0.06, "0x58f7aaE7B2c017F74B7403C9e89537f43B13bE87": 0.40, "0x28345814d210f2FE11C8de03236f0Ba7b603D282": 0.22, "0x484fF4FB5Ca053b47e5e0490C363b5ea38bB2adF": 0.0095}' > order_intent.json

# Submit the order intent to the Orion vault
orion submit-order --order-intent-path order_intent.json
```
