"""Shared aiogram session configuration.

api.telegram.org is dual-stack (A + AAAA), but this server's IPv6 route to it
is a black hole: TCP to the IPv4 address connects fine, while the IPv6 address
hangs until timeout. aiohttp (used by aiogram) would try the AAAA address and
stall, which crash-looped the bot on `set_my_commands` with TelegramNetworkError
"Request timeout error". Pinning the connector to IPv4 avoids the dead AAAA path.

Use `make_ipv4_session()` for every Bot (the polling bot AND the API-process
push bots). Each Bot owns its session lifecycle, so a fresh instance is returned
on every call.
"""
import socket

from aiogram.client.session.aiohttp import AiohttpSession


def make_ipv4_session(timeout: float | None = None) -> AiohttpSession:
    """A fresh aiogram HTTP session whose TCP connector is pinned to IPv4.

    Pass ``timeout`` (seconds) to bound every HTTP request. The API-process push
    bot uses this so a flaky/unreachable api.telegram.org can't stall a request
    for aiogram's 60s default. Leave as ``None`` for the long-polling bot — it
    sets its own per-request timeout for ``get_updates`` and must not be capped
    to a few seconds, or long-polling would error on every cycle.
    """
    session = AiohttpSession() if timeout is None else AiohttpSession(timeout=timeout)
    # aiogram builds `TCPConnector(**_connector_init)` inside create_session();
    # adding family=AF_INET forces IPv4-only resolution/connection.
    session._connector_init["family"] = socket.AF_INET
    return session
