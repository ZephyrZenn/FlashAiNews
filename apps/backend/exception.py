import logging

from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from apps.backend.models.common import failure_with_message

logger = logging.getLogger(__name__)


# Validation error messages mapping (Chinese)
VALIDATION_MESSAGES = {
    "group_ids": "请至少选择一个分组",
    "time": "请输入有效的执行时间",
    "focus": "关注点格式不正确",
}


class BizException(Exception):
    """
    Custom exception class for business logic errors.
    """

    def __init__(self, message: str):
        """
        Initialize the BizException with a message and an optional error code.

        :param message: The error message.
        """
        super().__init__(message)
        self.message = message

async def handle_biz_exception(request, exc: BizException):
    """
    Exception handler for BizException.

    :param request: The request object.
    :param exc: The exception object.
    :return: JSON response with error message and status code 400.
    """
    logger.error("Business exception occurred: %s", exc.message)
    return JSONResponse(content=failure_with_message(exc.message).to_dict())

async def handle_exception(request, exc):
    """
    General exception handler for all other exceptions.

    :param request: The request object.
    :param exc: The exception object.
    :return: JSON response with error message and status code 500.
    """
    logger.error("An unexpected error occurred: %s", str(exc), exc_info=True)
    return failure_with_message(str(exc))


async def handle_validation_exception(request, exc: RequestValidationError):
    """
    Exception handler for Pydantic validation errors.
    Returns user-friendly error messages.
    """
    errors = exc.errors()
    messages = []

    for error in errors:
        # Get the field name from the location
        loc = error.get("loc", ())
        field = loc[-1] if loc else "unknown"

        # Try to get a friendly message, fallback to the original
        if field in VALIDATION_MESSAGES:
            messages.append(VALIDATION_MESSAGES[field])
        else:
            # Use original message but make it more readable
            msg = error.get("msg", "验证失败")
            messages.append(f"{field}: {msg}")

    # Combine all messages
    combined_message = "; ".join(messages) if messages else "请求参数验证失败"
    logger.warning("Validation error: %s", combined_message)

    return JSONResponse(
        status_code=422,
        content=failure_with_message(combined_message).to_dict()
    )