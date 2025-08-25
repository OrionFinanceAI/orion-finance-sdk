const { createInstance, SepoliaConfig } = require('@zama-fhe/relayer-sdk/node');

async function main() {
  const input = await new Promise((resolve) => {
    let data = '';
    process.stdin.on('data', (chunk) => (data += chunk));
    process.stdin.on('end', () => resolve(JSON.parse(data)));
  });

  const { vaultAddress, curatorAddress, values } = input;

  const instance = await createInstance(SepoliaConfig);

  // Create a buffer for all values to encrypt
  const encryptedBuffer = instance.createEncryptedInput(
    vaultAddress,
    curatorAddress,
  );

  for (const value of values) {
    encryptedBuffer.add32(value);
  }

  // Encrypt intent values
  const encryptedCiphertexts = await encryptedBuffer.encrypt();

  // Convert proof and handles to hex
  const handlesHex = encryptedCiphertexts.handles.map(
    (h) => '0x' + Buffer.from(h).toString('hex'),
  );
  const inputProofHex =
    '0x' + Buffer.from(encryptedCiphertexts.inputProof).toString('hex');

  console.log(
    JSON.stringify({ encryptedValues: handlesHex, inputProof: inputProofHex }),
  );
}

main().catch((err) => {
  console.error('Error:', err);
  process.exit(1);
});
