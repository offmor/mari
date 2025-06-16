import dataclasses
from dataclasses import dataclass
import typing
from enum import IntEnum
from abc import ABC

MIRA_PROTOCOL_VERSION = 2
MIRA_BROADCAST_ADDRESS = 0xFFFFFFFFFFFFFFFF
MIRA_NET_ID_DEFAULT = 0x0001


class ProtocolPayloadParserException(Exception):
    """Exception raised on invalid or unsupported payload."""


class PacketType(IntEnum):
    """Types of MAC layer packet."""

    BEACON = 1
    JOIN_REQUEST = 2
    JOIN_RESPONSE = 4
    KEEP_ALIVE = 8
    DATA = 16


@dataclass
class PacketFieldMetadata:
    """Data class that describes a packet field metadata."""

    name: str = ""
    disp: str = ""
    length: int = 1
    signed: bool = False
    type_: typing.Any = int

    def __post_init__(self):
        if not self.disp:
            self.disp = self.name


@dataclass
class Packet(ABC):
    """Base class for packet classes."""

    @property
    def size(self) -> int:
        return sum(field.length for field in self.metadata)

    def from_bytes(self, bytes_):
        fields = dataclasses.fields(self)
        # base class makes metadata attribute mandatory so there's at least one
        # field defined in subclasses
        # first elements in fields has to be metadata
        if not fields or fields[0].name != "metadata":
            raise ValueError("metadata must be defined first")
        metadata = fields[0].default_factory()
        for idx, field in enumerate(fields[1:]):
            if metadata[idx].type_ is list:
                element_class = typing.get_args(field.type)[0]
                field_attribute = getattr(self, field.name)
                # subclass element is a list and previous attribute is called
                # "count" and should have already been retrieved from the byte
                # stream
                for _ in range(self.count):
                    element = element_class()
                    if len(bytes_) < element.size:
                        raise ValueError("Not enough bytes to parse")
                    field_attribute.append(element.from_bytes(bytes_))
                    bytes_ = bytes_[element.size :]
            elif metadata[idx].type_ in [bytes, bytearray]:
                # subclass element is bytes and previous attribute is called
                # "count" and should have already been retrieved from the byte
                # stream
                length = metadata[idx].length
                if hasattr(self, "count"):
                    length = self.count
                setattr(self, field.name, bytes_[0:length])
                bytes_ = bytes_[length:]
            else:
                length = metadata[idx].length
                if len(bytes_) < length:
                    raise ValueError("Not enough bytes to parse")
                setattr(
                    self,
                    field.name,
                    int.from_bytes(
                        bytes=bytes_[0:length],
                        signed=metadata[idx].signed,
                        byteorder="little",
                    ),
                )
                bytes_ = bytes_[length:]
        return self

    def to_bytes(self, byteorder="little") -> bytes:
        buffer = bytearray()
        metadata = dataclasses.fields(self)[0].default_factory()
        for idx, field in enumerate(dataclasses.fields(self)[1:]):
            value = getattr(self, field.name)
            if isinstance(value, list):
                for element in value:
                    buffer += element.to_bytes()
            elif isinstance(value, (bytes, bytearray)):
                buffer += value
            else:
                buffer += int(value).to_bytes(
                    length=metadata[idx].length,
                    byteorder=byteorder,
                    signed=metadata[idx].signed,
                )
        return buffer


@dataclass
class Header(Packet):
    """Dataclass that holds MAC header fields."""

    metadata: list[PacketFieldMetadata] = dataclasses.field(
        default_factory=lambda: [
            PacketFieldMetadata(name="version", disp="ver.", length=1),
            PacketFieldMetadata(name="type_", disp="type", length=1),
            PacketFieldMetadata(name="network_id", disp="net", length=2),
            PacketFieldMetadata(name="destination", disp="dst", length=8),
            PacketFieldMetadata(name="source", disp="src", length=8),
        ]
    )
    version: int = MIRA_PROTOCOL_VERSION
    type_: int = PacketType.DATA
    network_id: int = MIRA_NET_ID_DEFAULT
    destination: int = MIRA_BROADCAST_ADDRESS
    source: int = 0x0000000000000000


