from __future__ import annotations

import logging

import httpx

from .config import SummarizationConfig, YandexGPTConfig

logger = logging.getLogger(__name__)

_YANDEX_GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
_PROMPT = "Summarize the following update in 2–3 sentences:\n\n{text}"


class TruncatingSummarizer:
    def __init__(
        self,
        config: SummarizationConfig,
        yandex_gpt: YandexGPTConfig | None = None,
    ) -> None:
        self._threshold = config.threshold
        self._yandex_gpt = yandex_gpt

    async def summarize(self, text: str) -> str:
        if self._yandex_gpt and self._yandex_gpt.api_key:
            try:
                return await self._summarize_with_yandex(text)
            except Exception as exc:
                logger.warning("yandex_gpt_failed_fallback_to_truncation", extra={"error": str(exc)})
        if len(text) <= self._threshold:
            return text
        return text[: self._threshold] + "..."

    async def _summarize_with_yandex(self, text: str) -> str:
        cfg = self._yandex_gpt
        assert cfg is not None
        model_uri = f"gpt://{cfg.folder_id}/{cfg.model}"
        payload = {
            "modelUri": model_uri,
            "completionOptions": {"stream": False, "temperature": 0.3, "maxTokens": 200},
            "messages": [{"role": "user", "text": _PROMPT.format(text=text)}],
        }
        headers = {
            "Authorization": f"Api-Key {cfg.api_key}",
            "x-folder-id": cfg.folder_id,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(_YANDEX_GPT_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["result"]["alternatives"][0]["message"]["text"]
