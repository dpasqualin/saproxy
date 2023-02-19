import argparse
import logging
import uuid
from datetime import date, datetime, timezone

import aiohttp
import jwt
from aiohttp import web


def cli_parser() -> argparse.Namespace:
    """Parse CLI.

    :return: Namespace with CLI parameters set.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="Listening port", default=8080, type=int)
    parser.add_argument(
        "-v", "--verbose", help="Enable verbose mode", action="store_true"
    )
    return parser.parse_args()


def generate_jwt(user: str = "username") -> str:
    """Generate JWT for user.

    :param user: string with username.
    :return: string representation of jwt token.
    """
    # Secret is here for simplicity, in production it would be provided in some other
    # better/safer way.
    secret = (
        "a9ddbcaba8c0ac1a0a812dc0c2f08514b23f2db0a68343cb8199ebb38a6d91e4ebfb378e22ad39"
        "c2d01 d0b4ec9c34aa91056862ddace3fbbd6852ee60c36acbf"
    )
    payload = {
        # Registered claims
        "iat": datetime.now(tz=timezone.utc),
        "jti": str(uuid.uuid4()),
        # Private claims
        "user": user,
        "date": date.today().isoformat(),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


async def call_upstream(request: web.Request, my_jwt: str) -> tuple[int, str, bytes]:
    """Call upstream forwarding request body and params and adding JWT token.

    :param request: client original request.
    :param my_jwt: string representing the JWT token.
    :return: tuple with status code, content type and body.
    """
    body = await request.read() if request.body_exists else None
    headers = {"x-my-jwt": my_jwt}
    session = request.app["upstream_session"]
    async with session.post(
        "/post", data=body, params=request.query, headers=headers
    ) as resp:
        return resp.status, resp.content_type, await resp.read()


async def proxy_handler(request: web.Request) -> web.Response:
    """Call upstream and return response to the client.

    :param request: client request.
    :return: response.
    """
    my_jwt = generate_jwt()

    # Call upstream
    status, content_type, body = await call_upstream(request, my_jwt)

    # Update stats
    request.app["status"]["request_count"] += 1

    # Return to client
    return web.Response(
        status=status,
        content_type=content_type,
        body=body,
    )


async def status_handler(request: web.Request) -> web.Response:
    """Return app statistics.

    :param request: client request
    :return: json response with uptime and request count.
    """
    request_count = request.app["status"]["request_count"]
    start_ts = request.app["status"]["start_ts"]

    body = {
        "uptime": (datetime.now() - start_ts).total_seconds(),
        "request_count": request_count,
    }

    return web.json_response(body)


async def on_cleanup(app: web.Application) -> None:
    """Clean app before closing.

    :param app: application.
    """
    # Close upstream session
    await app["upstream_session"].close()


async def on_startup(app: web.Application) -> None:
    """Initialize app globals.

    :param app: application
    """
    # Create global status for request count
    app["status"] = {
        "start_ts": datetime.now(),
        "request_count": 0,
    }

    # Create a session with upstream for faster requests
    upstream_url = "https://postman-echo.com"
    app["upstream_session"] = aiohttp.ClientSession(base_url=upstream_url)


async def init_app() -> web.Application:
    """Initialize app.

    Setup routes and initialization routines.

    :return: application coroutine.
    """
    app = web.Application()

    app.router.add_route("GET", "/status", status_handler)
    # Route post to any path to proxy_handler
    app.router.add_route("POST", "/{tail:.*}", proxy_handler)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_cleanup)

    return app


if __name__ == "__main__":
    args = cli_parser()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    web.run_app(init_app(), port=args.port)
