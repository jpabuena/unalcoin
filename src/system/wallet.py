from dataclasses import asdict, dataclass, field
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from blockchain.transaction import Transaction
from crypto.keys import generate_pair_key


@dataclass(frozen=True)
class Wallet:
    """
    Clase wallet que representa a un usuario, esta contiene
    el par de claves que representa a un usuario
    """

    sk: Ed25519PrivateKey = field(init=False)
    pk: Ed25519PublicKey = field(init=False)

    def __post_init__(self):
        sk, pk, = generate_pair_key()

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
            # TODO: lanzar una excepcion
            pass

    def create_transaction(self, recipient: str, amount: float):
        """
        Metodo para crear una transaccion usando las claves de
        esta wallet
        """

        # verificar los datos
        if not recipient:
            # TODO: lanzar una excepcion
            pass
       
        if amount <= 0:
            # TODO: lanzar una excepcion
            pass

        return Transaction(self.pk.public_bytes_raw().hex(), recipient, amount, 0) # TODO: como vamos a manejar el nonce?
