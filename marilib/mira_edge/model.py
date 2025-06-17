from enum import IntEnum
from dataclasses import dataclass, field
from datetime import datetime, timedelta


class EdgeEvent(IntEnum):
    """Types of UART packet."""
    NODE_JOINED = 1
    NODE_LEFT = 2
    NODE_DATA = 3
    NODE_KEEP_ALIVE = 4


@dataclass
class NodeAddress:
    value: bytes = field(default_factory=lambda: b'\x00' * 8)

    @property
    def value_int(self) -> int:
        return int.from_bytes(self.value, "little")

    @staticmethod
    def from_int(address_int: int) -> "NodeAddress":
        return NodeAddress(address_int.to_bytes(length=8, byteorder="little"))

    def __repr__(self):
        return '0x' + ''.join([f'{b:02X}' for b in reversed(self.value)])


@dataclass
class MiraNode:
    address: NodeAddress
    last_seen: datetime

    @property
    def is_alive(self) -> bool:
        return datetime.now() - self.last_seen < timedelta(seconds=10)

    @property
    def address_int(self) -> int:
        return self.address.value_int

    def __repr__(self):
        return f"MiraNode(address={self.address}, last_seen={self.last_seen})"
