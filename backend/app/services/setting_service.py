from typing import Optional
from app.config import llm
from app.models.setting import ModelSetting, Setting


def get_setting():
    prompt = llm.get_prompt()
    if not llm.llm_config.has_inited():
        return Setting(
            model=None,
            prompt=prompt,
        )
    name, llm_config = llm.get_model()
    return Setting(
        model=ModelSetting(
            name=name,
            model=llm_config["model"],
            provider=llm_config["provider"],
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
        ),
        prompt=prompt,
    )


def update_setting(prompt: Optional[str] = None, model: Optional[ModelSetting] = None):
    llm.update_setting(prompt, model)
