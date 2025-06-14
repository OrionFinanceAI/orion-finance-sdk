mkdir -p abis/

contracts=(
    OrionConfig
    OrionVaultFactory
    OrionVault
)

# TODO: point to main branch after protocol merge.
for contract in "${contracts[@]}"; do
    curl -sSL "https://raw.githubusercontent.com/OrionFinanceAI/protocol/dev/artifacts/contracts/${contract}.sol/${contract}.json" \
        -o "abis/${contract}.json"
done
