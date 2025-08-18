from marilib.mari_protocol import Frame, Header

header = Header(destination=0x0000000000000001)

frame = Frame(header=header, payload=b"A" * 10)
print(frame.to_bytes().hex())