class NodeState(IntEnum):
    """States of a node."""

    BOOTLOADER = 0
    RUNNING = 1
    STOPPED = 2
    PROGRAMMING = 3


@dataclass
class PayloadNodeStatus(Packet):
    """Dataclass that holds a node status."""

    metadata: list[PacketFieldMetadata] = dataclasses.field(
        default_factory=lambda: [
            PacketFieldMetadata(name="node_state", disp="state", length=1),
            PacketFieldMetadata(name="battery_level", disp="bat", length=1),
            PacketFieldMetadata(name="lh2_pos_x", disp="x", length=2),
            PacketFieldMetadata(name="lh2_pos_y", disp="y", length=2),
        ]
    )

    node_state: NodeState = NodeState.BOOTLOADER
    battery_level: int = 50
    lh2_pos_x: int = 0
    lh2_pos_y: int = 0

class PayloadType(IntEnum):
    """Types of DotBot payload types."""

    ADVERTISEMENT = 0x04

PAYLOAD_PARSERS: dict[int, Packet] = {
    PayloadType.ADVERTISEMENT: PayloadNodeStatus,
}


@dataclass
class Frame:
    """Data class that holds a payload packet."""

    header: Header = None
    payload: Packet = None

    @property
    def payload_type(self) -> int:
        for payload_type, cls_ in PAYLOAD_PARSERS.items():
            if cls_ == self.payload.__class__:
                return payload_type
        raise ValueError(f"Unsupported payload class '{self.payload.__class__}'")

    def from_bytes(self, bytes_):
        self.header = Header().from_bytes(bytes_[0:18])
        payload_type = int.from_bytes(bytes_[18:19], "little")
        if payload_type not in PAYLOAD_PARSERS:
            raise ProtocolPayloadParserException(
                f"Unsupported payload type '{payload_type}'"
            )
        self.payload = PAYLOAD_PARSERS[payload_type]().from_bytes(bytes_[19:])
        return self

    def to_bytes(self, byteorder="little") -> bytes:
        header_bytes = self.header.to_bytes(byteorder)
        if isinstance(self.payload, bytes):
            payload_bytes = self.payload
        else:
            payload_bytes = self.payload.to_bytes(byteorder)
        return header_bytes + int.to_bytes(self.payload_type) + payload_bytes

    def __repr__(self):
        header_separators = [
            "-" * (2 * field.length + 4) for field in self.header.metadata
        ]
        type_separators = ["-" * 6]
        payload_separators = [
            "-" * (2 * field.length + 4)
            for field in self.payload.metadata
            if field.type_ is int
        ]
        payload_separators += [
            "-" * (2 * field_metadata.length + 4)
            for metadata in self.payload.metadata
            if metadata.type_ is list
            for field in getattr(self.payload, metadata.name)
            for field_metadata in field.metadata
        ]
        payload_separators += [
            "-" * (2 * len(getattr(self.payload, field.name)) + 4)
            for field in self.payload.metadata
            if field.type_ is bytes
        ]
        header_names = [
            f" {field.disp:<{2 * field.length + 3}}" for field in self.header.metadata
        ]
        payload_names = [
            f" {field.disp:<{2 * field.length + 3}}"
            for field in self.payload.metadata
            if field.type_ in (int, bytes) and field.length > 0
        ]
        payload_names += [
            f" {field.disp:<{2 * len(getattr(self.payload, field.name)) + 3}}"
            for field in self.payload.metadata
            if field.type_ is bytes and field.length == 0
        ]
        payload_names += [
            f" {field_metadata.disp:<{2 * field_metadata.length + 3}}"
            for metadata in self.payload.metadata
            if metadata.type_ is list
            for field in getattr(self.payload, metadata.name)
            for field_metadata in field.metadata
        ]
        header_values = [
            f" 0x{hexlify(int(getattr(self.header, field.name)).to_bytes(self.header.metadata[idx].length, 'big', signed=self.header.metadata[idx].signed)).decode():<{2 * self.header.metadata[idx].length + 1}}"
            for idx, field in enumerate(dataclasses.fields(self.header)[1:])
        ]
        type_value = [f" 0x{hexlify(self.payload_type.to_bytes(1, 'big')).decode():<3}"]
        payload_values = [
            f" 0x{hexlify(int(getattr(self.payload, field.name)).to_bytes(self.payload.metadata[idx].length, 'big', signed=self.payload.metadata[idx].signed)).decode():<{2 * self.payload.metadata[idx].length + 1}}"
            for idx, field in enumerate(dataclasses.fields(self.payload)[1:])
            if self.payload.metadata[idx].type_ is int
        ]
        payload_values += [
            f" 0x{hexlify(int(getattr(field, field_metadata.name)).to_bytes(field_metadata.length, 'big', signed=field_metadata.signed)).decode():<{2 *field_metadata.length + 1}}"
            for metadata in self.payload.metadata
            if metadata.type_ is list
            for field in getattr(self.payload, metadata.name)
            for field_metadata in field.metadata
        ]
        payload_values += [
            f" 0x{hexlify(getattr(self.payload, field.name)).decode():<{2 * self.payload.count + 1}}"
            for idx, field in enumerate(dataclasses.fields(self.payload)[1:])
            if self.payload.metadata[idx].type_ is bytes
            and hasattr(self.payload, "count")
        ]
        payload_values += [
            f" 0x{hexlify(getattr(self.payload, field.name)).decode():<{2 * self.payload.metadata[idx].length + 1}}"
            for idx, field in enumerate(dataclasses.fields(self.payload)[1:])
            if self.payload.metadata[idx].type_ is bytes
            and not hasattr(self.payload, "count")
        ]
        num_bytes = (
            sum(field.length for field in self.header.metadata)
            + 1
            + sum(field.length for field in self.payload.metadata)
        )
        num_bytes += sum(
            field_metadata.length
            for metadata in self.payload.metadata
            if metadata.type_ is list
            for field in getattr(self.payload, metadata.name)
            for field_metadata in field.metadata
        )
        num_bytes += sum(
            len(getattr(self.payload, field.name))
            for field in self.payload.metadata
            if field.type_ is bytes and field.length == 0
        )

        if self.payload_type not in [*PayloadType]:
            payload_type_str = "CUSTOM_DATA"
        else:
            payload_type_str = PayloadType(self.payload_type).name
        if num_bytes > 24:
            # put values on a separate row
            separators = header_separators + type_separators
            names = header_names + [" type "]
            values = header_values + type_value
            return (
                f" {' ' * 16}+{'+'.join(separators)}+\n"
                f" {payload_type_str:<16}|{'|'.join(names)}|\n"
                f" {f'({num_bytes} Bytes)':<16}|{'|'.join(values)}|\n"
                f" {' ' * 16}+{'+'.join(separators)}+\n"
                f" {' ' * 16}+{'+'.join(payload_separators)}+\n"
                f" {' ' * 16}|{'|'.join(payload_names)}|\n"
                f" {' ' * 16}|{'|'.join(payload_values)}|\n"
                f" {' ' * 16}+{'+'.join(payload_separators)}+\n"
            )

        # all in a row by default
        separators = header_separators + type_separators + payload_separators
        names = header_names + [" type "] + payload_names
        values = header_values + type_value + payload_values
        return (
            f" {' ' * 16}+{'+'.join(separators)}+\n"
            f" {payload_type_str:<16}|{'|'.join(names)}|\n"
            f" {f'({num_bytes} Bytes)':<16}|{'|'.join(values)}|\n"
            f" {' ' * 16}+{'+'.join(separators)}+\n"
        )
