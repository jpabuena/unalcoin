from dataclasses import dataclass


@dataclass
class Error(Exception):
    message: str
    description: str


@dataclass
class BlockError(Error):
    pass


@dataclass
class TransactionError(Error):
    pass


@dataclass
class BlockchainError(Error):
    pass


@dataclass
class BlockBuilderError(Error):
    pass
