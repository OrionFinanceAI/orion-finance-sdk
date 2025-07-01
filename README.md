# orion-sdk [![Github Actions][gha-badge]][gha]

[gha]: https://github.com/OrionFinanceAI/orion-sdk/actions
[gha-badge]: https://github.com/OrionFinanceAI/orion-sdk/actions/workflows/build.yml/badge.svg

## About

A Python Software Development Kit (SDK) to ease interactions with the Orion protocol and its Vaults. This repository provides tools and utilities for developers to seamlessly integrate with Orion's [portfolio management infrastructure](https://github.com/OrionFinanceAI/protocol).

## Licences

The license for Orion is the MIT License given in [`LICENSE`](./LICENSE).

## Installation

```bash
make venv
source .venv/bin/activate
make install
```

For development installation, use the following command instead:

```bash
make install-dev
```

## Examples of Usage

```bash
# List available commands
orion --help

# Deploy a new Orion transparent vault
source .env && orion deploy-orion-transparent-vault --name "Vault 0" --symbol "V0"
# Use off-chain stack to generate an order intent
echo '{"0x0692d38F0da545D08d5101aC09AA4139D121F127": 0.42, "0x3d99435E5531b47267739755D7c91332a0304905": 0.58}' > order_intent.json
# Submit the order intent to the Orion vault
source .env && orion submit-order plain --order-intent-path order_intent.json
```

## Order Intent Input Format

The SDK supports providing order intents as a JSON file.
