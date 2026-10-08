import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ApiError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ApiError):
    status_code = 404
    code = "not_found"


class InvalidInputError(ApiError):
    status_code = 422
    code = "invalid_input"


class ModelUnavailableError(ApiError):
    status_code = 503
    code = "model_unavailable"


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"error": {"code": code, "message": message}}
    )


FIELD_LABELS = {
    "hour": "la hora",
    "weekday": "el día de la semana",
    "month": "el mes",
    "store_id": "la sede",
    "units": "las unidades",
    "revenue": "los ingresos",
    "avg_price": "el precio promedio",
    "quarter": "el trimestre",
    "limit": "el límite",
    "product_type": "el tipo de producto",
}


def describe_validation_error(error: RequestValidationError) -> str:
    problems = []
    for item in error.errors():
        field_name = str(item["loc"][-1]) if item["loc"] else "datos"
        label = FIELD_LABELS.get(field_name, field_name)
        problems.append(f"Revisa {label}: el valor ingresado no es válido.")
    return " ".join(dict.fromkeys(problems)) or "Los datos enviados no son válidos."


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_request: Request, error: ApiError) -> JSONResponse:
        return error_response(error.status_code, error.code, error.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return error_response(422, "invalid_input", describe_validation_error(error))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_request: Request, error: StarletteHTTPException) -> JSONResponse:
        message = (
            "No encontramos lo que buscabas."
            if error.status_code == 404
            else "No pudimos procesar la solicitud."
        )
        return error_response(error.status_code, "http_error", message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, error: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=error)
        return error_response(
            500,
            "internal_error",
            "Ocurrió un error inesperado. Inténtalo de nuevo en unos minutos.",
        )
