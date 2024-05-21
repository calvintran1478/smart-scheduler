from litestar import Response

async def after_tag_get_request(response: Response) -> Response:
    return Response(content={"tags": response.content})