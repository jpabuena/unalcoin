from dataclasses import dataclass, field, asdict
from datetime import datetime
from json import dumps
from hashlib import sha256
from .transaction import Transaction


@dataclass(frozen=True)
class Block:
    """
    Bloque dentro de la blockchain
    """

    index: int
    transactions: tuple[Transaction, ...]
    previous_hash: str
    nonce: int
    timestamp: datetime
    hash: str
