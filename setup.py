"""Setup script for the Orion Python SDK."""

import os
import urllib.request

from setuptools import setup
from setuptools.command.build_py import build_py


class CustomBuild(build_py):
    """Download the Orion contracts ABIs."""

    def run(self):
        """Run the build process."""
        self.download_abis()
        super().run()

    def download_abis(self):
        """Download the Orion contracts ABIs."""
        abis = ["OrionConfig", "OrionVaultFactory", "OrionTransparentVault"]
        os.makedirs("abis", exist_ok=True)
        
        is_dev = os.getenv("ORION_DEV", "false").lower() == "true"
        branch = "dev" if is_dev else "main"
        base_url = f"https://raw.githubusercontent.com/OrionFinanceAI/protocol/{branch}/artifacts/contracts"
                
        for contract in abis:
            url = f"{base_url}/{contract}.sol/{contract}.json"
            dest = f"abis/{contract}.json"
            print(f"Downloading {contract} ABI...")
            urllib.request.urlretrieve(url, dest)


setup(
    cmdclass={
        "build_py": CustomBuild,
    }
)
