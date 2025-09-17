from LLM import LLMAsyncGen
from ollama import AsyncClient


class OllamaGen(LLMAsyncGen):
    """
    Ollama LLM generation class.
    Inherits from LLMGen and implements specific methods for Ollama.
    """

    def __init__(self, model_name: str, base_url: str):
        """
        Initialize the Ollama client and specify the model name.
        """
        self.client = AsyncClient(
            host=base_url,
        )  # Connect to local Ollama service by default
        self.model_name = model_name

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using Ollama.

        :param prompt: The input prompt string
        :param kwargs: Additional parameters (currently unused)
        :return: The generated response text
        """
        response = await self.client.chat(self.model_name, prompt)
        return response['message']['content']
