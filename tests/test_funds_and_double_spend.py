from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "src" / "blockchain"))

from blockchain.blockchain import Blockchain
from blockchain.block_builder import BlockBuilder
from blockchain.exceptions import BlockchainError
from system.wallet import Wallet


class FundsAndDoubleSpendTests(unittest.TestCase):
    def setUp(self):
        self.alice = Wallet()
        self.bob = Wallet()
        self.alice_address = self.alice.pk.public_bytes_raw().hex()

        # Estado inicial académico: Alice arranca con 10 monedas confirmadas.
        def patched_balance(this, address: str):
            return 10.0 if address == self.alice_address else 0.0

        self.balance_patcher = patch.object(Blockchain, "get_balance", patched_balance)
        self.balance_patcher.start()
        self.chain = Blockchain(difficulty=1)

    def tearDown(self):
        self.balance_patcher.stop()

    def test_rejects_transaction_with_insufficient_funds(self):
        tx = self.alice.create_transaction(self.bob.pk.public_bytes_raw().hex(), 15.0)
        self.alice.sign(tx)

        builder = BlockBuilder(
            index=self.chain.length,
            previous_hash=self.chain.last_block.hash,
        )
        builder.add_transaction(tx)
        candidate = builder.mine(self.chain.difficulty)

        self.assertFalse(self.chain.validate_transactions_lot(candidate))

    def test_rejects_double_spend_in_same_lot(self):
        tx1 = self.alice.create_transaction(self.bob.pk.public_bytes_raw().hex(), 7.0)
        tx2 = self.alice.create_transaction(self.bob.pk.public_bytes_raw().hex(), 5.0)
        self.alice.sign(tx1)
        self.alice.sign(tx2)

        builder = BlockBuilder(
            index=self.chain.length,
            previous_hash=self.chain.last_block.hash,
        )
        builder.add_transaction(tx1)
        builder.add_transaction(tx2)
        candidate = builder.mine(self.chain.difficulty)

        self.assertFalse(self.chain.validate_transactions_lot(candidate))

    def test_add_block_rejects_invalid_lot_by_funds(self):
        tx = self.alice.create_transaction(self.bob.pk.public_bytes_raw().hex(), 15.0)
        self.alice.sign(tx)

        builder = BlockBuilder(
            index=self.chain.length,
            previous_hash=self.chain.last_block.hash,
        )
        builder.add_transaction(tx)
        candidate = builder.mine(self.chain.difficulty)

        with self.assertRaises(BlockchainError):
            self.chain.add_block(candidate)

    def test_accepts_lot_when_total_spend_is_within_balance(self):
        tx1 = self.alice.create_transaction(self.bob.pk.public_bytes_raw().hex(), 4.0)
        tx2 = self.alice.create_transaction(self.bob.pk.public_bytes_raw().hex(), 6.0)
        self.alice.sign(tx1)
        self.alice.sign(tx2)

        builder = BlockBuilder(
            index=self.chain.length,
            previous_hash=self.chain.last_block.hash,
        )
        builder.add_transaction(tx1)
        builder.add_transaction(tx2)
        candidate = builder.mine(self.chain.difficulty)

        self.assertTrue(self.chain.validate_transactions_lot(candidate))
        self.chain.add_block(candidate)
        self.assertEqual(self.chain.length, 2)


if __name__ == "__main__":
    unittest.main()
