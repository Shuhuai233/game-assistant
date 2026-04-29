"""
LLM Provider abstraction.
All providers use OpenAI-compatible API format, so we just swap base_url and api_key.
"""

import base64
from openai import OpenAI
from config_loader import Config, LLMProviderConfig
from logger import logger


class LLMClient:
    """Unified LLM client that works with any OpenAI-compatible API."""

    def __init__(self, config: Config):
        self.config = config
        self.provider_name = config.llm_provider
        self.provider_config: LLMProviderConfig = config.llm_configs.get(
            self.provider_name,
            config.llm_configs.get("deepseek")
        )
        self.system_prompt = config.game_system_prompt
        self.conversation_history = []

        api_key = self.provider_config.api_key or "no-key"
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.provider_config.base_url or None,
        )
        self.model = self.provider_config.model

        logger.info(f"LLM init: provider={self.provider_name}, model={self.model}")

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []

    def ask(self, question: str, screenshot_base64: str = None) -> str:
        """
        Send a question to the LLM and return the response.
        Optionally include a screenshot for vision models.
        """
        if screenshot_base64:
            content = [
                {"type": "text", "text": question},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_base64}"
                    }
                }
            ]
        else:
            content = question

        self.conversation_history.append({
            "role": "user",
            "content": content
        })

        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            answer = response.choices[0].message.content

            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return answer

        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return f"AI request failed: {e}"
