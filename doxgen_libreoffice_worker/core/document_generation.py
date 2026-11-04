import asyncio
import json
import os

from appy.pod import PodError
from asgiref.sync import sync_to_async

from doxgen_libreoffice_worker.core.health import Health
from doxgen_libreoffice_worker.core.responses import response_header, handle_404
from doxgen_libreoffice_worker.core.sandbox import SafeRenderer
from doxgen_libreoffice_worker.core.security import InvalidRequest, check_template, is_authorized, storage_path


@sync_to_async
def generate(template_file, generation_context, destination_file):
    check_template(template_file)
    renderer = SafeRenderer(
        template_file,
        generation_context,
        destination_file,
        pythonWithUnoPath=os.getenv("PYTHON_WITH_UNO_PATH", default=""),
        ooServer="localhost",
        ooPort=2002,
        stream=False,
        overwriteExisting=True,
    )
    renderer.run()


async def read_body(receive):
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body


async def send_failure(send, error, status=500):
    await send(response_header('json', status))
    return await send(
        {
            "type": "http.response.body",
            "body": bytes(json.dumps({"status": "failure", "error": error}), "utf-8"),
            "more_body": False,
        }
    )


GENERATION_LOCK = asyncio.Lock()


async def document_generation_view(scope, receive, send):
    if scope["method"] != "POST":
        return await handle_404(scope, receive, send)
    if not is_authorized(scope):
        return await send_failure(send, "Unauthorized", status=401)

    payload = json.loads((await read_body(receive)).decode("utf-8"))
    generation_context = payload["generation_context"]
    try:
        template_file = storage_path(payload["template_path"])
        destination_file = storage_path(payload["destination_path"])
    except InvalidRequest as e:
        return await send_failure(send, str(e), status=400)
    async with GENERATION_LOCK:
        try:
            await asyncio.wait_for(
                generate(template_file, generation_context, destination_file),
                timeout=int(os.getenv("GENERATION_TIMEOUT", default=120)),
            )
        except TimeoutError:
            # LibreOffice is probably stuck
            Health.state = "unhealthy"
            return await send_failure(send, "Generation timed out")
        except InvalidRequest as e:
            return await send_failure(send, str(e), status=400)
        except PodError as e:
            return await send_failure(send, str(e))

    await send(response_header('json', 200))
    return await send(
        {
            "type": "http.response.body",
            "body": bytes(json.dumps({"status": "success"}), "utf-8"),
            "more_body": False,
        }
    )
