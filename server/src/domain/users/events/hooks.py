from litestar import Response

async def after_event_get_request(response: Response) -> Response:
    return Response(content={"events": response.content})