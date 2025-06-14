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

## Examples of Usage

```bash
# List available commands
orion --help

# Submit an order intent
orion order-intent --portfolio-path ../portfolio-manager/output/optimized/1.parquet
```
