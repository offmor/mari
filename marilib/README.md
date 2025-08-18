# MariLib 💫 👀 🐍

MariLib is a Python library to interact with a local [Mari](https://github.com/DotBots/mari) network.
It connects to a Mari gateway via UART.

## Example with TUI
MariLib provides a stateful class with gateway and node information, network statistics, and a rich real-time TUI:

[mari-edge-2.webm](https://github.com/user-attachments/assets/fe50f2ba-8e67-4522-8700-69730f8e3aee)

See the how it works in `examples/basic.py`.

## Minimal example
Here is a minimal example showcasing how to use MariLib:

```python
import time
from marilib.marilib import MarilibEdge
from marilib.serial_uart import get_default_port

def main():
    mari = MarilibEdge(lambda event, data: print(event.name, data), get_default_port())
    while True:
        for node in mari.gateway.nodes:
            mari.send_frame(dst=node.address, payload=b"A" * 3)
        statistics = [(f"{node.address:016X}", node.stats.received_rssi_dbm()) for node in mari.gateway.nodes]
        print(f"Network statistics: {statistics}")
        time.sleep(0.25)

if __name__ == "__main__":
    main()
```
See it in action in `examples/minimal.py`.
