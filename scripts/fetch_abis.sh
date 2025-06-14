mkdir -p abis/

contracts=(
    OrionConfig
    OrionVaultFactory
    OrionTransparentVault
)

# TODO: point to main branch after protocol merge.
for contract in "${contracts[@]}"; do
    curl -sSL "https://raw.githubusercontent.com/OrionFinanceAI/protocol/dev/artifacts/contracts/${contract}.sol/${contract}.json" \
        -o "abis/${contract}.json"
done
# TODO: move this into setup/toml for pypi distribution support.
