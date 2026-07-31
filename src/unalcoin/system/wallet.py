from dataclasses import asdict, dataclass, field
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from ..blockchain.transaction import Transaction
from ..crypto.keys import generate_pair_key
from .exceptions import WalletError


@dataclass(frozen=True)
class Wallet:
    """
    Clase wallet que representa a un usuario, esta contiene
    el par de claves que representa a un usuario
    """

    sk: Ed25519PrivateKey = field(init=False)
    pk: Ed25519PublicKey = field(init=False)
    nonce: int = 0

    def __post_init__(self):
        (
            sk,
            pk,
        ) = generate_pair_key()

        object.__setattr__(self, "sk", sk)
        object.__setattr__(self, "pk", pk)

    def sign(self, tx: Transaction):
        """
        Metodo para firmar una transaccion usando la clave publica de
        esta wallet
        """

        # primero verificar que la transaccion haya sido creada por
        # esta wallet, solo se pueden firmar transacciones creadas
        # por si misma
        if tx.sender == self.pk.public_bytes_raw().hex():
            sign = self.sk.sign(tx.to_bytes())
            tx.assign_sign(sign.hex())
        else:
            raise WalletError("Error al firmar la transaccion", "Esta transaccion no ha sido creada por esta wallet")

    def create_transaction(self, recipient: str, amount: float):
        """
        Metodo para crear una transaccion usando las claves de
        esta wallet
        """

        # verificar los datos
        if not recipient:
            raise WalletError("Error al crear la transaccion", "Transaccion incompleta: falta el receptor")

        if amount <= 0:
            raise WalletError("Error al crear la transaccion", "Transaccion no valida: la cantidad de la transaccion debe ser positiva")

        tx = Transaction(
            self.pk.public_bytes_raw().hex(), recipient, amount, self.nonce
        )
        object.__setattr__(self, "nonce", self.nonce + 1)

        return tx
