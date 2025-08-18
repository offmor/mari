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

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.network_id = "FFFF"
        self.client = None

    # TODO: de-duplicate the on_message functions? decide as the integration evolves

    def on_message_edge(self, client, userdata, message):
        try:
            data = base64.b64decode(message.payload)
        except Exception as e:
            # print the error and a stacktrace
            print(f"[red]Error decoding MQTT message: {e}[/]")
            print(f"[red]Message: {message.payload}[/]")
            return
        self.on_data_received(data)

    def on_message_cloud(self, client, userdata, message):
        try:
            data = base64.b64decode(message.payload)
        except Exception as e:
            # print the error and a stacktrace
            print(f"[red]Error decoding MQTT message: {e}[/]")
            print(f"[red]Message: {message.payload}[/]")
            return
        self.on_data_received(data)

    def on_log(self, client, userdata, paho_log_level, messages):
        print(messages)

    def on_connect_edge(self, client, userdata, flags, reason_code, properties):
        self.client.subscribe(f"/mari/{self.network_id}/cloud_to_edge")

    def on_connect_cloud(self, client, userdata, flags, reason_code, properties):
        self.client.subscribe(f"/mari/{self.network_id}/edge_to_cloud")

    def init(self, network_id: str, on_data_received: callable, is_edge: bool):
        if self.client:
            # already initialized, do nothing
            return

        self.network_id = network_id
        self.is_edge = is_edge

        self.on_data_received = on_data_received
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTProtocolVersion.MQTTv5,
        )
        # self.client.tls_set_context(context=None)  # Commented out for plain MQTT
        self.client.on_log = self.on_log
        self.client.on_connect = self.on_connect_edge if is_edge else self.on_connect_cloud
        self.client.on_message = self.on_message_edge if is_edge else self.on_message_cloud
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
        self.client.publish(
            f"/mari/{self.network_id}/cloud_to_edge",
            base64.b64encode(data).decode(),
        )

    def send_data_to_cloud(self, data):
        self.client.publish(
            f"/mari/{self.network_id}/edge_to_cloud",
            base64.b64encode(data).decode(),
        )
