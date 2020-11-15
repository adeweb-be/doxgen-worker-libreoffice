async def handle_404(scope, receive, send):
    content = b"Not found"
    await send(response_header('text', 404))
    return await send({"type": "http.response.body", "body": content, "more_body": False})


def response_header(response_type, code):
    if response_type == 'json':
        return {
            "type": "http.response.start",
            "status": code,
            "headers": [
                [b"content-type", b"application/json"],
            ],
        }
    if response_type == 'text':
        return {
            "type": "http.response.start",
            "status": code,
            "headers": [
                [b"content-type", b"text/plain; charset=utf-8"],
            ],
        }
