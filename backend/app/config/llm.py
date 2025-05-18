import toml

from app.constants import DEFAULT_PROMPT

import logging

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
        self.config = toml.load(config_path)

    def get_model(self, name: str):
        if name not in self.config["models"]:
            raise ValueError(f"Model {name} not found")
        cfg = self.config["models"][name]
        _validate_llm_config(cfg)
        return cfg

    def get_default_model(self):
        name = self.config["global"]["default_model"]
        if name not in self.config["models"]:
            raise ValueError(f"Default model {name} not found")
        return self.get_model(name)

    def get_prompt(self):
        return self.config["global"].get("prompt", DEFAULT_PROMPT)


llm_config = None


def init_llm_config(config_path: str = "config.toml"):
    global llm_config
    llm_config = LLMConfig(config_path)
    logger.info(f"Loaded Models: {[name for name in llm_config.config['models']]}")


def get_model(name: str = None) -> dict:
    global llm_config
    if not name:
        return llm_config.get_default_model()
    return llm_config.get_model(name)


def get_prompt() -> str:
    global llm_config
    return llm_config.get_prompt()
