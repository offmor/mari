from marilib.mari_protocol import Frame, Header, MARI_BROADCAST_ADDRESS
from marilib.model import EdgeEvent

header = Header(destination=MARI_BROADCAST_ADDRESS)
frame = Frame(header=header, payload=b"NORMAL_APP_DATA")
frame_to_send = EdgeEvent.to_bytes(EdgeEvent.NODE_DATA) + frame.to_bytes()
print(frame_to_send.hex())
