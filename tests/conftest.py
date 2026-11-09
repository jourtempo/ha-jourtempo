"""Fixtures communes."""

import sys

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Charge custom_components/ dans chaque test."""
    yield


if sys.platform == "win32":
    # Sous Windows, la boucle asyncio crée une paire de sockets locale : on
    # neutralise le blocage des sockets (les appels HTTP restent simulés).
    import pytest_socket

    pytest_socket.disable_socket = lambda *args, **kwargs: None
