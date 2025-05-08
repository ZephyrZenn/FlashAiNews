from typing import Generic, TypeVar, Optional

from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """convert snake_case to camelCase"""
    first, *others = string.split('_')
    return first + ''.join(word.capitalize() for word in others)


class CamelModel(BaseModel):
    """Base model with camelCase field names."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        validate_by_name=True,
    )


T = TypeVar('T')


class CommonResult(CamelModel, Generic[T]):
    """Result Wrapper"""
    success: bool
    message: str = ''
    data: Optional[T] = None

    def to_dict(self) -> dict:
        """Convert the model to a dictionary."""
        return self.model_dump(by_alias=True)


def success_with_data(data=None):
    return CommonResult(success=True, data=data)


def success_with_message(message: str = ''):
    return CommonResult(success=True, message=message)


def failure_with_message(message: str = ''):
    return CommonResult(success=False, message=message)
