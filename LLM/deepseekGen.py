from LLM import LLMGen
from openai import OpenAI


class DeepseekGen(LLMGen):
    """
    DeepSeek LLM generation class.
    Inherits from LLMGen and implements specific methods for DeepSeek.
    """

    def __init__(self, api_key: str, base_url: str):
        self.client = OpenAI(api_key=api_key,
                             base_url=base_url)

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the LLM based on the provided prompt.

        :param prompt: The input prompt to generate a response for.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated response as a string.
        """
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=prompt
        )

        return response.choices[0].message.content
