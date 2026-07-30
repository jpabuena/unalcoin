# blockchain

## Setup

Para empezar a trabajar en el proyecto se necesita tener *uv* instalado y ejecutar
```sh
uv sync
```
*Esto creara el ambiente virtual e instalara las dependencias.*

Para añádir dependencias (librerias)
```sh
uv add <dependencia>
```

Para ejecutar el programa
```sh
uv run main.py
```

## Tests

Para añadir tests, crea archivos dentro de `tests/` con nombres como `test_*.py`.

Ejecutar todos los tests:
```sh
uv run python -m unittest discover -s tests -v
```

Ejecutar un archivo de test específico:
```sh
uv run python -m unittest -v tests/test_transaction_signature.py
```
