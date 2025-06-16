import time
from mira_edge.mira_edge import MiraEdge
from mira_edge.protocol import Frame, MIRA_BROADCAST_ADDRESS, PayloadNodeStatus


def on_receive(frame: Frame): # type: ignore
    print(f"Received frame: {frame}")

mira = MiraEdge(on_receive=on_receive)
mira.connect_to_gateway() # via UART

while True:
    time.sleep(1)
    mira.send_frame(dst=MIRA_BROADCAST_ADDRESS, payload=PayloadNodeStatus())

#     for node in mira.nodes:
#         mira.send_frame(dst=node.address, payload=b"Hello, World!")


mira.disconnect_from_gateway()
