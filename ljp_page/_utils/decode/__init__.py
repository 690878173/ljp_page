# 05-19-16-20-00
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .decode import AESCipher as AESCipher

__all__ = ["AESCipher", "Aes"]


def __getattr__(name: str) -> object:
    if name not in __all__:
        raise AttributeError(f"{__name__} 找不到成员 {name}")
    from .decode import AESCipher

    if name == "Aes":
        return AESCipher
    return AESCipher
