from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, code: str, status: int, message: str, details: dict | None = None):
        self.code, self.status, self.message, self.details = code, status, message, details or {}


def _body(code: str, message: str, details: dict) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}  # platform.md 1.3


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(_: Request, e: ApiError):
        return JSONResponse(status_code=e.status, content=_body(e.code, e.message, e.details))

    @app.exception_handler(RequestValidationError)
    async def _val(_: Request, e: RequestValidationError):
        err = e.errors()[0]
        body = _body("VALIDATION", err["msg"], {"field": str(err["loc"][-1])})
        return JSONResponse(status_code=400, content=body)
