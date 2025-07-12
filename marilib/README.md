# MiraEdge 💫 👀 🐍

MiraEdge is a Python library to interact with a local [Mira](https://github.com/DotBots/mira) network.
It connects to a Mira gateway via UART.

## Example with TUI
MiraEdge provides a stateful class with gateway and node information, network statistics, and a rich real-time TUI:

[mira-edge-2.webm](https://github.com/user-attachments/assets/fe50f2ba-8e67-4522-8700-69730f8e3aee)

See the how it works in `examples/basic.py`.

## Minimal example
Here is a minimal example showcasing how to use MiraEdge:

```python
import time
from mira_edge.mira_edge import MiraEdge
from mira_edge.serial_uart import get_default_port

def main():
    mira = MiraEdge(lambda event, data: print(event.name, data), get_default_port())
    while True:
        for node in mira.gateway.nodes:
            mira.send_frame(dst=node.address, payload=b"A" * 3)
        statistics = [(f"{node.address:016X}", node.stats.received_rssi_dbm()) for node in mira.gateway.nodes]
        print(f"Network statistics: {statistics}")
        time.sleep(0.25)

if __name__ == "__main__":
    main()
```
See it in action in `examples/minimal.py`.
