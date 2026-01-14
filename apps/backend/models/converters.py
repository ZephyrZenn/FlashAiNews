"""Converters between core dataclasses and API Pydantic models."""

from core.config.loader import get_base_url_for_provider
from core.models.config import ModelConfig
from core.models.generator import ModelProvider

from .request import ModelConfigRequest
from .view_model import ModelSettingVO


def model_config_to_vo(config: ModelConfig) -> ModelSettingVO:
    """Convert core ModelConfig dataclass to API response VO.
    
    Args:
        config: The core ModelConfig dataclass
    
    Returns:
        ModelSettingVO for API response
    
    Note: API keys are managed via environment variables, not exposed in API.
    """
    return ModelSettingVO(
        model=config.model,
        provider=config.provider.value,
        base_url=config.base_url if config.provider == ModelProvider.OTHER else None,
    )


def request_to_model_config(request: ModelConfigRequest) -> ModelConfig:
    """Convert API request to core ModelConfig dataclass.
    
    Args:
        request: The ModelConfigRequest from API
    
    Returns:
        ModelConfig dataclass for business logic
    
    Note: Base URL is auto-determined except for 'other' provider.
    """
    provider = ModelProvider(request.provider)
    base_url = get_base_url_for_provider(provider, request.base_url)
    
    return ModelConfig(
        model=request.model,
        provider=provider,
        base_url=base_url,
    )
