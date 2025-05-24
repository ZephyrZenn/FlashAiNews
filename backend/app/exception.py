import logging

from starlette.responses import JSONResponse

from app.models.common import failure_with_message

logger = logging.getLogger(__name__)

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