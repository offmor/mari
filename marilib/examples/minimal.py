import time

from mira_edge.mira_edge import MiraEdge
from mira_edge.serial_uart import get_default_port


def main():
    mira = MiraEdge(lambda event, data: print(event.name, data), get_default_port())
    while True:
        for node in mira.gateway.nodes:
            mira.send_frame(dst=node.address, payload=b"A" * 3)
        statistics = [
            (f"{node.address:016X}", node.stats.received_rssi_dbm())
            for node in mira.gateway.nodes
        ]
        print(f"Network statistics: {statistics}")
        time.sleep(0.25)


if __name__ == "__main__":
    main()
