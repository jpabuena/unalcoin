from hashlib import sha256
from json import dumps
from typing import Any


def calculate_hash(content: dict[str, Any]):
    """
    Funcion para calcular el hash asociado a los parametros
    """
    serialized_content = dumps(content, sort_keys=True)
    return sha256(serialized_content.encode()).hexdigest()
