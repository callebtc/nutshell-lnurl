import sys

from fastapi import FastAPI, status
from fastapi.exception_handlers import (
    request_validation_exception_handler as _request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from main import router, startup_server

logger.remove()  # remove the old handler. Else, the old one will work along with the new one you've added below'
logger.add(sys.stdout, level="DEBUG")


def create_app(config_object="core.settings") -> FastAPI:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
    ]

    app = FastAPI(
        title="Cashu LNURL middleware",
        description="A LNURL middleware for Cashu",
        license_info={
            "name": "MIT License",
            "url": "https://raw.githubusercontent.com/cashubtc/cashu/main/LICENSE",
        },
        middleware=middleware,
    )

    return app


app = create_app()


@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    CORS_HEADERS = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true",
    }
    try:
        return await call_next(request)
    except Exception as e:
        try:
            err_message = str(e)
        except Exception:
            err_message = e.args[0] if e.args else "Unknown error"
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "ERROR", "detail": err_message},
            headers=CORS_HEADERS,
        )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    This is a wrapper to the default RequestValidationException handler of FastAPI.
    This function will be called when client input is not valid.
    """
    query_params = request.query_params._dict
    detail = {
        "errors": exc.errors(),
        "query_params": query_params,
    }
    # log the error
    logger.error(detail)
    # pass on
    return await _request_validation_exception_handler(request, exc)


@app.on_event("startup")
async def startup():
    await startup_server()


app.include_router(router=router, tags=["LNURL server"])
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
