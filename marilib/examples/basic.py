import time
from mira_edge.mira_edge import MiraEdge, EdgeEvent, MiraNode
from mira_edge.protocol import Frame, MIRA_BROADCAST_ADDRESS


def on_event(event: EdgeEvent, event_data: MiraNode | Frame):
    if event == EdgeEvent.NODE_JOINED:
        print(f"Node {event_data} joined")
    elif event == EdgeEvent.NODE_LEFT:
        print(f"Node {event_data} left")
    elif event == EdgeEvent.NODE_DATA:
        print(f"Got frame from {event_data.header.source}: {event_data.payload}")

mira = MiraEdge(on_event=on_event)
mira.connect_to_gateway() # via UART

for i in range(30):
    # payload = b"aaa aaa aaa"
    # print(f"Sending broadcast frame: {payload}")
    # mira.send_frame(dst=MIRA_BROADCAST_ADDRESS, payload=payload)
    time.sleep(1)

    for node in mira.nodes:
        mira.send_frame(dst=node.address_int, payload=b"Hello, World!")


mira.disconnect_from_gateway()
