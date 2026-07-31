from dataclasses import dataclass, field, asdict
from datetime import datetime
from .utils import get_timestamp, serialize


@dataclass(frozen=True)
class CoinbaseTransaction:
    """
    Transacción especial que introduce monedas nuevas al sistema.
    Representa la recompensa que recibe el minero al añadir un bloque válido.

    A diferencia de las transacciones ordinarias:
      - No tiene emisor real (sender = "COINBASE").
      - No requiere firma digital.
      - Solo puede aparecer una vez por bloque y debe ser la primera transacción.
    """

    recipient: str
    amount: float
    sender: str = field(default="COINBASE", init=False)
    signature: str = field(default="COINBASE", init=False)
    timestamp: datetime = field(default_factory=get_timestamp, init=False)

    def to_bytes(self) -> bytes:
        data = asdict(self)
        del data["signature"]
        return serialize(data).encode()
