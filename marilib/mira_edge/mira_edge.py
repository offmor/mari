from typing import Callable
from enum import IntEnum
from mira_edge.protocol import Frame, Header, ProtocolPayloadParserException
from mira_edge.serial_adapter import SerialAdapter
from mira_edge.serial_interface import SerialInterfaceException


class EdgeEvent(IntEnum):
    """Types of UART packet."""
    NODE_JOINED = 1
    NODE_LEFT = 2
    NODE_DATA = 3


class MiraEdge:
    def __init__(self, on_event: Callable[[EdgeEvent, Frame | bytes], None], port: str = "/dev/ttyACM0", baudrate: int = 1_000_000):
        self.on_event = on_event
        self.nodes = []
        try:
            self._interface = SerialAdapter(
                port, baudrate
            )
        except (
            SerialInterfaceException,
            serial.serialutil.SerialException,
        ) as exc:
            print(f"Error: {exc}")

    def on_data_received(self, data: bytes):
        if data[0] == EdgeEvent.NODE_JOINED:
            print(f"Node joined: {data[1:9]}")
            self.nodes.append(data[1:9])
            self.on_event(EdgeEvent.NODE_JOINED, data[1:9])
        elif data[0] == EdgeEvent.NODE_LEFT:
            print(f"Node left: {data[1:9]}")
            try:
                self.nodes.remove(data[1:9])
                self.on_event(EdgeEvent.NODE_LEFT, data[1:9])
            except ValueError:
                print(f"Node {data[1:9]} not found in nodes list")
        elif data[0] == EdgeEvent.NODE_DATA:
            try:
                frame = Frame().from_bytes(data)
                self.on_event(EdgeEvent.NODE_DATA, frame)
            except (ValueError, ProtocolPayloadParserException) as exc:
                print(f"Failed to decode frame: {exc}")
        else:
            print(f"Unknown event: {data[0]} -- {data}")

    def connect_to_gateway(self):
        self._interface.init(self.on_data_received)

    def disconnect_from_gateway(self):
        self._interface.close()

    def send_frame(self, dst: int, payload: bytes):
        self._interface.send_data(Frame(Header(destination=dst), payload=payload).to_bytes())
