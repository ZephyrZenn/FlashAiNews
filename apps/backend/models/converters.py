"""Converters between core dataclasses and API Pydantic models."""

from core.models.config import ModelConfig
from core.models.generator import ModelProvider

from .request import ModelConfigRequest
from .view_model import ModelSettingVO


def model_config_to_vo(config: ModelConfig, mask_api_key: bool = True) -> ModelSettingVO:
    """Convert core ModelConfig dataclass to API response VO.
    
    Args:
        config: The core ModelConfig dataclass
        mask_api_key: If True, mask the API key in the response
    
    Returns:
        ModelSettingVO for API response
    """
    return ModelSettingVO(
        model=config.model,
        provider=config.provider.value,
        api_key="********" if mask_api_key else config.api_key,
        base_url=config.base_url or "",
    )


def request_to_model_config(request: ModelConfigRequest) -> ModelConfig:
    """Convert API request to core ModelConfig dataclass.
    
    Args:
        request: The ModelConfigRequest from API
    
    Returns:
        ModelConfig dataclass for business logic
    """
    return ModelConfig(
        model=request.model,
        provider=ModelProvider(request.provider),
        api_key=request.api_key,
        base_url=request.base_url,
    )
