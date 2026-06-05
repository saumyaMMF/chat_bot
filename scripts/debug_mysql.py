"""Direct aiomysql connect probe — bypass app code, see raw error."""
from __future__ import annotations

import asyncio
import os
import ssl as ssl_module
import traceback
from pathlib import Path

from dotenv import load_dotenv
import aiomysql

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

URL = os.environ["CHATBOT_MYSQL_RO_URL"]


async def probe(label: str, **kwargs):
    print(f"\n--- {label} ---")
    print(f"  args: {dict(kwargs, password='***')}")
    try:
        conn = await aiomysql.connect(**kwargs, connect_timeout=10)
        await conn.ensure_closed()
        print("  OK")
    except Exception as exc:
        print(f"  FAIL: {type(exc).__name__}: {exc}")
        traceback.print_exc()


async def main():
    from urllib.parse import urlsplit
    u = urlsplit(URL)
    host = u.hostname
    port = u.port or 3306
    user = u.username
    pw = u.password
    db = (u.path or "/").lstrip("/")

    # 1. no SSL
    await probe("no-ssl", host=host, port=port, user=user, password=pw, db=db)

    # 2. SSL no-verify
    ctx = ssl_module.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl_module.CERT_NONE
    await probe("ssl-no-verify", host=host, port=port, user=user, password=pw, db=db, ssl=ctx)

    # 3. SSL default
    ctx2 = ssl_module.create_default_context()
    await probe("ssl-strict", host=host, port=port, user=user, password=pw, db=db, ssl=ctx2)

    # 4. explicit IP
    import socket
    ip = socket.gethostbyname(host)
    print(f"\n  resolved {host} -> {ip}")
    ctx3 = ssl_module.create_default_context()
    ctx3.check_hostname = False
    ctx3.verify_mode = ssl_module.CERT_NONE
    await probe("ssl-by-ip", host=ip, port=port, user=user, password=pw, db=db, ssl=ctx3)


asyncio.run(main())
