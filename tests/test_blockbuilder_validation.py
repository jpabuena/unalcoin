from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "src" / "blockchain"))

from unalcoin.blockchain.block_builder import BlockBuilder
from unalcoin.blockchain.exceptions import BlockBuilderError
from unalcoin.system.wallet import Wallet


class BlockBuilderValidationTests(unittest.TestCase):
    def test_add_transaction_rejects_unsigned_transaction(self):
        sender = Wallet()
        recipient = Wallet()
        tx = sender.create_transaction(recipient.pk.public_bytes_raw().hex(), 3.0)

        builder = BlockBuilder(index=1, previous_hash="abc")

        with self.assertRaises(BlockBuilderError):
            builder.add_transaction(tx)

    def test_mine_rejects_invalid_transaction_in_lot(self):
        sender = Wallet()
        recipient = Wallet()
        tx = sender.create_transaction(recipient.pk.public_bytes_raw().hex(), 2.0)
        sender.sign(tx)
        object.__setattr__(tx, "amount", 9.0)

        builder = BlockBuilder(index=1, previous_hash="abc")
        builder.transactions.append(tx)

        with self.assertRaises(BlockBuilderError):
            builder.mine(difficulty=1)


if __name__ == "__main__":
    unittest.main()
