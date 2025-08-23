"""Setup script for the Orion Finance Python SDK."""

import os
import urllib.request

from setuptools import setup
from setuptools.command.build_py import build_py


class CustomBuild(build_py):
    """Download the Orion Finance contracts ABIs."""

    def run(self):
        """Run the build process."""
        self.download_abis()
        super().run()

    def download_abis(self):
        """Download the Orion Finance contracts ABIs."""
        subfolders_abis = [
            "",
            "factories",
            "factories",
            "vaults",
            "vaults",
        ]

        abis = [
            "OrionConfig",
            "TransparentVaultFactory",
            "EncryptedVaultFactory",
            "OrionTransparentVault",
            "OrionEncryptedVault",
        ]
        os.makedirs("src/abis", exist_ok=True)

        base_url = "https://raw.githubusercontent.com/OrionFinanceAI/protocol/main/artifacts/contracts"

        for i, contract in enumerate(abis):
            url = f"{base_url}/{subfolders_abis[i]}/{contract}.sol/{contract}.json"
            dest = f"src/abis/{contract}.json"
            print(f"Downloading {contract} ABI...")
            urllib.request.urlretrieve(url, dest)


setup(
    cmdclass={
        "build_py": CustomBuild,
    }
)
