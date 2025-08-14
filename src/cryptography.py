"""Encryption operations for the Orion Python SDK."""


def encrypt_order_intent(order_intent: dict) -> dict:
    """Encrypt an order intent."""
    # Encrypted amounts — amounts are expected to be already encoded as euint32 from TFHE
    # TODO: before bindings building, assess the compatibility of tenseal/tfhe-rs+py03 and fhevm-solidity.
    # TODO: int > euint32 > bytes.
    # py03 + https://github.com/zama-ai/tfhe-rs
    # items = [{"token": Web3.to_checksum_address(t), "amount": a} for t, a in order_intent.items()]
    # func = contract.functions.submitIntent
    return order_intent
