from litestar import Response

async def after_habit_get_request(response: Response) -> Response:
    return Response(content={"habits": response.content})