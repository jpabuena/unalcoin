from dataclasses import dataclass, field, asdict
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from crypto.signature import verify_signature
from blockchain.exceptions import BlockBuilderError
from .coinbase import CoinbaseTransaction
from .utils import get_timestamp
from .transaction import Transaction
from .block import Block
from datetime import datetime
from crypto.hash import calculate_hash


@dataclass
class BlockBuilder:
    """
    Clase auxiliar que se encarga de crear un bloque inmutable para
    agregar a la cadena. Esta permite agregar transacciones.
    """

    index: int
    previous_hash: str
    transactions: list[Transaction | CoinbaseTransaction] = field(init=False, default_factory=list)

    # el timestamp corresponde al momento de creación del bloque
    timestamp: datetime = field(default_factory=get_timestamp, init=False)

    def set_coinbase(self, recipient: str, amount: float):
        """
        Establece la transacción coinbase del bloque (recompensa al minero).
        Siempre se inserta en la primera posición.
        """
        coinbase = CoinbaseTransaction(recipient=recipient, amount=amount)
        self.transactions.insert(0, coinbase)

    def _validate_transaction(self, tx: Transaction | CoinbaseTransaction):
        # las transacciones coinbase no requieren firma
        if isinstance(tx, CoinbaseTransaction):
            return

        # recuperar la clave publica del sender
        try:
            pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(tx.sender))
        except ValueError:
            raise BlockBuilderError(
                "Error al validar la transaccion",
                "El emisor no tiene una clave publica valida",
            )

        if not tx.signature:
            raise BlockBuilderError(
                "Error al añadir la transaccion",
                "La transaccion no se encuentra firmada",
            )

        if not verify_signature(tx, pk):
            raise BlockBuilderError(
                "Error al añadir la transaccion",
                "La firma de la transaccion es invalida",
            )

    def add_transaction(self, tx: Transaction):
        self._validate_transaction(tx)

        # todo ok
        self.transactions.append(tx)

    def mine(self, difficulty: int):
        """
        Metodo de "Proof Of Work" para minar el bloque.

        Se buscara encontrar mediante distintos nonce aquel hash que empieze
        con tantos 0's como "difficulty" lo establezca. Es decir, si difficulty
        es 4 el nonce que "mina" el bloque es aquel que produce un hash de la
        forma "0000...".
        """
        # defensa final: validar de nuevo todo el lote antes de minar
        for tx in self.transactions:
            self._validate_transaction(tx)

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
