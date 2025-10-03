from typing import Optional
from app.config.loader import get_config
from app.models.setting import ModelConfig, Setting
from app.config.utils import write_config


def get_setting():
    config = get_config()
    prompt = config.prompt
    model_cfg = config.model
    return Setting(
        model=ModelConfig(
            name=model_cfg.model,
            model=model_cfg.model,
            provider=model_cfg.provider,
            api_key=model_cfg.api_key,
            base_url=model_cfg.base_url or "",
        ),
        prompt=prompt,
    )


def update_setting(prompt: Optional[str], model: Optional[ModelConfig]):
    cfg = get_config()
    if prompt:
        cfg.prompt = prompt
    if model:
        cfg.model = model
    
    write_config(cfg)
