from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generate_pair_key(): 
    """
    Funcion para generar un par de llaves publica y privada para el algoritmo de
    firma Ed25519
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    return private_key, public_key

