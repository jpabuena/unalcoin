from dataclasses import dataclass


@dataclass
class BlockchainError(Exception):
    message: str
    descripcion: str


@dataclass
class GenesisBlockExistentError(BlockchainError):
    pass


@dataclass
class AddBlockError(BlockchainError):
    pass

