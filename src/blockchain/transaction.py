from dataclasses import dataclass, field
from time import time

from exceptions import TransactionError


@dataclass(frozen=True)
class Transaction:
    """
    Clase que representa una transaccion en el blockchain, esta es
    inmutable despues de su creacion
    """

    # sender y receiver seria la identificacion de los usuarios
    # es decir sus claves publicas
    sender: str
    receiver: str
    amount: float

    # que tipo de dato seria la firma ?
    signature: str

    timestamp: float = field(default_factory=time)

    def __post_init__(self):
        # verificar que el amount sea positivo
        if self.amount <= 0:
            raise TransactionError(
                "Error en la creacion de la transaccion", "El valor debe ser positivo"
            )

        # verificar que el sender sea distinto al receiver
        if self.sender == self.receiver:
            raise TransactionError(
                "Error en la creacion de la transaccion",
                "El emisor debe ser distinto al receptor de la transaccion",
            )

        # verificar que la firma no sea una cadena vacia
        if not self.signature:
            raise TransactionError("Error al crear la transaccion", "Firma no valida")
