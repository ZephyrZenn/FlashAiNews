import logging
from pathlib import Path
from typing import Optional

import toml
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from app.constants import DEFAULT_INSTRUCTION_PROMPT, PROMPT_TEMPLATE
from app.models.setting import ModelSetting

logger = logging.getLogger(__name__)


def _validate_llm_config(config: dict):
    if "api_key" not in config:
        raise ValueError("api_key is required")
    if "model" not in config:
        raise ValueError("model is required")
    if "provider" not in config:
        raise ValueError("provider is required")

# TODO: The watcher doesn't work in the container, need to fix it

class ConfigManager(FileSystemEventHandler):
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = None
        self.load()

    def load(self):
        self.config = toml.load(self.config_path)
        if "models" not in self.config:
            self.config["models"] = {}
        if "global" not in self.config:
            self.config["global"] = {}

    def on_modified(self, event):
        logger.info(f"Config file modified: {event.src_path}")
        # Convert both paths to absolute paths for consistent comparison
        event_path = Path(event.src_path).resolve()
        config_path = Path(self.config_path).resolve()
        if event_path == config_path:
            self.load()

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
        if "prompt" not in self.config["global"] or not self.config["global"]["prompt"]:
            return DEFAULT_INSTRUCTION_PROMPT
        return self.config["global"]["prompt"]

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


llm_config = None
_observer = None


def init_llm_config(config_path: str = "config.toml"):
    global llm_config, _observer
    path = Path(config_path).resolve()
    llm_config = ConfigManager(path)
    if "models" in llm_config.config:
        logger.info(f"Loaded Models: {[name for name in llm_config.config['models']]}")

    if _observer is not None:
        logger.info("LLM config watcher already initialized")
        return

    logger.info(f"Initializing LLM config watcher for file: {path}")
    _observer = Observer()
    _observer.schedule(llm_config, path, recursive=True)
    _observer.start()
    logger.info(f"LLM config initialized. Watching config file: {path}")


def close_config_watcher():
    global _observer
    if _observer:
        _observer.stop()
        _observer.join()
        _observer = None
        logger.info("LLM config watcher closed")


def get_model(name: str = None) -> tuple[str, dict]:
    global llm_config
    if not name:
        return llm_config.get_default_model()
    return llm_config.get_model(name)


def get_prompt() -> str:
    global llm_config
    return llm_config.get_prompt()


def get_full_prompt() -> str:
    global llm_config
    prompt = llm_config.get_prompt()
    return PROMPT_TEMPLATE.format(instruction=prompt)


def update_setting(prompt: Optional[str] = None, model: Optional[ModelSetting] = None):
    global llm_config
    if prompt:
        llm_config.update_prompt(prompt)
    if model:
        llm_config.update_model(model)
    llm_config.save()
