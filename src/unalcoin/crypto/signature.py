from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from ..blockchain.transaction import Transaction


def verify_signature(tx: Transaction, pk: Ed25519PublicKey):
    """
    Metodo para verificar la firma de una transaccion a partir
    de una llave publica
    """
    if tx.signature:
        try:
            pk.verify(bytes.fromhex(tx.signature), tx.to_bytes())
            return True
        except InvalidSignature:
            return False
    else:
        return False
