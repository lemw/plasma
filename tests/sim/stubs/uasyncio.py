"""Compatibility shim: maps MicroPython `uasyncio` onto CPython `asyncio`.

Key adaptations
---------------
* `start_server` — redirects the listening port to WEB_TEST_PORT when set,
  and wraps the connection handler with a `_CompatWriter` so that str writes
  are transparently encoded to bytes (MicroPython's StreamWriter accepts str;
  CPython's does not).
* All other symbols are thin wrappers or direct re-exports of their asyncio
  equivalents.
"""

import asyncio
import os


async def sleep(secs):
    await asyncio.sleep(secs)


async def sleep_ms(ms):
    await asyncio.sleep(ms / 1000.0)


async def gather(*coros, **kwargs):
    return await asyncio.gather(*coros, **kwargs)


class _CompatWriter:
    """Wraps an asyncio.StreamWriter to accept both str and bytes.

    MicroPython's uasyncio.StreamWriter.write() accepts either type;
    the CPython equivalent requires bytes.  This adapter handles the
    conversion so application code runs unmodified in both environments.
    """

    def __init__(self, writer: asyncio.StreamWriter):
        self._writer = writer

    def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        return self._writer.write(data)

    async def drain(self):
        return await self._writer.drain()

    def close(self):
        return self._writer.close()

    async def wait_closed(self):
        return await self._writer.wait_closed()


async def start_server(callback, host, port):
    test_port = int(os.environ.get("WEB_TEST_PORT", 0))
    actual_port = test_port if test_port else port

    async def _compat_handler(reader, writer):
        await callback(reader, _CompatWriter(writer))

    await asyncio.start_server(_compat_handler, host, actual_port)


def run(coro):
    asyncio.run(coro)
