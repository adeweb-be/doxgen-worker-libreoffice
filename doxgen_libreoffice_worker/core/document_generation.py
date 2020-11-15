import asyncio
import json
import os

from appy.pod import PodError
from asgiref.sync import sync_to_async
from appy.pod.renderer import Renderer

from doxgen_libreoffice_worker.core.health import Health
from doxgen_libreoffice_worker.core.responses import response_header, handle_404


@sync_to_async
def generate(template_path, generation_context, destination_path):
    renderer = Renderer(
        "/storage/" + template_path,
        generation_context,
        "/storage/" + destination_path,
        pythonWithUnoPath=os.getenv("PYTHON_WITH_UNO_PATH", default=""),
        ooServer="localhost",
        ooPort=2002,
        stream=False,
        overwriteExisting=True,
    )
    renderer.run()


GENERATION_LOCK = asyncio.Lock()


async def document_generation_view(scope, receive, send):
    if scope["method"] != "POST":
        return await handle_404(scope, receive, send)

    received = await receive()
    payload = json.loads(received["body"].decode("utf-8"))
    template_path = payload["template_path"]
    generation_context = payload["generation_context"]
    destination_path = payload["destination_path"]
    try:
        await GENERATION_LOCK.acquire()
        await asyncio.wait_for(
            generate(template_path, generation_context, destination_path),
            timeout=int(os.getenv("GENERATION_TIMEOUT", default=120)),
        )
    except TimeoutError as e:
        # LibreOffice is probably stuck
        Health.state = "unhealthy"
        await send(response_header('json', 500))
        return await send(
            {
                "type": "http.response.body",
                "body": bytes(json.dumps({"status": "failure", "error": e}), "utf-8"),
                "more_body": False,
            }
        )
    except PodError as e:
        await send(response_header('json', 500))
        return await send(
            {
                "type": "http.response.body",
                "body": bytes(json.dumps({"status": "failure", "error": e}), "utf-8"),
                "more_body": False,
            }
        )
    finally:
        GENERATION_LOCK.release()

    await send(response_header('json', 200))
    return await send(
        {
            "type": "http.response.body",
            "body": bytes(json.dumps({"status": "success"}), "utf-8"),
            "more_body": False,
        }
    )
