import time
import shortuuid
import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app import REQUEST_ID_CONTEXT, APP_NAME
from app.logging_ import logger, file_handler
from app.errors import (
    ErrorCodeException,
    err_code_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.api import message_api


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title=APP_NAME,
    openapi_url=f"/api/v1/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)


@app.middleware("http")
async def http_access(request: Request, call_next):
    """
    在最外层记录 access log，添加 trace id 等工作
    """

    def _get_path_with_query_string(request: Request) -> str:
        if request.url.query:
            return f"{request.url.path}?{request.url.query}"
        return request.url.path

    trace_id = shortuuid.uuid()
    REQUEST_ID_CONTEXT.set(trace_id)

    start_time = time.time()

    response = await call_next(request)

    response_time = time.time() - start_time
    remote_ip = request.headers.get("X-Real-IP") or "N/A"

    logger.info(
        f"{remote_ip} - "
        f"{request.client.host}:{request.client.port} - "
        f'"{request.method} {_get_path_with_query_string(request)}" '
        f"{response.status_code} {response_time * 1000:.2f}ms"
    )

    response.headers["x-tr"] = trace_id

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 请求头
)
app.include_router(message_api.router)

app.add_exception_handler(ErrorCodeException, err_code_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


@app.on_event("startup")
async def startup_event():
    """
    将所有非必要的初始化代码放在fastapi的startup event中进行初始化，避免因为reload进程的存在而导致初始化两次所有模块

    :return:
    """
    import logging

    from app.database import Base, engine
    from app.model.user import User
    from app.model.message import Message, MessageExtra
    from app.model.completion import Completion

    logging.getLogger("uvicorn").addHandler(file_handler)
    Base.metadata.create_all(bind=engine, checkfirst=True)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
    )
