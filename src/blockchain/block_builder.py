from dataclasses import dataclass, field, asdict
from transaction import Transaction
from block import Block
from json import dumps
from hashlib import sha256
from time import time
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
    timestamp: float = field(default_factory=time, init=False)

    def add_transaction(self, tx: Transaction):
        self.transactions.append(
            tx
        )  # TODO: validar la firma antes de agregar la transaccion

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
        content = asdict(self)

        # nonce para el minado del bloque
        content["nonce"] = 0


        # como vamos a minar el bloque le asignamos a hash una cadena vacia
        # para poder comparar debido a que esta es None en la creacion del
        # builder
        computed_hash = ""
        while not computed_hash.startswith(target):
            # le sumamos uno al nonce y recalculamos el hash
            content["nonce"] += 1

            computed_hash = calculate_hash(content)

        # una vez se mina el bloque se procede a crear el mismo inmutable
        return Block(
            self.index,
            tuple(self.transactions),
            self.previous_hash,
            content["nonce"],
            self.timestamp,
            computed_hash,
        )
