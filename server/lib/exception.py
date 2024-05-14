from litestar import Request, Response
from litestar.exceptions import ClientException

def client_exception_handler(_: Request, exception: Exception) -> Response:
    status_code = getattr(exception, "status_code")
    detail = getattr(exception, "detail")

    return Response(content={"error": detail}, status_code=status_code)