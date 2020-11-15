from doxgen_libreoffice_worker.core.responses import handle_404, response_header


class Health:
    state = "healthy"


async def healthcheck_view(scope, receive, send):
    if scope["method"] != "GET":
        return await handle_404(scope, receive, send)
    if Health.state != "healthy":
        await send(response_header('text', 500))
        return await send(
            {"type": "http.response.body", "body": bytes(Health.state, "utf-8"), "more_body": False}
        )
    await send(response_header('text', 200))
    return await send(
        {"type": "http.response.body", "body": bytes(Health.state, "utf-8"), "more_body": False}
    )
