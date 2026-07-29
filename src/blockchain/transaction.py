from dataclasses import asdict, dataclass, field
from json import dumps
from time import time
from .exceptions import TransactionError


@dataclass(frozen=True)
class Transaction:
    """
    Clase que representa una transaccion en el blockchain, esta es
    inmutable despues de su creacion
    """

    # sender y recipient serian la identificacion de los usuarios
    # es decir sus claves publicas (o una representacion)
    sender: str
    recipient: str
    amount: float
    nonce: int

    timestamp: float = field(default_factory=time, init=False)

    # la firma sera guardada en hexadecimal
    signature: str | None = field(default=None, init=False)

    def __post_init__(self):
        # verificar que el amount sea positivo
        if self.amount <= 0:
            raise TransactionError(
                "Error en la creacion de la transaccion", "El valor debe ser positivo"
            )

        # verificar que el sender sea distinto al recipient
        if self.sender == self.recipient:
            raise TransactionError(
                "Error en la creacion de la transaccion",
                "El emisor debe ser distinto al receptor de la transaccion",
            )

    def to_bytes(self):
        """
        Representacion en bytes de la transaccion
        """
        
        content = asdict(self)
        del content["signature"]
        return dumps(content, sort_keys=True).encode()


    def assign_sign(self, sign: str):
        object.__setattr__(self, "signature", sign)
