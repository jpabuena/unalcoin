from dataclasses import dataclass, field, asdict
from block import Block
from exceptions import BlockchainError
from time import time
from block_builder import BlockBuilder
from crypto.hash import calculate_hash


@dataclass
class Blockchain:
    """
    Clase que representa la cadena de bloques
    """

    difficulty: int
    chain: list[Block] = field(default=[], init=False)

    @property
    def length(self) -> int:
        return len(self.chain)

    @property
    def last_block(self) -> Block | None:
        """
        El ultimo bloque agregado a la cadena
        """
        if self.length:
            return self.chain[-1]
        else:
            return None

    def create_genesis_block(self):
        """
        Es necesario crear el bloque genesis para empezar
        a añadir bloques a la cadena, este metodo se encargara
        de ello
        """
        if not self.length:
            # crear el builder del bloque y minarlo
            genesis_block = BlockBuilder(
                0, [], "0",
            )

            # minamos el bloque
            mined_genesis_block = genesis_block.mine(self.difficulty)

            # agregamos el bloque directamente a la cadena
            self.chain.append(mined_genesis_block)
        else:
            raise BlockchainError(
                "Error al crear el bloque genesis", "El bloque genesis ya fue creado"
            )

    def add_block(self, block: Block):
        if self.length:
            if self.verify_block(block):
                self.chain.append(block)
            else:
                raise BlockchainError(
                    "Error al agregar el bloque",
                    "El bloque es invalido y no puede ser agregado a la cadena",
                )
        else:
            raise BlockchainError(
                "Error al agregar el bloque",
                "No puede agregarse el nuevo bloque ya que no existe el bloque genesis",
            )

    def verify_block(self, block: Block) -> bool:
        """
        Metodo para verificar si un bloque es realmente valido
        para ser añadido a la cadena.
        """

        # primero verificar que el hash del bloque corresponda a este mismo
        block_hash = calculate_hash(asdict(block))
        if block_hash != block.hash:
            return False

        # verificar que el hash cumpla con la dificultad de minado
        if not block_hash.startswith("0" * self.difficulty):
            return False

        # validar la integridad del bloque respecto a la cadena, es decir respecto a su bloque
        # anterior, solo verificamos para los nuevos bloques, el bloque genesis no tiene previous_hash
        if self.last_block and self.length > 1:
            if self.last_block.hash != block.previous_hash:
                return False

        return True

    # que deberia retornar esto?
    def verify_chain(self) -> bool:
        """
        Metodo que verifica la integridad de la cadena, esto se refiere a mirar si cada bloque es
        correcto y ademas cumple con la propiedad de estar enlazado criptogrficamente con su bloque previo
        """
        for i in range(self.length - 1, 0, -1):
            # se debe hacer una verificación de cada bloque, ¿cuando un bloque es correcto?
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # verificar ambos bloques
            if not self.verify_block(current_block) or not self.verify_block(
                previous_block
            ):
                # esto puede pasar? xD
                # deberiamos retornar False o lanzar una excepcion?
                return False

            # verificar si estan enlazados criptograficamente
            if current_block.previous_hash != previous_block.hash:
                # retornar False o lanzar excepcion?
                return False

        return True
