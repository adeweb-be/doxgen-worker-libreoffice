from doxgen_libreoffice_worker.core.responses import handle_404
from doxgen_libreoffice_worker.core.routes import ROUTES


async def main(scope, receive, send):
    path = scope["path"]
    handler = ROUTES.get(path, handle_404)
    await handler(scope, receive, send)
