import asyncio
from typing import Optional, Union

from .config import LLMConfig
from .api_client import LLMAPIClient

class LLMInterface:
    def __init__(self, config: Union[str, LLMConfig, dict], api_client: Optional[LLMAPIClient] = None):
        if isinstance(config, str):
            # Treat config as a file path
            self.config = LLMConfig.from_file(config)
        elif isinstance(config, dict):
            # Treat config as a dictionary
            self.config = LLMConfig.from_dict(config)
        else:
            # Assume config is an LLMConfig object
            self.config = config

        if api_client is None:
            self.api_client = LLMAPIClient(self.config)
        else:
            self.api_client = api_client

    async def send_message(self, user_message: str) -> str:
        """
        Send a user message to the LLM API and return the response.

        Args:
            user_message (str): The user's message to send to the LLM API.

        Returns:
            str: The response from the LLM API.
        """
        # Prepare the conversation context
        context = self.config.system_message + self.config.example_messages

        # Add the user's message to the context
        context.append({"role": "user", "content": user_message})

        # Make the API call asynchronously
        response = await self.api_client.query(
            model=self.config.model,
            messages=context,
            **self.config.api_parameters
        )

        return response
