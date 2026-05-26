from marilib.mari_protocol import Frame, Header, NextProto


def test_header_size():
    assert Header().size == 21


def test_header_roundtrip_next_proto_dotbot():
    """Sender sets next_proto=DOTBOT_APP, receiver reads it back unchanged."""
    h = Header(destination=0x1234, next_proto=NextProto.DOTBOT_APP)
    parsed = Header().from_bytes(h.to_bytes())
    assert parsed.next_proto == NextProto.DOTBOT_APP
    assert parsed.destination == 0x1234


def test_header_roundtrip_next_proto_ipv6():
    """IPV6 round-trip — confirms the enum carries non-mari values."""
    h = Header(next_proto=NextProto.IPV6)
    parsed = Header().from_bytes(h.to_bytes())
    assert parsed.next_proto == NextProto.IPV6


def test_header_repr_handles_unknown_next_proto():
    """An out-of-enum next_proto value renders as hex without raising."""
    h = Header(next_proto=0x42)
    s = repr(h)
    assert "next_proto=0x42" in s


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
