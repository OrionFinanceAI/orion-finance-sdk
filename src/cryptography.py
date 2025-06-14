"""Encryption operations for the Orion Python SDK."""

import tenseal as ts


def run_keygen():
    """Generate keys for the FHE operations."""
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    context.generate_galois_keys()
    context.generate_relin_keys()
    context.global_scale = 2**40

    public_context = context.copy()
    public_context.make_context_public()
    with open("context.public.tenseal", "wb") as f:
        f.write(public_context.serialize())

    with open("context.secret.tenseal", "wb") as f:
        f.write(context.serialize(save_secret_key=True))

    print("✅ Keys generated and saved.")


def encrypt_order_intent(order_intent: dict[str, int]) -> dict:
    """Encrypt the data on the client."""
    with open("context.public.tenseal", "rb") as f:
        public_context = ts.context_from(f.read())

    encrypted_dict = {}
    for key, value in order_intent.items():
        encrypted_dict[key] = ts.ckks_vector(public_context, [value]).serialize()

    # Encrypted amounts — amounts are expected to be already encoded as euint32 from TFHE
    # TODO: before bindings building, assess the compatibility of tenseal/tfhe-rs+py03 and fhevm-solidity.
    # TODO: int > euint32 > bytes.
    # py03 + https://github.com/zama-ai/tfhe-rs
    # items = [{"token": Web3.to_checksum_address(t), "amount": a} for t, a in order_intent.items()]
    # func = contract.functions.submitOrderIntentEncrypted

    breakpoint()

    return encrypted_dict


def compute_server_evaluation():
    """Compute the result of the compute server evaluation."""
    with open("context.public.tenseal", "rb") as f:
        public_context = ts.context_from(f.read())

    with open("encrypted_data.bin", "rb") as f:
        enc_vector = ts.ckks_vector_from(public_context, f.read())

    enc_result = enc_vector * 10

    with open("encrypted_result.bin", "wb") as f:
        f.write(enc_result.serialize())

    print("🧮 Compute server applied computation.")


def decryptor_decrypt():
    """Decrypt the result of the compute server evaluation."""
    with open("context.secret.tenseal", "rb") as f:
        secret_context = ts.context_from(f.read())

    with open("encrypted_result.bin", "rb") as f:
        enc_result = ts.ckks_vector_from(secret_context, f.read())

    result = enc_result.decrypt(secret_key=secret_context.secret_key())
    print("🔓 Decrypted result:", result)
