import time

from mari_edge.mari_edge import MariEdge
from mari_edge.serial_uart import get_default_port


def main():
    mari = MariEdge(lambda event, data: print(event.name, data), get_default_port())
    while True:
        for node in mari.gateway.nodes:
            mari.send_frame(dst=node.address, payload=b"A" * 3)
        statistics = [
            (f"{node.address:016X}", node.stats.received_rssi_dbm())
            for node in mari.gateway.nodes
        ]
        print(f"Network statistics: {statistics}")
        time.sleep(0.25)


if __name__ == "__main__":
    main()
