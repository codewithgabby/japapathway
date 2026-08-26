# app/core/exceptions.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from typing import Optional

class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        detail: Optional[str] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.detail = detail

class NotFoundException(AppException):
    def __init__(self, entity: str = "Resource"):
        super().__init__(status_code=404, message=f"{entity} not found")

class UnauthorizedException(AppException):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(status_code=401, message=message)

class ForbiddenException(AppException):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(status_code=403, message=message)

class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request"):
        super().__init__(status_code=400, message=message)

def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "detail": exc.detail,
                "error_code": exc.status_code,
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "error_code": exc.status_code,
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation error",
                "detail": exc.errors(),
                "error_code": 422,
            }
        )