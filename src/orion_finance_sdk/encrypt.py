"""Encryption operations for the Orion Finance Python SDK."""

import subprocess
import sys


def check_npm_available() -> bool:
    """Check if npm is available on the system."""
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def check_orion_finance_sdk_installed() -> bool:
    """Check if @orion-finance/sdk npm package is installed."""
    if not check_npm_available():
        return False

    try:
        result = subprocess.run(
            ["npm", "list", "@orion-finance/sdk"],
            capture_output=True,
            text=True,
            check=False,
        )

        return result.returncode == 0 and "empty" not in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def print_installation_guide():
    """Print installation guide for @orion-finance/sdk."""
    print("=" * 80)
    print(
        "ERROR: Curation of Encrypted Vaults requires the @orion-finance/sdk npm package."
    )
    print("=" * 80)
    print()

    if not check_npm_available():
        print("npm is not available on your system.")
        print("Please install Node.js and npm first:")
        print()
        print("  Visit: https://nodejs.org/")
        print("  OR use a package manager:")
        print("    macOS: brew install node")
        print("    Ubuntu/Debian: sudo apt install nodejs npm")
        print("    Windows: Download from https://nodejs.org/")
        print()
    print("To install the required npm package, run one of the following commands:")
    print()
    print("  npm install @orion-finance/sdk")
    print("  # OR")
    print("  yarn add @orion-finance/sdk")
    print("  # OR")
    print("  pnpm add @orion-finance/sdk")
    print()

    print(
        "For more information, visit: https://www.npmjs.com/package/@orion-finance/sdk"
    )
    print("=" * 80)


def encrypt_order_intent(order_intent: dict) -> dict:
    """Encrypt an order intent."""
    if not check_orion_finance_sdk_installed():
        print_installation_guide()
        sys.exit(1)

    # TODO: call @orion-finance/sdk subprocess, capture output.
    # TODO: return encrypted order intent.
    raise NotImplementedError("Encryption not implemented yet.")
