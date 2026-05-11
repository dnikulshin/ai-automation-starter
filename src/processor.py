import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import requests
import yaml

from src.config import AppConfig

logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self, config: AppConfig, prompt_path: Path | None = None):
        self.config = config
        self.prompt = self._load_prompt(prompt_path or Path("prompts/default.yaml"))

    def _load_prompt(self, path: Path) -> Dict[str, str]:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _call_llm(self, text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/DNikulshin",
        }
        payload = {
            "model": self.config.llm_model,
            "messages": [
                {"role": "system", "content": self.prompt["system"]},
                {"role": "user", "content": self.prompt["template"].format(text=text)},
            ],
        }

        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.config.request_timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def process(self, raw_text: str) -> Dict[str, Any]:
        last_error = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                raw_response = self._call_llm(raw_text)
                # Очистка от markdown-блоков, если модель их добавляет
                clean_json = raw_response.strip().removeprefix("```json").removesuffix("```").strip()
                return json.loads(clean_json)
            except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt}/{self.config.max_retries} failed: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(2**attempt)
        
        raise RuntimeError(f"LLM processing failed after {self.config.max_retries} attempts: {last_error}")