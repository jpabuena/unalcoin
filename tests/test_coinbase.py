from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "src" / "blockchain"))

from unalcoin.blockchain.blockchain import Blockchain
from unalcoin.blockchain.block_builder import BlockBuilder
from unalcoin.blockchain.coinbase import CoinbaseTransaction
from unalcoin.blockchain.exceptions import BlockchainError
from unalcoin.system.wallet import Wallet


class CoinbaseTests(unittest.TestCase):
    def setUp(self):
        self.chain = Blockchain(difficulty=1, mining_reward=50.0)
        self.miner = Wallet()
        self.miner_addr = self.miner.pk.public_bytes_raw().hex()

    def _mine_with_coinbase(self, recipient: str, amount: float = 50.0):
        builder = BlockBuilder(
            index=self.chain.length,
            previous_hash=self.chain.last_block.hash,
        )
        builder.set_coinbase(recipient, amount)
        return builder.mine(self.chain.difficulty)

    def test_coinbase_credits_miner_balance(self):
        block = self._mine_with_coinbase(self.miner_addr)
        self.chain.add_block(block)
        self.assertEqual(self.chain.get_balance(self.miner_addr), 50.0)

    def test_coinbase_must_be_first_transaction(self):
        """Coinbase en posicion != 0 debe invalidar el lote."""
        alice = Wallet()
        alice_addr = alice.pk.public_bytes_raw().hex()

        # Give alice some balance via a valid coinbase block first
        first_block = self._mine_with_coinbase(alice_addr, 50.0)
        self.chain.add_block(first_block)

        # Build a block where a regular tx comes before a coinbase
        regular_tx = alice.create_transaction(self.miner_addr, 5.0)
        alice.sign(regular_tx)
        builder = BlockBuilder(
            index=self.chain.length,
            previous_hash=self.chain.last_block.hash,
        )
        builder.add_transaction(regular_tx)
        block = builder.mine(self.chain.difficulty)

        # Manually inject a coinbase at position 1
        coinbase = CoinbaseTransaction(recipient=self.miner_addr, amount=50.0)
        tampered = block.__class__(
            block.index,
            block.transactions + (coinbase,),
            block.previous_hash,
            block.nonce,
            block.timestamp,
            block.hash,
        )
        self.assertFalse(self.chain.validate_transactions_lot(tampered))

    def test_coinbase_wrong_amount_rejected(self):
        block = self._mine_with_coinbase(self.miner_addr, amount=9999.0)
        self.assertFalse(self.chain.validate_transactions_lot(block))
        with self.assertRaises(BlockchainError):
            self.chain.add_block(block)

    def test_blocks_without_coinbase_still_valid(self):
        """Los bloques sin coinbase (como en las pruebas existentes) siguen siendo válidos."""
        builder = BlockBuilder(
            index=self.chain.length,
            previous_hash=self.chain.last_block.hash,
        )
        block = builder.mine(self.chain.difficulty)
        self.chain.add_block(block)
        self.assertEqual(self.chain.length, 2)

    def test_miner_can_spend_coinbase_reward(self):
        recipient = Wallet()
        recipient_addr = recipient.pk.public_bytes_raw().hex()

        # Mine a block to get coins
        block1 = self._mine_with_coinbase(self.miner_addr)
        self.chain.add_block(block1)

        # Spend part of the reward
        tx = self.miner.create_transaction(recipient_addr, 20.0)
        self.miner.sign(tx)
        builder = BlockBuilder(
            index=self.chain.length,
            previous_hash=self.chain.last_block.hash,
        )
        builder.add_transaction(tx)
        block2 = builder.mine(self.chain.difficulty)
        self.chain.add_block(block2)

        self.assertEqual(self.chain.get_balance(self.miner_addr), 30.0)
        self.assertEqual(self.chain.get_balance(recipient_addr), 20.0)


if __name__ == "__main__":
    unittest.main()
