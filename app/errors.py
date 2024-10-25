import traceback
from http import HTTPStatus
from typing import Optional, Any
from urllib.request import Request

import exceptiongroup
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from app.logging_ import logger


class ErrorBody(BaseModel):
    code: str = Field(alias="code")
    message: str = Field(alias="message")
    details: Optional[dict[str, Any]] = Field(alias="details", default=None)


class Error(BaseModel):
    error: ErrorBody = Field(alias="error")


class Fault(BaseModel):
    fault: Optional[ErrorBody] = Field(alias="fault", default=None)


class ErrorCodeException(Exception):
    """内部异常类"""

    def __init__(self, error: Error, code: int = 400, details: Any = None):
        self.error = error
        self.code = code
        self.details = details


class UnauthorizedException(ErrorCodeException):
    """未授权异常类"""

    def __init__(self, error: Error):
        self.error = error
        self.code = HTTPStatus.UNAUTHORIZED


class ForbiddenException(ErrorCodeException):
    """禁止访问异常类"""

    def __init__(self, error: Error):
        self.error = error
        self.code = HTTPStatus.FORBIDDEN


class NotFoundException(ErrorCodeException):
    """资源不存在异常类"""

    def __init__(self, error: Error):
        self.error = error
        self.code = HTTPStatus.NOT_FOUND


class BadRequestException(ErrorCodeException):
    """非法请求异常类"""

    def __init__(self, error: Error, details: Any = None):
        self.error = error
        self.code = HTTPStatus.BAD_REQUEST
        if details is not None:
            self.error.error.details = details


class RateLimitException(ErrorCodeException):
    """Open AI服务繁忙"""

    def __init__(self, error: Error, details: Any = None):
        self.error = error
        self.code = HTTPStatus.TOO_MANY_REQUESTS
        self.details = details


class ConflictException(ErrorCodeException):
    """冲突异常类"""

    def __init__(self, error: Error):
        self.error = error
        self.code = HTTPStatus.CONFLICT


class InternalServerErrorException(ErrorCodeException):
    """内部错误异常类"""

    def __init__(self, error: Error, details: Any = None):
        self.error = error
        self.code = HTTPStatus.INTERNAL_SERVER_ERROR
        if details is not None:
            self.details = details


def err_code_exception_handler(request: Request, exp: ErrorCodeException):
    """BizException异常处理器"""
    return JSONResponse(
        status_code=exp.code,
        content=exp.error.model_dump(by_alias=True),
        media_type=JSONResponse.media_type,
    )


def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


def log_exception(exc: Exception):
    """如果是异常组则递归打印每个异常，否则无法正常地获取实际的异常"""
    if isinstance(exc, exceptiongroup.ExceptionGroup):
        for e in exc.exceptions:
            log_exception(e)
    else:
        # 试用 join，因为返回的是列表
        logger.error(
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        )


def convert_global_exception_to_code_exception(exp: Exception):
    log_exception(exp)

    return ErrorCodeException(code=500, error=INTERNAL_ERROR)


def global_exception_handler(request: Request, exp: Exception):
    return to_json_response(convert_global_exception_to_code_exception(exp))


def to_json_response(exp: ErrorCodeException):
    return JSONResponse(
        status_code=exp.code,
        content=exp.error.model_dump(by_alias=True),
        media_type=JSONResponse.media_type,
    )


# 具体的异常
UNAUTHORIZED = Error(error=ErrorBody(code="Unauthorized", message="请求未授权/登录"))
INTERNAL_ERROR = Error(
    error=ErrorBody(code="InternalError", message="内部错误，请联系管理员")
)
FORBIDDEN_ERROR = Error(error=ErrorBody(code="Forbidden", message="无权限访问/操作"))
BAD_REQUEST_ERROR = Error(
    error=ErrorBody(code="BadRequestError", message="请求参数异常")
)
EXPIRED_ERROR = Error(error=ErrorBody(code="ExpiredError", message="已过期"))

FILE_NOT_SUPPORT = Error(
    error=ErrorBody(
        code="FileNotSupport", message="当前文档类型不支持，目前暂时支持{extensions}"
    )
)
FILE_RECORD_CNT_LIMIT = Error(
    error=ErrorBody(code="DocRecordCntLimit", message="上传文件限制最大{max}条记录")
)
FILE_NOT_FOUND = Error(error=ErrorBody(code="FileNotFound", message="文件不存在"))
FILE_IS_EMBEDDING = Error(
    error=ErrorBody(code="FileIsEmbedding", message="文件正在生成向量")
)
EMBEDDING_CONTENT_TOO_LONG = Error(
    error=ErrorBody(code="EmbeddingContentTooLong", message="文件的向量文本过长")
)
EXPLORATION_TASK_NOT_FOUND = Error(
    error=ErrorBody(code="ExplorationTaskNotFound", message="数据探索任务不存在")
)

DIM_REDUCTION_NOT_FOUND = Error(
    error=ErrorBody(code="DimReductionNotFound", message="散点图不存在")
)
DIMENSIONS_IS_REDUCING = Error(
    error=ErrorBody(code="DimensionsIsReducing", message="正在进行降维")
)
EXPLORATION_TASK_IS_RUNNING = Error(
    error=ErrorBody(code="ExplorationTaskIsRunning", message="探索任务进行中")
)

LABEL_TASK_EXIST = Error(
    error=ErrorBody(code="LabelTaskExist", message="该数据集已存在标签任务")
)
LABEL_TASK_CNT_LIMIT = Error(
    error=ErrorBody(code="LabelTaskCntLimit", message="标签任务限制最大{max}条记录")
)
LABEL_TASK_COLUMN_LIMIT = Error(
    error=ErrorBody(code="LabelTaskColumnLimit", message="列数量不能超过5列")
)
LABEL_TASK_OUTPUT_LABEL_LIMIT = Error(
    error=ErrorBody(code="LabelTaskOutputLabelLimit", message="输出标签不能超过4列")
)
LABEL_TASK_RERUN_FORBIDDEN = Error(
    error=ErrorBody(code="LabelTaskRerunForbidden", message="终止的任务不能重跑")
)

IP_NOT_ALLOWED = Error(error=ErrorBody(code="IpNotAllowed", message="IP not allowed"))
LLM_QUOTA_EXCEED_LIMIT = Error(
    error=ErrorBody(code="LlmQuotaExceedLimit", message="用量已超过限制额度")
)

DATASET_NOT_FOUND = Error(
    error=ErrorBody(code="DatasetNotFound", message="数据集不存在")
)
DATASET_ACTION_NOT_SUPPORT = Error(
    error=ErrorBody(
        code="DatasetActionNotSupport", message="数据集更新只支持更新或删除操作"
    )
)
DATASET_MODIFY_ERROR = Error(
    error=ErrorBody(code="DatasetModifyError", message="数据集更新失败")
)
