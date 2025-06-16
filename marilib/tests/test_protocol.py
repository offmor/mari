from mira_edge.protocol import Header

def test_header_size():
    assert Header().size == 20
