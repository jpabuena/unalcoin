from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "src" / "blockchain"))

from blockchain.blockchain import Blockchain
from blockchain.block_builder import BlockBuilder
from blockchain.transaction import Transaction
from blockchain.exceptions import BlockchainError
from system.wallet import Wallet


class NonceValidationTests(unittest.TestCase):
    def setUp(self):
        self.alice = Wallet()
        self.bob = Wallet()
        self.alice_address = self.alice.pk.public_bytes_raw().hex()
        self.bob_address = self.bob.pk.public_bytes_raw().hex()

        # Aislar pruebas de nonce para que no fallen por fondos.
        def patched_balance(this, address: str):
            return 100.0 if address == self.alice_address else 0.0

        self.balance_patcher = patch.object(Blockchain, "get_balance", patched_balance)
        self.balance_patcher.start()

        self.chain = Blockchain(difficulty=1)

    def tearDown(self):
        self.balance_patcher.stop()

    def _signed_tx(self, nonce: int, amount: float = 1.0):
        tx = Transaction(self.alice_address, self.bob_address, amount, nonce)
        self.alice.sign(tx)
        return tx

    def _mine_candidate(self, txs: list[Transaction]):
        return BlockBuilder(
            index=self.chain.length,
            transactions=txs,
            previous_hash=self.chain.last_block.hash,
        ).mine(self.chain.difficulty)

    def test_accepts_sequential_nonces_in_same_block(self):
        tx0 = self._signed_tx(0, 2.0)
        tx1 = self._signed_tx(1, 3.0)

        candidate = self._mine_candidate([tx0, tx1])

        self.assertTrue(self.chain.validate_transactions_lot(candidate))

    def test_rejects_duplicate_nonce_in_same_block(self):
        tx0 = self._signed_tx(0, 2.0)
        tx0_duplicate = self._signed_tx(0, 1.0)

        candidate = self._mine_candidate([tx0, tx0_duplicate])

        self.assertFalse(self.chain.validate_transactions_lot(candidate))

    def test_rejects_nonce_gap_in_same_block(self):
        tx0 = self._signed_tx(0, 2.0)
        tx2 = self._signed_tx(2, 1.0)

        candidate = self._mine_candidate([tx0, tx2])

        self.assertFalse(self.chain.validate_transactions_lot(candidate))

    def test_rejects_replay_of_confirmed_nonce(self):
        first_tx = self._signed_tx(0, 2.0)
        first_block = self._mine_candidate([first_tx])
        self.chain.add_block(first_block)

        replay_tx = self._signed_tx(0, 1.0)
        replay_block = self._mine_candidate([replay_tx])

        self.assertFalse(self.chain.validate_transactions_lot(replay_block))
        with self.assertRaises(BlockchainError):
            self.chain.add_block(replay_block)


if __name__ == "__main__":
    unittest.main()
