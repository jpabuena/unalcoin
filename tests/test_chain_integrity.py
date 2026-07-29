from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "src" / "blockchain"))

from blockchain.blockchain import Blockchain
from blockchain.block_builder import BlockBuilder
from blockchain.exceptions import BlockchainError


class ChainIntegrityTests(unittest.TestCase):
    def test_accepts_validly_linked_blocks(self):
        chain = Blockchain(difficulty=1)

        block_1 = BlockBuilder(
            index=chain.length,
            transactions=[],
            previous_hash=chain.last_block.hash,
        ).mine(chain.difficulty)
        chain.add_block(block_1)

        block_2 = BlockBuilder(
            index=chain.length,
            transactions=[],
            previous_hash=chain.last_block.hash,
        ).mine(chain.difficulty)
        chain.add_block(block_2)

        self.assertTrue(chain.verify_chain())

    def test_rejects_block_with_wrong_previous_hash(self):
        chain = Blockchain(difficulty=1)

        invalid_block = BlockBuilder(
            index=chain.length,
            transactions=[],
            previous_hash="hash_invalido",
        ).mine(chain.difficulty)

        with self.assertRaises(BlockchainError):
            chain.add_block(invalid_block)

    def test_rejects_block_with_non_sequential_index(self):
        chain = Blockchain(difficulty=1)

        invalid_block = BlockBuilder(
            index=chain.length + 1,
            transactions=[],
            previous_hash=chain.last_block.hash,
        ).mine(chain.difficulty)

        with self.assertRaises(BlockchainError):
            chain.add_block(invalid_block)

    def test_detects_tampering_in_previous_hash_link(self):
        chain = Blockchain(difficulty=1)

        block_1 = BlockBuilder(
            index=chain.length,
            transactions=[],
            previous_hash=chain.last_block.hash,
        ).mine(chain.difficulty)
        chain.add_block(block_1)

        block_2 = BlockBuilder(
            index=chain.length,
            transactions=[],
            previous_hash=chain.last_block.hash,
        ).mine(chain.difficulty)
        chain.add_block(block_2)

        object.__setattr__(chain._chain[2], "previous_hash", "enlace_roto")

        self.assertFalse(chain.verify_chain())


if __name__ == "__main__":
    unittest.main()
