"""Encryption operations for the Orion Finance Python SDK."""

import json
import os
import subprocess

from .utils import validate_env_var


def encrypt_order_intent(order_intent: dict[str, int]) -> tuple[dict[str, bytes], str]:
    """Encrypt an order intent."""
    # TODO: bring back this check after npm package is published.
    # if not check_orion_finance_sdk_installed():
    #     print_installation_guide()
    #     sys.exit(1)

    curator_address = os.getenv("CURATOR_ADDRESS")
    validate_env_var(
        curator_address,
        error_message=(
            "CURATOR_ADDRESS environment variable is missing or invalid. "
            "Please set CURATOR_ADDRESS in your .env file or as an environment variable. "
        ),
    )
    vault_address = os.getenv("ORION_VAULT_ADDRESS")
    validate_env_var(
        vault_address,
        error_message=(
            "ORION_VAULT_ADDRESS environment variable is missing or invalid. "
            "Please set ORION_VAULT_ADDRESS in your .env file or as an environment variable. "
        ),
    )

    tokens = [token for token in order_intent.keys()]
    values = [value for value in order_intent.values()]

    payload = {
        "vaultAddress": vault_address,
        "curatorAddress": curator_address,
        "values": values,
    }

    result = subprocess.run(
        ["npm", "run", "start"],
        cwd="../orion-finance-sdk-js/",
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    # TODO: call @orion-finance/sdk npm package.

    stdout = result.stdout.strip()
    json_start = stdout.find("{")
    json_str = stdout[json_start:]
    data = json.loads(json_str)

    encrypted_values = data["encryptedValues"]

    encrypted_intent = dict(zip(tokens, encrypted_values))

    input_proof = data["inputProof"]

    return encrypted_intent, input_proof


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
