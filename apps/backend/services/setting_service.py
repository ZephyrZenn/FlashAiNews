from typing import Optional

from core.config.loader import get_config
from core.config.utils import write_config
from apps.backend.models.setting import ModelConfig, Setting


def get_setting():
    config = get_config()
    model_cfg = config.model
    return Setting(
        model=ModelConfig(
            model=model_cfg.model,
            provider=model_cfg.provider,
            api_key=model_cfg.api_key,
            base_url=model_cfg.base_url or "",
        ),
    )


def update_setting(model: Optional[ModelConfig]):
    cfg = get_config()
    if model:
        cfg.model = model
    write_config(cfg)
