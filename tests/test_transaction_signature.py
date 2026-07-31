from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "src" / "blockchain"))

from unalcoin.crypto.signature import verify_signature
from unalcoin.system.wallet import Wallet


class TransactionSignatureTests(unittest.TestCase):
    def test_sign_assigns_signature_and_verifies_with_sender_public_key(self):
        sender = Wallet()
        recipient = Wallet()
        tx = sender.create_transaction(recipient.pk.public_bytes_raw().hex(), 5.0)

        sender.sign(tx)

        self.assertIsNotNone(tx.signature)
        self.assertTrue(verify_signature(tx, sender.pk))

    def test_signature_becomes_invalid_after_transaction_tampering(self):
        sender = Wallet()
        recipient = Wallet()
        tx = sender.create_transaction(recipient.pk.public_bytes_raw().hex(), 7.0)
        sender.sign(tx)

        object.__setattr__(tx, "amount", 8.0)

        self.assertFalse(verify_signature(tx, sender.pk))

    def test_verify_signature_accepts_valid_signature_bytes(self):
        sender = Wallet()
        recipient = Wallet()
        tx = sender.create_transaction(recipient.pk.public_bytes_raw().hex(), 2.0)
        tx.assign_sign(sender.sk.sign(tx.to_bytes()).hex())

        self.assertTrue(verify_signature(tx, sender.pk))


if __name__ == "__main__":
    unittest.main()
