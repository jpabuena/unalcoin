from datetime import datetime, timezone
from json import dumps
from typing import Any


def get_timestamp():
    return datetime.now(timezone.utc)


def _default_serializer(obj: Any):
    """Serializador auxiliar para json.dumps.

        - datetime -> ISO 8601 UTC with microsecond precision and trailing Z
    - tuples -> list (to ensure JSON compatibility)
    """
    if isinstance(obj, datetime):
        # tratar datetimes naive como UTC para compatibilidad
        if obj.tzinfo is None:
            dt_utc = obj.replace(tzinfo=timezone.utc)
        else:
            dt_utc = obj.astimezone(timezone.utc)
        return dt_utc.isoformat(timespec="microseconds").replace("+00:00", "Z")

    if isinstance(obj, tuple):
        return list(obj)

    # dejar que json levante TypeError para otros tipos no soportados
    raise TypeError(f"No se puede serializar objeto de tipo {type(obj)}")


def serialize(data: dict[str, Any]):
    """
    Metodo que serizaliza el diccionario de la data en JSON
    """
    return dumps(data, sort_keys=True, default=_default_serializer)
