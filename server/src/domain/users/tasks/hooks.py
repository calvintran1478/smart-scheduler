from litestar import Response

async def after_task_get_request(response: Response) -> Response:
    return Response(content={"tasks": response.content})