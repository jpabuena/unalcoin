from dataclasses import dataclass

@dataclass
class SystemError(Exception):
    message: str
    description: str

@dataclass
class WalletError(SystemError):
    pass
