import time
from mira_edge.mira_edge import MiraEdge, EdgeEvent
from mira_edge.protocol import Frame, MIRA_BROADCAST_ADDRESS


def on_event(event: EdgeEvent, data: Frame | bytes):
    if event == EdgeEvent.NODE_JOINED:
        print(f"Node {data} joined")
    elif event == EdgeEvent.NODE_LEFT:
        print(f"Node {data} left")
    elif event == EdgeEvent.NODE_DATA:
        print(f"Got frame from {data.header.source}: {data.payload}")

mira = MiraEdge(on_event=on_event)
mira.connect_to_gateway() # via UART

for i in range(30):
    # payload = b"aaa aaa aaa"
    # print(f"Sending broadcast frame: {payload}")
    # mira.send_frame(dst=MIRA_BROADCAST_ADDRESS, payload=payload)
    time.sleep(1)

    for node in mira.nodes:
        mira.send_frame(dst=node, payload=b"Hello, World!")


mira.disconnect_from_gateway()
