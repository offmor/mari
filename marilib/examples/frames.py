from marilib.mari_protocol import Frame, Header
from marilib.model import EdgeEvent

header = Header(destination=0x0000000000000001)
frame = Frame(header=header, payload=b"A" * 10)
frame_to_send = EdgeEvent.to_bytes(EdgeEvent.NODE_DATA) + frame.to_bytes()
print(frame_to_send.hex())
