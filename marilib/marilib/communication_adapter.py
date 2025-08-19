import base64
import paho.mqtt.client as mqtt

from abc import ABC, abstractmethod
from rich import print

from marilib.serial_hdlc import (
    HDLCDecodeException,
    HDLCHandler,
    HDLCState,
    hdlc_encode,
)
from marilib.serial_uart import SerialInterface, SERIAL_DEFAULT_BAUDRATE


class CommunicationAdapterBase(ABC):
    """Base class for interface adapters."""

    @abstractmethod
    def init(self, on_data_received: callable):
        """Initialize the interface."""

    @abstractmethod
    def close(self):
        """Close the interface."""


class SerialAdapter(CommunicationAdapterBase):
    """Class used to interface with the serial port."""

    def __init__(self, port, baudrate=SERIAL_DEFAULT_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.hdlc_handler = HDLCHandler()

    def on_byte_received(self, byte):
        self.hdlc_handler.handle_byte(byte)
        if self.hdlc_handler.state == HDLCState.READY:
            try:
                payload = self.hdlc_handler.payload
                # print(f"Received payload: {payload.hex()}")
                self.on_data_received(payload)
            except HDLCDecodeException as e:
                print(f"Error decoding payload: {e}")

    def init(self, on_data_received: callable):
        self.on_data_received = on_data_received
        self.serial = SerialInterface(self.port, self.baudrate, self.on_byte_received)
        print(f"[yellow]Connected to gateway on port {self.port}[/]")

    def close(self):
        print("[yellow]Disconnect from gateway...[/]")

    def send_data(self, data):
        self.serial.serial.flush()
        encoded = hdlc_encode(data)
        self.serial.write(encoded)


class MQTTAdapter(CommunicationAdapterBase):
    """Class used to interface with MQTT."""

    def __init__(self, host, port, is_edge: bool):
        self.host = host
        self.port = port
        self.network_id = None
        self.client = None
        self.on_data_received = None
        self.is_edge = is_edge

    @classmethod
    def from_host_port(cls, host_port: str):
        host, port = host_port.split(":")
        return cls(host, int(port))

    # ==== public methods ====

    def is_ready(self) -> bool:
        return self.client is not None and self.client.is_connected()

    def set_network_id(self, network_id: str):
        self.network_id = network_id

    def set_on_data_received(self, on_data_received: callable):
        self.on_data_received = on_data_received

    def update(self, network_id: str, on_data_received: callable):
        if self.network_id is None:
            self.network_id = network_id
        else:
            # TODO: handle the case when the network_id changes
            pass
        if self.on_data_received is None:
            self.set_on_data_received(on_data_received)
        if not self.is_ready():
            self.init()

    def init(self):
        if self.client:
            # already initialized, do nothing
            return

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTProtocolVersion.MQTTv5,
        )
        # self.client.tls_set_context(context=None)  # Commented out for plain MQTT
        self.client.on_log = self._on_log
        self.client.on_connect = self._on_connect_edge if self.is_edge else self._on_connect_cloud
        self.client.on_message = self._on_message_edge if self.is_edge else self._on_message_cloud
        try:
            self.client.connect(self.host, self.port, 60)
        except Exception as e:
            print(f"[red]Error connecting to MQTT broker: {e}[/]")
            print(f"[red]Host: {self.host}, Port: {self.port}[/]")
            return
        self.client.loop_start()

    def close(self):
        self.client.disconnect()
        self.client.loop_stop()

    def send_data_to_edge(self, data):
        if not self.is_ready():
            return
        self.client.publish(
            f"/mari/{self.network_id}/to_edge",
            base64.b64encode(data).decode(),
        )

    def send_data_to_cloud(self, data):
        if not self.is_ready():
            return
        self.client.publish(
            f"/mari/{self.network_id}/to_cloud",
            base64.b64encode(data).decode(),
        )

    # ==== private methods ====

    # TODO: de-duplicate the _on_message_* functions? decide as the integration evolves
    def _on_message_edge(self, client, userdata, message):
        try:
            data = base64.b64decode(message.payload)
        except Exception as e:
            # print the error and a stacktrace
            print(f"[red]Error decoding MQTT message: {e}[/]")
            print(f"[red]Message: {message.payload}[/]")
            return
        self.on_data_received(data)

    def _on_message_cloud(self, client, userdata, message):
        try:
            data = base64.b64decode(message.payload)
        except Exception as e:
            # print the error and a stacktrace
            print(f"[red]Error decoding MQTT message: {e}[/]")
            print(f"[red]Message: {message.payload}[/]")
            return
        self.on_data_received(data)

    def _on_log(self, client, userdata, paho_log_level, messages):
        # print(messages)
        pass

    def _on_connect_edge(self, client, userdata, flags, reason_code, properties):
        self.client.subscribe(f"/mari/{self.network_id}/to_edge")

    def _on_connect_cloud(self, client, userdata, flags, reason_code, properties):
        self.client.subscribe(f"/mari/{self.network_id}/to_cloud")


class MQTTAdapterDummy(MQTTAdapter):
    """Dummy MQTT adapter, does nothing, for when edge runs only locally, without a cloud."""
    def __init__(self, host="", port=0):
        super().__init__(host, port)

    def is_ready(self) -> bool:
        """Dummy adapter is never ready."""
        return False

    def init(self, network_id: str, on_data_received: callable, is_edge: bool):
        pass

    def close(self):
        pass

    def send_data_to_edge(self, data):
        pass

    def send_data_to_cloud(self, data):
        pass
