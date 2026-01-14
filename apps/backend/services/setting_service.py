from typing import Optional

from core.config.loader import get_config, reload_config
from core.config.utils import write_config
from core.models.config import ModelConfig

from apps.backend.models.converters import model_config_to_vo
from apps.backend.models.view_model import SettingVO


def get_setting() -> SettingVO:
    """Get current settings as a VO for API response."""
    config = get_config()
    return SettingVO(model=model_config_to_vo(config.model))


def update_setting(model: Optional[ModelConfig]) -> None:
    """Update settings with a new model configuration.
    
    Note: Only model name, provider, and base_url (for 'other' provider) are saved.
    API keys are managed via environment variables.
    """
    cfg = get_config()
    if model:
        cfg.model = model
    write_config(cfg)
    # Reload config to pick up changes
    reload_config()