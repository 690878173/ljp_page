"""SOCKS5 代理转发器 — 转发到远程的本地无身份验证代理
经过身份验证的 SOCKS5 代理。

Chrome/Chromium 本身不支持 SOCKS5 身份验证
（Chromium 问题#40323993）。该模块通过以下方式解决了该限制
运行轻量级本地 SOCKS5 代理（无需身份验证）
代表使用用户名/密码执行 SOCKS5 握手
浏览器。

数据流：
    Chrome ──► localhost:{local_port} (无授权)
                    │
              SOCKS5转发器
                    │（通过远程验证）
                    ▼
           远程主机：远程端口（用户/密码身份验证）
                    │
                    ▼
              目的服务器

用作 CLI：
    python -m pydoll.utils.socks5_proxy_forwarder \\
        --远程主机 proxy.example.com \\
        --远程端口1080 \\
        --用户名 myuser \\
        --密码 mypass \\
        --本地端口1081

与 Pydoll 一起使用：
    导入异步
    从 pydoll.utils 导入 SOCKS5Forwarder
    从 pydoll.browser.chromium 导入 Chrome
    从 pydoll.browser.options 导入 ChromiumOptions

    异步 def main():
        转发器 = SOCKS5转发器(
            remote_host='proxy.example.com',
            远程端口=1080，
            用户名='myuser',
            密码='我的密码',
            本地端口=1081，
        ）
        与转发器异步：
            选项 = ChromiumOptions()
            options.add_argument('--proxy-server=socks5://127.0.0.1:1081')
            与 Chrome(options=options) 异步浏览器：
                tab = 等待浏览器.start()
                等待 tab.go_to('https://httpbin.org/ip')

    asyncio.run（主（））

要求：Python >= 3.10，无外部依赖。"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import signal
import struct
from types import TracebackType
from ljp_page.logger import loguru_logger

__all__ = ['_suppress_closed', 'SOCKS5Forwarder', '_HandshakeError']

SOCKS5_VERSION = 0x05
AUTH_NO_AUTH = 0x00
AUTH_USERNAME_PASSWORD = 0x02
AUTH_NO_ACCEPTABLE = 0xFF

CMD_CONNECT = 0x01

ATYP_IPV4 = 0x01
ATYP_DOMAIN = 0x03
ATYP_IPV6 = 0x04

REPLY_SUCCESS = 0x00
REPLY_GENERAL_FAILURE = 0x01
REPLY_CONNECTION_REFUSED = 0x05
REPLY_COMMAND_NOT_SUPPORTED = 0x07
REPLY_ADDRESS_TYPE_NOT_SUPPORTED = 0x08

BUFFER_SIZE = 65536
HANDSHAKE_TIMEOUT = 30
MAX_CREDENTIAL_BYTES = 255


class _suppress_closed:
    """微型上下文管理器，可以消除已经关闭的传输上的错误。"""

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        return exc_type is not None and issubclass(exc_type, OSError)


async def _close_writer(writer: asyncio.StreamWriter) -> None:
    """关闭流写入器并等待传输完成。"""
    with _suppress_closed():
        writer.close()
        await writer.wait_closed()


async def _pipe(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    label: str,
) -> None:
    """将数据从*读取器*转发到*写入器*直到EOF。"""
    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        await _close_writer(writer)


class SOCKS5Forwarder:
    """转发到经过身份验证的远程的本地 SOCKS5 代理（无身份验证）
    SOCKS5 代理。

    可以用作异步上下文管理器::

        与 SOCKS5Forwarder(...) 异步作为转发：
            # fwd.local_port 现在正在监听
            ..."""

    def __init__(
        self,
        remote_host: str,
        remote_port: int,
        username: str,
        password: str,
        local_host: str = '127.0.0.1',
        local_port: int = 0,
    ) -> None:
        if len(username.encode()) > MAX_CREDENTIAL_BYTES:
            raise ValueError('SOCKS5 username must be at most 255 bytes (UTF-8 encoded)')
        if len(password.encode()) > MAX_CREDENTIAL_BYTES:
            raise ValueError('SOCKS5 password must be at most 255 bytes (UTF-8 encoded)')
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.username = username
        self.password = password
        self.local_host = local_host
        self.local_port = local_port
        self._server: asyncio.Server | None = None

    async def __aenter__(self) -> SOCKS5Forwarder:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()

    async def start(self) -> None:
        """开始接受 *local_host*:*local_port* 上的连接。"""
        try:
            addr = ipaddress.ip_address(self.local_host)
        except ValueError:
            addr = None

        if addr is not None and not addr.is_loopback:
            loguru_logger.warning(
                'Binding to non-loopback address %s — the forwarder will be '
                'accessible from the network without authentication!',
                self.local_host,
            )
        elif addr is None and self.local_host != 'localhost':
            loguru_logger.debug(
                'local_host=%r is not an IP literal; skipping loopback check',
                self.local_host,
            )
        self._server = await asyncio.start_server(
            self._handle_client,
            self.local_host,
            self.local_port,
        )
        sockets = list(self._server.sockets or [])
        ports = {s.getsockname()[1] for s in sockets}
        if len(ports) != 1:
            await self.stop()
            raise RuntimeError(
                f'start_server created sockets with different ports: {sorted(ports)}. '
                "Use an explicit IP (e.g. '127.0.0.1' or '::1') instead of a hostname, "
                'or specify --local-port explicitly.'
            )
        self.local_port = ports.pop()
        loguru_logger.info(
            'SOCKS5 forwarder listening on %s:%s -> %s:%s',
            self.local_host,
            self.local_port,
            self.remote_host,
            self.remote_port,
        )

    async def stop(self) -> None:
        """优雅地关闭服务器。"""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            loguru_logger.info('SOCKS5 forwarder stopped')

    async def serve_forever(self) -> None:
        """阻止直到服务器关闭（对于 CLI 模式有用）。"""
        if self._server is None:
            raise RuntimeError('Server not started — call start() first')
        async with self._server:
            await self._server.serve_forever()

    async def _handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ) -> None:
        """处理一个传入的浏览器连接。"""
        remote_writer: asyncio.StreamWriter | None = None
        try:
            addr_payload, dest_port = await self._accept_local_handshake(
                client_reader,
                client_writer,
            )
            r_reader, r_writer = await asyncio.wait_for(
                asyncio.open_connection(self.remote_host, self.remote_port),
                timeout=HANDSHAKE_TIMEOUT,
            )
            remote_writer = r_writer
            await self._remote_handshake(
                r_reader,
                r_writer,
                addr_payload,
                dest_port,
            )
            await self._send_reply(client_writer, REPLY_SUCCESS)
            await asyncio.gather(
                _pipe(client_reader, r_writer, 'client->remote'),
                _pipe(r_reader, client_writer, 'remote->client'),
            )
        except _HandshakeError as exc:
            loguru_logger.warning('Handshake failed: %s', exc)
            if exc.send_reply:
                with _suppress_closed():
                    await self._send_reply(client_writer, exc.reply_code)
        except asyncio.TimeoutError:
            loguru_logger.warning('Connection to remote proxy timed out')
            with _suppress_closed():
                await self._send_reply(client_writer, REPLY_GENERAL_FAILURE)
        except (ConnectionRefusedError, OSError) as exc:
            loguru_logger.warning('Connection to remote proxy failed: %s', exc)
            reply = (
                REPLY_CONNECTION_REFUSED
                if isinstance(exc, ConnectionRefusedError)
                else REPLY_GENERAL_FAILURE
            )
            with _suppress_closed():
                await self._send_reply(client_writer, reply)
        except asyncio.CancelledError:
            raise
        except Exception:
            loguru_logger.exception('Unexpected error in client handler')
        finally:
            await _close_writer(client_writer)
            if remote_writer is not None:
                await _close_writer(remote_writer)

    async def _accept_local_handshake(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> tuple[bytes, int]:
        """接受来自 Chrome 的 SOCKS5 问候语（无身份验证）并阅读
        连接请求。

        返回 ``(addr_payload, dest_port)`` 其中 *addr_payload* 是原始数据
        SOCKS5 地址字段（ATYP 字节 + 地址字节）与 Chrome 完全相同
        已发送，准备好逐字转发到远程代理。"""
        try:
            header = await _read_exact(reader, 2, peer='client')
        except _HandshakeError as exc:
            raise _HandshakeError(str(exc), send_reply=False) from exc
        version, nmethods = header[0], header[1]
        if version != SOCKS5_VERSION:
            raise _HandshakeError(
                f'Unsupported SOCKS version from client: {version}', send_reply=False
            )

        try:
            methods = await _read_exact(reader, nmethods, peer='client')
        except _HandshakeError as exc:
            raise _HandshakeError(str(exc), send_reply=False) from exc
        if AUTH_NO_AUTH not in methods:
            writer.write(bytes([SOCKS5_VERSION, AUTH_NO_ACCEPTABLE]))
            await writer.drain()
            raise _HandshakeError('Client does not offer no-auth method', send_reply=False)

        writer.write(bytes([SOCKS5_VERSION, AUTH_NO_AUTH]))
        await writer.drain()

        req = await _read_exact(reader, 4, peer='client')
        if req[0] != SOCKS5_VERSION:
            raise _HandshakeError('Bad SOCKS version in request')
        if req[1] != CMD_CONNECT:
            raise _HandshakeError(
                f'Unsupported command: {req[1]}',
                reply_code=REPLY_COMMAND_NOT_SUPPORTED,
            )

        atyp = req[3]
        addr_payload = await self._read_raw_address(reader, atyp, peer='client')
        dest_port = struct.unpack('!H', await _read_exact(reader, 2, peer='client'))[0]
        loguru_logger.debug('Client CONNECT to %s port %d', addr_payload.hex(), dest_port)
        return addr_payload, dest_port

    async def _remote_handshake(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        addr_payload: bytes,
        dest_port: int,
    ) -> None:
        """与远程代理执行完整的 SOCKS5 握手，包括
        用户名/密码验证，然后发送 CONNECT 请求。

        *addr_payload* 是来自客户端的原始 ATYP + 地址字节，
        逐字转发，以便保留地址类型。"""
        greeting = bytes([SOCKS5_VERSION, 0x02, AUTH_NO_AUTH, AUTH_USERNAME_PASSWORD])
        writer.write(greeting)
        await writer.drain()
        loguru_logger.debug('-> greeting: %s', greeting.hex())

        resp = await _read_exact(reader, 2, peer='remote proxy')
        loguru_logger.debug('<- method selection: %s', resp.hex())

        if resp[0] != SOCKS5_VERSION:
            raise _HandshakeError(f'Remote proxy bad version (response: {resp.hex()})')

        selected_method = resp[1]
        if selected_method == AUTH_NO_ACCEPTABLE:
            raise _HandshakeError('Remote proxy rejected all auth methods')

        if selected_method == AUTH_USERNAME_PASSWORD:
            uname = self.username.encode()
            passwd = self.password.encode()
            auth_req = bytes([0x01, len(uname)]) + uname + bytes([len(passwd)]) + passwd
            writer.write(auth_req)
            await writer.drain()
            loguru_logger.debug('-> auth request: ulen=%d plen=%d', len(uname), len(passwd))

            auth_resp = await _read_exact(reader, 2, peer='remote proxy')
            loguru_logger.debug('<- auth response: %s', auth_resp.hex())
            if auth_resp[1] != 0x00:
                raise _HandshakeError(
                    f'Remote proxy authentication failed (status: {auth_resp[1]:#04x})'
                )
        elif selected_method == AUTH_NO_AUTH:
            loguru_logger.debug('Remote proxy selected no-auth (0x00)')
        else:
            raise _HandshakeError(
                f'Remote proxy selected unsupported method: {selected_method:#04x}'
            )

        connect_req = bytes([SOCKS5_VERSION, CMD_CONNECT, 0x00])
        connect_req += addr_payload
        connect_req += struct.pack('!H', dest_port)
        writer.write(connect_req)
        await writer.drain()
        loguru_logger.debug('-> CONNECT: %s', connect_req.hex())

        reply_header = await _read_exact(reader, 4, peer='remote proxy')
        loguru_logger.debug('<- reply header: %s', reply_header.hex())

        rep = reply_header[1]
        if rep != REPLY_SUCCESS:
            extra = b''
            try:
                extra = await asyncio.wait_for(reader.read(256), timeout=0.5)
            except (asyncio.TimeoutError, OSError):
                pass
            raise _HandshakeError(
                f'Remote proxy CONNECT failed '
                f'(rep={rep:#04x}, reply: {reply_header.hex()}, '
                f'extra: {extra.hex() if extra else "none"})',
                reply_code=rep,
            )

        atyp = reply_header[3]
        await self._read_raw_address(reader, atyp, peer='remote proxy')
        await _read_exact(reader, 2, peer='remote proxy')

    @staticmethod
    async def _read_raw_address(
        reader: asyncio.StreamReader,
        atyp: int,
        *,
        peer: str = 'peer',
    ) -> bytes:
        """读取 SOCKS5 地址字段并返回原始字节，包括
        ATYP 前缀，适合逐字转发到另一个代理。"""
        if atyp == ATYP_IPV4:
            raw = await _read_exact(reader, 4, peer=peer)
            return bytes([atyp]) + raw
        if atyp == ATYP_DOMAIN:
            length_byte = await _read_exact(reader, 1, peer=peer)
            domain = await _read_exact(reader, length_byte[0], peer=peer)
            return bytes([atyp]) + length_byte + domain
        if atyp == ATYP_IPV6:
            raw = await _read_exact(reader, 16, peer=peer)
            return bytes([atyp]) + raw
        raise _HandshakeError(
            f'Unsupported address type: {atyp}',
            reply_code=REPLY_ADDRESS_TYPE_NOT_SUPPORTED,
        )

    @staticmethod
    async def _send_reply(
        writer: asyncio.StreamWriter,
        reply_code: int,
    ) -> None:
        """向客户端发送最小的 SOCKS5 回复。"""
        writer.write(
            bytes([
                SOCKS5_VERSION,
                reply_code,
                0x00,
                ATYP_IPV4,
                0,
                0,
                0,
                0,
                0,
                0,
            ])
        )
        await writer.drain()


class _HandshakeError(Exception):
    """当 SOCKS5 握手步骤失败时引发。"""

    def __init__(
        self,
        message: str,
        reply_code: int = REPLY_GENERAL_FAILURE,
        send_reply: bool = True,
    ) -> None:
        super().__init__(message)
        self.reply_code = reply_code
        self.send_reply = send_reply


async def _read_exact(reader: asyncio.StreamReader, n: int, *, peer: str = 'peer') -> bytes:
    """准确读取 *n* 个字节或引发“_HandshakeError”。"""
    try:
        return await asyncio.wait_for(reader.readexactly(n), timeout=HANDSHAKE_TIMEOUT)
    except asyncio.IncompleteReadError as exc:
        raise _HandshakeError(
            f'Connection closed prematurely (expected {n} bytes, '
            f'got {len(exc.partial)} from {peer})'
        ) from exc
    except asyncio.TimeoutError as exc:
        raise _HandshakeError(
            f'Timed out reading {n} bytes from {peer}',
        ) from exc


async def _skip_bnd_address(reader: asyncio.StreamReader, atyp: int, *, peer: str = 'peer') -> None:
    """使用 SOCKS5 回复中的 BND.ADDR + BND.PORT。"""
    if atyp == ATYP_IPV4:
        await _read_exact(reader, 4 + 2, peer=peer)
    elif atyp == ATYP_DOMAIN:
        length = (await _read_exact(reader, 1, peer=peer))[0]
        await _read_exact(reader, length + 2, peer=peer)
    elif atyp == ATYP_IPV6:
        await _read_exact(reader, 16 + 2, peer=peer)


async def _main(args: argparse.Namespace) -> None:
    forwarder = SOCKS5Forwarder(
        remote_host=args.remote_host,
        remote_port=args.remote_port,
        username=args.username,
        password=args.password,
        local_host=args.local_host,
        local_port=args.local_port,
    )
    await forwarder.start()

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set_result, None)
    except NotImplementedError:
        pass  #Windows / ProactorEventLoop — 回退到 KeyboardInterrupt

    loguru_logger.info(
        'Forwarding socks5://127.0.0.1:%s -> socks5://%s:***@%s:%s',
        forwarder.local_port,
        args.username,
        args.remote_host,
        args.remote_port,
    )
    loguru_logger.info('Press Ctrl+C to stop.')

    try:
        await stop
    finally:
        await forwarder.stop()


async def _test_negotiate_auth(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    username: str,
    password: str,
) -> bool:
    """对 --test 诊断执行问候语 + 身份验证。成功则返回 True。"""
    greeting = bytes([SOCKS5_VERSION, 0x02, AUTH_NO_AUTH, AUTH_USERNAME_PASSWORD])
    writer.write(greeting)
    await writer.drain()
    loguru_logger.info('-> Greeting:  %s', greeting.hex())

    resp = await asyncio.wait_for(reader.readexactly(2), timeout=10)
    loguru_logger.info('<- Method:    %s  (selected method: %#04x)', resp.hex(), resp[1])

    if resp[0] != SOCKS5_VERSION:
        loguru_logger.error('Bad version byte: %#04x', resp[0])
        return False

    if resp[1] == AUTH_USERNAME_PASSWORD:
        uname = username.encode()
        passwd = password.encode()
        auth_req = bytes([0x01, len(uname)]) + uname + bytes([len(passwd)]) + passwd
        writer.write(auth_req)
        await writer.drain()
        loguru_logger.info('-> Auth:      ulen=%d plen=%d', len(uname), len(passwd))

        auth_resp = await asyncio.wait_for(reader.readexactly(2), timeout=10)
        loguru_logger.info('<- Auth resp: %s  (status: %#04x)', auth_resp.hex(), auth_resp[1])
        if auth_resp[1] != 0x00:
            loguru_logger.error('Authentication rejected')
            return False
        loguru_logger.info('Authentication succeeded')
    elif resp[1] == AUTH_NO_AUTH:
        loguru_logger.info('Proxy selected no-auth')
    elif resp[1] == AUTH_NO_ACCEPTABLE:
        loguru_logger.error('Proxy rejected all auth methods')
        return False

    return True


async def _test_connect_and_verify(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> bool:
    """将 CONNECT 发送到 httpbin.org:80 并使用 HTTP 请求进行验证。"""
    target = b'httpbin.org'
    connect_req = (
        bytes([SOCKS5_VERSION, CMD_CONNECT, 0x00, ATYP_DOMAIN, len(target)])
        + target
        + struct.pack('!H', 80)
    )
    writer.write(connect_req)
    await writer.drain()
    loguru_logger.info('-> CONNECT:   %s  (httpbin.org:80)', connect_req.hex())

    reply = await asyncio.wait_for(reader.readexactly(4), timeout=15)
    loguru_logger.info('<- Reply:     %s  (rep: %#04x)', reply.hex(), reply[1])

    if reply[1] != REPLY_SUCCESS:
        extra = b''
        try:
            extra = await asyncio.wait_for(reader.read(256), timeout=1)
        except (asyncio.TimeoutError, OSError):
            pass
        loguru_logger.error('CONNECT rejected — reply code %#04x', reply[1])
        if extra:
            loguru_logger.error('Extra data: %s', extra.hex())
        loguru_logger.error(
            'Possible causes: invalid/expired credentials, quota exceeded, '
            'IP not whitelisted, or wrong port'
        )
        return False

    await _skip_bnd_address(reader, reply[3], peer='remote proxy')
    loguru_logger.info('CONNECT established')

    http_req = b'GET /ip HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n'
    writer.write(http_req)
    await writer.drain()
    loguru_logger.info('-> HTTP GET /ip sent')

    http_resp = await asyncio.wait_for(reader.read(4096), timeout=15)
    decoded = http_resp.decode(errors='replace')
    loguru_logger.info('<- HTTP response (%d bytes):\n%s', len(http_resp), decoded)
    loguru_logger.info('Proxy is fully working!')
    return True


async def _test_proxy(args: argparse.Namespace) -> None:
    """对远程代理执行直接 SOCKS5 握手测试。"""
    loguru_logger.info('=== SOCKS5 Direct Test: %s:%s ===', args.remote_host, args.remote_port)

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(args.remote_host, args.remote_port),
            timeout=HANDSHAKE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        loguru_logger.error('TCP connection timed out')
        return
    except OSError as exc:
        loguru_logger.error('TCP connection failed: %s', exc)
        return

    loguru_logger.info('TCP connection established')

    try:
        if not await _test_negotiate_auth(reader, writer, args.username, args.password):
            return
        await _test_connect_and_verify(reader, writer)
    except _HandshakeError as exc:
        loguru_logger.error('SOCKS5 test failed: %s', exc)
    except asyncio.TimeoutError:
        loguru_logger.error('Timed out waiting for proxy response')
    except asyncio.IncompleteReadError as exc:
        loguru_logger.error('Connection closed prematurely (got %d bytes)', len(exc.partial))
    except OSError as exc:
        loguru_logger.error('Network error: %s', exc)
    finally:
        await _close_writer(writer)


def cli() -> None:
    parser = argparse.ArgumentParser(
        description='Local SOCKS5 forwarder for authenticated remote proxies.',
    )
    parser.add_argument('--remote-host', required=True, help='Remote SOCKS5 proxy host')
    parser.add_argument('--remote-port', type=int, default=1080, help='Remote SOCKS5 proxy port')
    parser.add_argument('--username', required=True, help='Remote proxy username')
    parser.add_argument('--password', required=True, help='Remote proxy password')
    parser.add_argument('--local-host', default='127.0.0.1', help='Local bind address')
    parser.add_argument('--local-port', type=int, default=1081, help='Local bind port (0 = random)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable debug logging')
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test the remote proxy directly (no local server, no Chrome needed)',
    )
    args = parser.parse_args()

    if args.test:
        asyncio.run(_test_proxy(args))
    else:
        asyncio.run(_main(args))


if __name__ == '__main__':
    cli()
