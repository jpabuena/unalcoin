from dataclasses import dataclass, field, asdict

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

from blockchain.exceptions import BlockchainError
from .utils import get_timestamp
from .transaction import Transaction
from .block import Block
from json import dumps
from hashlib import sha256
from datetime import datetime
from crypto.hash import calculate_hash


@dataclass
class BlockBuilder:
    """
    Clase auxiliar que se encarga de crear un bloque inmutable para
    agregar a la cadena. Esta permite agregar transacciones.
    """

    index: int
    transactions: list[Transaction]
    previous_hash: str

    # el timestamp corresponde al momento de creación del bloque
    timestamp: datetime = field(default_factory=get_timestamp, init=False)

    def add_transaction(self, tx: Transaction):
        # recuperar la clave publica del sender
        try:
            pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(tx.sender))
        except ValueError:
            raise ValueError()

        if tx.signature:
            try:
                pk.verify(bytes.fromhex(tx.signature), tx.to_bytes())
            except InvalidSignature:
                raise BlockchainError("Error al añadir la transaccion", "La firma de la transaccion es invalida")
        else:
            raise BlockchainError("Error al añadir la transaccion", "La transaccion no se encuentra firmada")

        # todo ok
        self.transactions.append(
            tx
        )

    def mine(self, difficulty: int):
        """
        Metodo de "Proof Of Work" para minar el bloque.

        Se buscara encontrar mediante distintos nonce aquel hash que empieze
        con tantos 0's como "difficulty" lo establezca. Es decir, si difficulty
        es 4 el nonce que "mina" el bloque es aquel que produce un hash de la
        forma "0000...".
        """

        target = "0" * difficulty

        # construimos el contenido a hashear, sin el campo hash
        data = asdict(self)

        # nonce para el minado del bloque
        data["nonce"] = 0

        computed_hash = calculate_hash(data)
        while not computed_hash.startswith(target):
            # le sumamos uno al nonce y recalculamos el hash
            data["nonce"] += 1

            computed_hash = calculate_hash(data)

        # una vez se mina el bloque se procede a crear el mismo inmutable
        return Block(
            self.index,
            tuple(self.transactions),
            self.previous_hash,
            data["nonce"],
            self.timestamp,
            computed_hash,
        )
