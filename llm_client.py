"""
LLM Provider abstraction.
All providers use OpenAI-compatible API format, so we just swap base_url and api_key.
"""

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
        # Build user message — always use string content for text-only
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
            content = str(question)

        self.conversation_history.append({
            "role": "user",
            "content": content
        })

        # Build messages — ensure all content fields are proper strings
        messages = [
            {"role": "system", "content": str(self.system_prompt)}
        ]
        for msg in self.conversation_history:
            messages.append({
                "role": str(msg["role"]),
                "content": msg["content"]
            })

        # Log the request for debugging
        logger.info(f"LLM request: model={self.model}, messages={len(messages)}, last_q='{question[:80]}'")

        try:
            # Build kwargs — only include parameters the provider supports
            kwargs = {
                "model": self.model,
                "messages": messages,
            }

            # DeepSeek uses max_tokens, some providers use max_completion_tokens
            # Try without max_tokens first for maximum compatibility
            if self.provider_name in ("openai",):
                kwargs["max_completion_tokens"] = 500
            else:
                kwargs["max_tokens"] = 500

            response = self.client.chat.completions.create(**kwargs)
            answer = response.choices[0].message.content or ""

            logger.info(f"LLM response: '{answer[:100]}...'")

            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return answer

        except Exception as e:
            error_str = str(e)
            logger.error(f"LLM request failed: {error_str}")

            # If max_tokens caused the error, retry without it
            if "max_tokens" in error_str.lower() or "deserialize" in error_str.lower():
                logger.info("Retrying without max_tokens...")
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                    )
                    answer = response.choices[0].message.content or ""
                    logger.info(f"LLM retry response: '{answer[:100]}...'")

                    self.conversation_history.append({
                        "role": "assistant",
                        "content": answer
                    })
                    return answer
                except Exception as e2:
                    logger.error(f"LLM retry also failed: {e2}")
                    # Remove the failed user message from history
                    if self.conversation_history:
                        self.conversation_history.pop()
                    return f"AI request failed: {e2}"

            # Remove the failed user message from history
            if self.conversation_history:
                self.conversation_history.pop()
            return f"AI request failed: {e}"
