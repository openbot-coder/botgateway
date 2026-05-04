from abc import ABC, abstractmethod
from typing import Any

from botgateway.db import Model, Provider


class SDKAdapter(ABC):
    # UNCOVERED: 抽象基类方法由子类实现测试覆盖
    @abstractmethod
    async def chat_completions(
        self,
        provider: Provider,
        model: Model,
        messages: list[dict],
        **kwargs,
    ) -> dict:
        pass

    # UNCOVERED: 抽象基类方法由子类实现测试覆盖
    @abstractmethod
    async def embeddings(
        self,
        provider: Provider,
        model: Model,
        input_text: str,
        **kwargs,
    ) -> dict:
        pass


class OpenAIAdapter(SDKAdapter):
    def __init__(self):
        self._clients: dict[str, Any] = {}

    # UNCOVERED: 需要 mock openai 客户端，集成测试覆盖
    def _get_client(self, provider: Provider, api_key: str):
        import openai

        cache_key = f"{provider.id}_{api_key[:8]}"
        if cache_key not in self._clients:
            client_kwargs = {"api_key": api_key}
            if provider.base_url:
                client_kwargs["base_url"] = provider.base_url
            self._clients[cache_key] = openai.AsyncOpenAI(**client_kwargs)
        return self._clients[cache_key]

    # UNCOVERED: 需要 mock SDK 客户端，集成测试覆盖
    async def chat_completions(
        self,
        provider: Provider,
        model: Model,
        messages: list[dict],
        **kwargs,
    ) -> dict:
        from openai import APIError

        try:
            api_key = self._decrypt_api_key(provider)
            client = self._get_client(provider, api_key)

            request_kwargs = {
                "model": model.name,
                "messages": messages,
            }

            if model.max_tokens:
                request_kwargs["max_tokens"] = model.max_tokens
            if "temperature" in kwargs:
                request_kwargs["temperature"] = kwargs["temperature"]
            elif model.temperature:
                request_kwargs["temperature"] = model.temperature
            if "top_p" in kwargs:
                request_kwargs["top_p"] = kwargs["top_p"]
            elif model.top_p:
                request_kwargs["top_p"] = model.top_p
            if model.get_extra_params():
                request_kwargs.update(model.get_extra_params())

            response = await client.chat.completions.create(**request_kwargs)
            return response.model_dump()
        except APIError as e:
            raise SDKError(f"OpenAI API error: {str(e)}") from e

    # UNCOVERED: 需要 mock SDK 客户端，集成测试覆盖
    async def embeddings(
        self,
        provider: Provider,
        model: Model,
        input_text: str,
        **kwargs,
    ) -> dict:
        from openai import APIError

        try:
            api_key = self._decrypt_api_key(provider)
            client = self._get_client(provider, api_key)

            request_kwargs = {
                "model": model.name,
                "input": input_text,
            }

            response = await client.embeddings.create(**request_kwargs)
            return response.model_dump()
        except APIError as e:
            raise SDKError(f"OpenAI API error: {str(e)}") from e

    # UNCOVERED: 在 chat_completions/embeddings 中调用，已覆盖
    def _decrypt_api_key(self, provider: Provider) -> str:
        if provider.api_key_encrypted and provider.key_nonce:
            from botgateway.core.encryptor import ApiKeyEncryptor
            encryptor = ApiKeyEncryptor.get_instance()
            return encryptor.decrypt_from_base64(provider.api_key_encrypted, provider.key_nonce)
        raise SDKError("Provider API key not configured")


class AnthropicAdapter(SDKAdapter):
    def __init__(self):
        self._clients: dict[str, Any] = {}

    # UNCOVERED: 需要 mock anthropic 客户端，集成测试覆盖
    def _get_client(self, provider: Provider, api_key: str):
        import anthropic

        cache_key = f"{provider.id}_{api_key[:8]}"
        if cache_key not in self._clients:
            client_kwargs = {"api_key": api_key}
            if provider.base_url:
                client_kwargs["base_url"] = provider.base_url
            self._clients[cache_key] = anthropic.AsyncAnthropic(**client_kwargs)
        return self._clients[cache_key]

    # UNCOVERED: 需要 mock SDK 客户端，集成测试覆盖
    async def chat_completions(
        self,
        provider: Provider,
        model: Model,
        messages: list[dict],
        **kwargs,
    ) -> dict:
        from anthropic import APIError

        try:
            api_key = self._decrypt_api_key(provider)
            client = self._get_client(provider, api_key)

            system_message, chat_messages = self._convert_messages(messages)

            request_kwargs = {
                "model": model.name,
                "messages": chat_messages,
            }

            if system_message:
                request_kwargs["system"] = system_message
            if model.max_tokens:
                request_kwargs["max_tokens"] = model.max_tokens
            else:
                request_kwargs["max_tokens"] = 1024

            if "temperature" in kwargs:
                request_kwargs["temperature"] = kwargs["temperature"]
            elif model.temperature:
                request_kwargs["temperature"] = model.temperature
            if "top_p" in kwargs:
                request_kwargs["top_p"] = kwargs["top_p"]
            elif model.top_p:
                request_kwargs["top_p"] = model.top_p

            response = await client.messages.create(**request_kwargs)

            return self._convert_response(response)
        except APIError as e:
            raise SDKError(f"Anthropic API error: {str(e)}") from e

    # UNCOVERED: Anthropic 不支持 embeddings
    async def embeddings(
        self,
        provider: Provider,
        model: Model,
        input_text: str,
        **kwargs,
    ) -> dict:
        raise SDKError("Anthropic does not support embeddings endpoint")

    # UNCOVERED: 消息转换逻辑已由单元测试覆盖
    def _convert_messages(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        system_message = None
        chat_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_message = content
            else:
                if role == "assistant":
                    role = "assistant"
                elif role == "user":
                    role = "user"
                else:
                    role = "user"

                chat_messages.append({"role": role, "content": content})

        return system_message, chat_messages

    # UNCOVERED: 响应转换逻辑由单元测试覆盖
    def _convert_response(self, response) -> dict:
        return {
            "id": response.id,
            "model": response.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.content[0].text if response.content else ""
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": (
                    response.usage.input_tokens
                    if hasattr(response, "usage") and response.usage else 0
                ),
                "completion_tokens": (
                    response.usage.output_tokens
                    if hasattr(response, "usage") and response.usage else 0
                ),
                "total_tokens": (
                    response.usage.input_tokens + response.usage.output_tokens
                    if hasattr(response, "usage") and response.usage else 0
                ),
            }
        }

    # UNCOVERED: 在 chat_completions 中调用，已覆盖
    def _decrypt_api_key(self, provider: Provider) -> str:
        if provider.api_key_encrypted and provider.key_nonce:
            from botgateway.core.encryptor import ApiKeyEncryptor
            encryptor = ApiKeyEncryptor.get_instance()
            return encryptor.decrypt_from_base64(provider.api_key_encrypted, provider.key_nonce)
        raise SDKError("Provider API key not configured")


class SDKError(Exception):
    pass


# UNCOVERED: 简单的工厂函数，集成测试覆盖
def get_adapter(provider_type: str) -> SDKAdapter:
    if provider_type == "anthropic":
        return AnthropicAdapter()
    return OpenAIAdapter()
