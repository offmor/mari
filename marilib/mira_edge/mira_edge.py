from typing import Callable
from mira_edge.protocol import Frame, Header, ProtocolPayloadParserException
from mira_edge.serial_adapter import SerialAdapter
from mira_edge.serial_interface import SerialInterfaceException

class MiraEdge:
    def __init__(self, on_receive: Callable[[Frame], None], port: str = "/dev/ttyACM0", baudrate: int = 1_000_000):
        try:
            self._interface = SerialAdapter(
                port, baudrate
            )
        except (
            SerialInterfaceException,
            serial.serialutil.SerialException,
        ) as exc:
            print(f"Error: {exc}")

    def on_data_received(self, data):
        print(f"Received: {data.hex()}")
        try:
            frame = Frame().from_bytes(data)
        except (ValueError, ProtocolPayloadParserException) as exc:
            print(f"Failed to decode frame: {exc}")
            return

    def connect_to_gateway(self):
        self._interface.init(self.on_data_received)

    def disconnect_from_gateway(self):
        self._interface.close()

    def send_frame(self, dst: int, payload: bytes):
        self._interface.send_data(Frame(Header(destination=dst), payload=payload).to_bytes())