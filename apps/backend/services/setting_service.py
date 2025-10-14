from datetime import time
from typing import Optional

from core.config.loader import get_config
from core.config.utils import write_config
from apps.backend.models.setting import ModelConfig, Setting
from apps.backend.services.scheduler_service import update_brief_schedule


def get_setting():
    config = get_config()
    prompt = config.prompt
    model_cfg = config.model
    return Setting(
        model=ModelConfig(
            model=model_cfg.model,
            provider=model_cfg.provider,
            api_key=model_cfg.api_key,
            base_url=model_cfg.base_url or "",
        ),
        prompt=prompt,
        brief_time=config.brief_time,
    )


def update_setting(
    prompt: Optional[str], model: Optional[ModelConfig], brief_time: Optional[time]
):
    cfg = get_config()
    new_schedule = None
    if prompt:
        cfg.prompt = prompt
    if model:
        cfg.model = model
    if brief_time is not None:
        normalized_time = brief_time.replace(second=0, microsecond=0)
        if normalized_time != cfg.brief_time:
            new_schedule = normalized_time
        cfg.brief_time = normalized_time

    write_config(cfg)
    if new_schedule:
        update_brief_schedule(new_schedule)
