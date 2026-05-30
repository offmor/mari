"""Tests for MQTTAdapter URL parsing and credential handling."""

from marilib.communication_adapter import MQTTAdapter


def test_from_url_plain():
    a = MQTTAdapter.from_url("mqtt://localhost:1883", is_edge=True)
    assert a.host == "localhost"
    assert a.port == 1883
    assert a.use_tls is False
    assert a.username is None
    assert a.password is None


def test_from_url_tls():
    a = MQTTAdapter.from_url("mqtts://argus.paris.inria.fr:8883", is_edge=False)
    assert a.host == "argus.paris.inria.fr"
    assert a.port == 8883
    assert a.use_tls is True


def test_from_url_with_embedded_credentials():
    # A userinfo prefix must not break the host:port split.
    a = MQTTAdapter.from_url("mqtts://alice:s3cret@argus:8883", is_edge=False)
    assert a.host == "argus"
    assert a.port == 8883
    assert a.username == "alice"
    assert a.password == "s3cret"


def test_from_url_explicit_credentials_override_url():
    a = MQTTAdapter.from_url(
        "mqtts://urluser:urlpass@argus:8883",
        is_edge=False,
        username="envuser",
        password="envpass",
    )
    # Explicit (env-fed) credentials win over URL-embedded ones.
    assert a.username == "envuser"
    assert a.password == "envpass"


def test_from_url_explicit_credentials_without_url_userinfo():
    a = MQTTAdapter.from_url("mqtts://argus:8883", is_edge=False, username="alice", password="pw")
    assert a.username == "alice"
    assert a.password == "pw"


def test_from_url_rejects_bad_scheme():
    import pytest

    with pytest.raises(ValueError):
        MQTTAdapter.from_url("http://nope:1", is_edge=True)


def test_constructor_credentials_default_none():
    a = MQTTAdapter("h", 1883, is_edge=True)
    assert a.username is None
    assert a.password is None
