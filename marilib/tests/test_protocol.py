from marilib.mari_protocol import Frame, Header, NextProto


def test_header_size():
    assert Header().size == 21


def test_header_from_bytes():
    header = Header().from_bytes(
        bytes.fromhex("0210170059291ba8fdcecef531eb7f2526ef039901f0f0f0f0f0")[0:21]
    )
    assert header.version == 2
    assert header.type_ == 16
    assert header.network_id == 23
    assert header.destination == int.from_bytes(
        bytes.fromhex("59291ba8fdcecef5"), byteorder="little"
    )
    assert header.source == int.from_bytes(bytes.fromhex("31eb7f2526ef0399"), byteorder="little")
    assert header.next_proto == NextProto.MARI_INTERNAL


def test_frame_from_bytes():
    frame = Frame().from_bytes(
        bytes.fromhex("0210170059291ba8fdcecef531eb7f2526ef039901f0f0f0f0f0")
    )
    assert frame.header.version == 2
    assert frame.header.type_ == 16
    assert frame.header.network_id == 23
    assert frame.header.destination == int.from_bytes(
        bytes.fromhex("59291ba8fdcecef5"), byteorder="little"
    )
    assert frame.header.source == int.from_bytes(
        bytes.fromhex("31eb7f2526ef0399"), byteorder="little"
    )
    assert frame.header.next_proto == NextProto.MARI_INTERNAL
    assert frame.payload == bytes.fromhex("f0f0f0f0f0")
