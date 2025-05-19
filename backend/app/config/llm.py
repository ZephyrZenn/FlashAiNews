import os
from typing import Optional
import toml

from app.constants import DEFAULT_PROMPT

import logging

from app.models.setting import ModelSetting

logger = logging.getLogger(__name__)


def _validate_llm_config(config: dict):
    if "api_key" not in config:
        raise ValueError("api_key is required")
    if "model" not in config:
        raise ValueError("model is required")
    if "provider" not in config:
        raise ValueError("provider is required")


class LLMConfig:
    def __init__(self, config_path):
        if not os.path.exists(config_path):
            raise ValueError(f"Config file {config_path} not found")
        self.config_path = config_path
        self.config = toml.load(config_path)
        if "models" not in self.config:
            self.config["models"] = {}
        if "global" not in self.config:
            self.config["global"] = {}
        self.save()

    def get_model(self, name: str) -> tuple[str, dict]:
        if name not in self.config["models"]:
            raise ValueError(f"Model {name} not found")
        cfg = self.config["models"][name]
        _validate_llm_config(cfg)
        return name, cfg

    def get_default_model(self) -> tuple[str, dict]:
        name = self.config["global"]["default_model"]
        if name not in self.config["models"]:
            raise ValueError(f"Default model {name} not found")
        return self.get_model(name)

    def get_prompt(self) -> str:
        return self.config["global"].get("prompt", DEFAULT_PROMPT)

    def has_inited(self) -> bool:
        try:
            self.get_default_model()
            return True
        except ValueError:
            return False

    def update_prompt(self, prompt: str):
        self.config["global"]["prompt"] = prompt

    def update_model(self, model: ModelSetting):
        self.config["models"][model.name] = {
            "model": model.model,
            "provider": model.provider.value,
            "api_key": model.api_key,
        }
        if model.base_url:
            self.config["models"][model.name]["base_url"] = model.base_url
        self.config["global"]["default_model"] = model.name

    def save(self):
        with open(self.config_path, "w") as f:
            toml.dump(self.config, f)


llm_config = None


def init_llm_config(config_path: str = "config.toml"):
    global llm_config
    llm_config = LLMConfig(config_path)
    if "models" in llm_config.config:
        logger.info(f"Loaded Models: {[name for name in llm_config.config['models']]}")


def get_model(name: str = None) -> tuple[str, dict]:
    global llm_config
    if not name:
        return llm_config.get_default_model()
    return llm_config.get_model(name)


def get_prompt() -> str:
    global llm_config
    return llm_config.get_prompt()


def update_setting(prompt: Optional[str] = None, model: Optional[ModelSetting] = None):
    global llm_config
    if prompt:
        llm_config.update_prompt(prompt)
    if model:
        llm_config.update_model(model)
    llm_config.save()