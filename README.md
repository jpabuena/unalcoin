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
uv run pytest
```

Ejecutar un archivo de test específico:
```sh
uv run python -m unittest -v tests/test_**.py
```

## main

Para ejecutar la implementación estatica de unalcoin
```sh
uv run unalcoin
```

Para interactuar con unalcoin mediante una cli
```sh
uv run unalcoin-cli
```

