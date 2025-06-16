import time
from mira_edge.mira_edge import MiraEdge
from mira_edge.protocol import Frame, MIRA_BROADCAST_ADDRESS


def on_receive(frame: Frame):
    print(f"Received frame: {frame}")

mira = MiraEdge(on_receive=on_receive)
mira.connect_to_gateway() # via UART

for i in range(3):
    payload = b"aaa aaa aaa"
    print(f"Sending broadcast frame: {payload}")
    mira.send_frame(dst=MIRA_BROADCAST_ADDRESS, payload=payload)
    time.sleep(1)

    # for node in mira.nodes:
    #     mira.send_frame(dst=node.address, payload=b"Hello, World!")


mira.disconnect_from_gateway()
