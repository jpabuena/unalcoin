from dataclasses import dataclass, field
from time import time
from json import dumps
from hashlib import sha256
from typing import Any


@dataclass
class Block:
    """
    Bloque dentro de la blockchain
    """

    index: int
    transactions: list[Any]
    previous_hash: str

    # nonce para el minado del bloque
    nonce: int = 0 # TODO: implementar el minado del bloque

    # fecha y hora de la creacion del bloque en formato UNIX
    timestamp: float = field(default_factory=time)

    # despues de ser instanciado el bloque calculamos su hash
    def __post_init__(self):
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Funcion para calcular el hash del bloque en funcion de su estado actual.

        Se utiliza formato json para representar el contenido del bloque, además
        se ordenan las llaves para obtener siempre el mismo hash para los mismos
        datos.
        """
        block_content = dumps(
            {
                "index": self.index,
                "transactions": self.transactions,
                "previous_hash": self.previous_hash,
                "nonce": self.nonce,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
        )

        return sha256(block_content.encode()).hexdigest()
