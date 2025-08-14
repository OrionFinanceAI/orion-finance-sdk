# orion-sdk [![Github Actions][gha-badge]][gha]

[gha]: https://github.com/OrionFinanceAI/orion-sdk/actions
[gha-badge]: https://github.com/OrionFinanceAI/orion-sdk/actions/workflows/build.yml/badge.svg

## About

A Python Software Development Kit (SDK) to ease interactions with the Orion protocol and its Vaults. This repository provides tools and utilities for quants and developers to seamlessly integrate with Orion's [portfolio management on-chain infrastructure](https://github.com/OrionFinanceAI/protocol).

aFor additional information, please refer to the [Orion documentation](https://docs.orionfinance.ai), and the curator section in particular.

## Licences

The license for Orion is the MIT License given in [`LICENSE`](./LICENSE).

## Environment Variables Setup

```bash
cp .env.example .env
```

Visit the [Vault Deployment guide](https://docs.orionfinance.ai/curator/orion_sdk/deploy) for more information on how to set up the environment variables.

## Installation

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate
uv pip install -e .
```

or, with make:

```bash
make uv-download
make venv
source .venv/bin/activate
make install
```

## Examples of Usage

### List available commands

```bash
orion --help
orion deploy-vault --help
orion submit-order --help
```

### Deploy a new Transparent Orion vault

```bash
orion deploy-vault --vault-type transparent --name "Algorithmic Liquidity Provision & Hedging Agent" --symbol "ALPHA" --fee-type hard_hurdle --performance-fee 100 --management-fee 10
```

### Deploy a new Encrypted Orion vault

```bash
orion deploy-vault --vault-type encrypted --name "Quantitative Uncertainty Analysis of Network Topologies" --symbol "QUANT" --fee-type high_water_mark --performance-fee 0 --management-fee 20
```



# Use off-chain stack to generate an order intent
echo '{"0x0692d38F0da545D08d5101aC09AA4139D121F127": 0.42, "0x3d99435E5531b47267739755D7c91332a0304905": 0.58}' > order_intent.json
# Submit the order intent to the Orion vault
orion submit-order plain --order-intent-path order_intent.json
```

## Order Intent Input Format

The SDK supports providing order intents as a JSON file.
