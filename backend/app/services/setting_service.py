from app.config.loader import get_config
from app.models.setting import ModelConfig, Setting


def get_setting():
    config = get_config()
    prompt = config.global_.prompt
    model_cfg = config.models[config.global_.default_model]
    return Setting(
        model=ModelConfig(
            name=config.global_.default_model,
            model=model_cfg.model,
            provider=model_cfg.provider,
            api_key=model_cfg.api_key,
            base_url=model_cfg.base_url,
        ),
        prompt=prompt,
    )
