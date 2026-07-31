# blockchain

## Setup

Para empezar a trabajar en el proyecto se necesita tener *uv* instalado y ejecutar:
```sh
uv sync
```
*Esto creara el ambiente virtual e instalara las dependencias.*

Para añádir dependencias (librerias):
```sh
uv add <dependencia>
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

## Ejecucion

### Usando *uv* (recomendado):
Para ejecutar la implementación estatica de unalcoin
```sh
uv run unalcoin
```

Para interactuar con unalcoin mediante una cli
```sh
uv run unalcoin-cli
```

### Usando pip

Si no se tiene *uv* para ejecutar el proyecto es necesario crear un entorno virtual:
```sh
python -m venv .venv
```

Activarlo:

*Linux/MacOS*:
```sh
source .venv/bin/activate
```

*Windows (quien usa windows (?)*
```cmd
.venv\Scripts\activate
```

Instalar el paquete (unalcoin)
```sh
pip install .
```

Ejecutar la implementación estatica:
```sh
unalcoin
```

Ejecutar la consola interactiva
```sh
unalcoin-cli
```
