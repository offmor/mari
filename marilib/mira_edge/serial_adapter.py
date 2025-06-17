"""Module containing classes for interfacing with the DotBot gateway."""

from abc import ABC, abstractmethod

from mira_edge.serial_interface import SerialInterface
from rich import print


class GatewayAdapterBase(ABC):
    """Base class for interface adapters."""

    @abstractmethod
    def init(self, on_data_received: callable):
        """Initialize the interface."""

    @abstractmethod
    def close(self):
        """Close the interface."""

    @abstractmethod
    def send_data(self, data):
        """Send data to the interface."""


class SerialAdapter(GatewayAdapterBase):
    """Class used to interface with the serial port."""

    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.expected_length = -1
        self.bytes = bytearray()

    def on_byte_received(self, byte):
        if self.expected_length == -1:
            self.expected_length = int.from_bytes(byte, byteorder="little")
        else:
            self.bytes += byte
        if len(self.bytes) == self.expected_length:
            self.on_data_received(self.bytes)
            self.expected_length = -1
            self.bytes = bytearray()

    def init(self, on_data_received: callable):
        self.on_data_received = on_data_received
        self.serial = SerialInterface(
            self.port, self.baudrate, self.on_byte_received
        )
        print(f"[yellow]Connected to gateway on port {self.port}[/]")
        # send a disconnect followed by a connect to reset the gateway
        self.send_data(b"\xfe")
        self.send_data(b"\xff")

    def close(self):
        print("[yellow]Disconnect from gateway...[/]")
        self.send_data(b"\xfe")
        self.serial.stop()

    def send_data(self, data):
        self.serial.serial.flush()
        self.expected_length = -1
        self.serial.write(len(data).to_bytes(1, "big"))
        self.serial.write(data)
