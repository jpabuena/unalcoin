from dataclasses import dataclass, field, asdict
from .block import Block
from .transaction import Transaction
from .exceptions import BlockchainError
from time import time
from .block_builder import BlockBuilder
from crypto.hash import calculate_hash
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from crypto.signature import verify_signature


@dataclass(frozen=True)
class Blockchain:
    """
    Clase que representa la cadena de bloques
    """

    difficulty: int
    _chain: list[Block] = field(init=False, default_factory=list)

    # queremos proteger la cadena de la maleabilidad directa
    # para ello exponemos una tupla cuando se quiera referenciar a esta
    @property
    def chain(self):
        return tuple(self._chain)

    @property
    def length(self):
        return len(self._chain)

    @property
    def last_block(self):
        """
        El ultimo bloque agregado a la cadena
        """
        return self._chain[-1]

    def __post_init__(self):
        # crear el builder del bloque y minarlo
        genesis_block = BlockBuilder(
            0,
            [],
            "0",
        )

        # minamos el bloque
        mined_genesis_block = genesis_block.mine(self.difficulty)

        # agregamos el bloque directamente a la cadena
        self._chain.append(mined_genesis_block)

    def add_block(self, block: Block):
        if self.validate_block(
            block, self.last_block
        ) and self.validate_transactions_lot(block):
            self._chain.append(block)
        else:
            raise BlockchainError(
                "Error al agregar el bloque",
                "El bloque es invalido y no puede ser agregado a la cadena",
            )

    def validate_block(self, block: Block, previous_block: Block | None = None):
        """
        Metodo para verificar si un bloque es realmente valido
        para ser añadido a la cadena.
        """

        # primero verificar que el hash del bloque corresponda a este mismo
        data = asdict(block)
        del data["hash"]

        block_hash = calculate_hash(data)
        if block_hash != block.hash:
            return False

        # verificar que el hash cumpla con la dificultad de minado
        if not block_hash.startswith("0" * self.difficulty):
            return False

        # reglas del bloque genesis
        if block.index == 0:
            return block.previous_hash == "0"

        # para bloques no genesis debe existir un bloque previo esperado
        if previous_block is None:
            previous_block = self.last_block

        if block.previous_hash != previous_block.hash:
            return False

        if block.index != previous_block.index + 1:
            return False

        return True

    def verify_chain(self):
        """
        Metodo que verifica la integridad de la cadena, esto se refiere a mirar si cada bloque es
        correcto y ademas cumple con la propiedad de estar enlazado criptogrficamente con su bloque previo
        """
        if self.length == 0:
            return False

        # validar bloque genesis
        if not self.validate_block(self._chain[0]):
            return False

        for i in range(1, self.length):
            current_block = self._chain[i]
            previous_block = self._chain[i - 1]
            if not self.validate_block(current_block, previous_block):
                return False

        return True

    def get_balance(self, address: str):
        """
        Metodo para obtener el balance de una persona (direccion) en la cadena
        """
        balance = 0.0

        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount

        return balance

    def get_last_transactions_nonce(self, address: str):
        last = -1
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address and tx.nonce > last:
                        last = tx.nonce
        return last

    def validate_transaction(self, tx: Transaction):
        if tx.amount <= 0:
            return False
        if tx.sender == tx.recipient:
            return False
        if not tx.signature:
            return False

        # verifiquemos la firma de la transaccion
        # recuperamos primero su pk
        try:
            sender_pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(tx.sender))
        except ValueError:
            return False

        # validamos
        if not verify_signature(tx, sender_pk):
            return False

        return True

    def validate_transactions_lot(self, block: Block):
        """
        Metodo para validar si el lote de transacciones del bloque es correcto
        y no existen transacciones invalidas o con fondos insuficientes
        """

        # cuentas pendientes
        pending_spend = {}
        # nonce siguiente
        pending_next_nonce = {}

        for tx in block.transactions:
            # validar la transaccion
            if not self.validate_transaction(tx):
                return False

            last_nonce = self.get_last_transactions_nonce(tx.sender)
            expected_nonce = pending_next_nonce.get(tx.sender, last_nonce + 1)

            # si el nonce no es el que deberia ser el lote es invalido
            if tx.nonce != expected_nonce:
                return False
            pending_next_nonce[tx.sender] = pending_next_nonce.get(tx.sender, 0.0) + expected_nonce + 1

            available = self.get_balance(tx.sender) - pending_spend.get(tx.sender, 0.0)

            # rechazar si no cuenta con fondos o existe doble gasto
            if tx.amount > available:
                return False

            pending_spend[tx.sender] = pending_spend.get(tx.sender, 0.0) + tx.amount

        return True
