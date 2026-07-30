from datetime import datetime, timezone
from hashlib import sha256
from json import dumps
from typing import Any
from blockchain.utils import serialize



def calculate_hash(data: dict[str, Any]):
    """
    Funcion para calcular el hash asociado a los parametros
    """
    serialized_content = serialize(data)
    return sha256(serialized_content.encode()).hexdigest()

