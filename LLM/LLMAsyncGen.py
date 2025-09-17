from abc import ABC, abstractmethod

from .prompts import CLASS_EXAMPLES_PROMPT, CLASS_SYSTEM_PROMPT, DIAGNOSTIC_SYSTEM_PROMPT, FIELD_EXAMPLES_PROMPT, FIELD_SYSTEM_PROMPT, METHOD_EXAMPLES_PROMPT, METHOD_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT


class LLMAsyncGen(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Asynchronous method to generate a response from the LLM based on the given prompt.

        :param prompt: The input prompt to generate a response for.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated response as a string.
        """
        pass

    async def generate_field_description(self, feature_type: str, feature: str, **kwargs) -> str:
        """
        Asynchronously generate a field description for a specified feature type and feature.

        :param feature_type: The type of the feature (e.g., 'permission', 'API').
        :param feature: The specific feature to describe.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated field description as a string.
        """
        inputs = {
            "role": "user",
            "content": f"{feature_type}: {feature}"
        }
        return await self.generate([FIELD_SYSTEM_PROMPT] + FIELD_EXAMPLES_PROMPT + [inputs], **kwargs)

    async def generate_class_description(self, class_content: str, **kwargs) -> str:
        """
        Generate a class description for a specific class content.

        :param class_content: The content of the class to describe.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated class description as a string.
        """
        inputs = {
            "role": "user",
            "content": f"Class: {class_content}"
        }
        return await self.generate([CLASS_SYSTEM_PROMPT] + CLASS_EXAMPLES_PROMPT + [inputs], **kwargs)

    async def generate_method_description(self, feature: str, **kwargs) -> str:
        """
        Asynchronously generate a method description for a specific feature.

        :param feature: The specific feature to describe.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated method description as a string.
        """
        inputs = {
            "role": "user",
            "content": f"Method: {feature}"
        }
        return await self.generate([METHOD_SYSTEM_PROMPT] + METHOD_EXAMPLES_PROMPT + [inputs], **kwargs)

    async def generate_summary(self, feature: str, package: str, **kwargs) -> str:
        """
        Asynchronously generate a summary for a specific feature and package.

        :param feature: The specific feature to summarize.
        :param package: The application package name, used to format the system prompt.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated summary as a string.
        """
        inputs = {
            "role": "user",
            "content": feature
        }
        system_prompt = {
            "role": SUMMARY_SYSTEM_PROMPT["role"],
            "content": SUMMARY_SYSTEM_PROMPT["content"].format(Package=package)
        }
        return await self.generate([system_prompt] + [inputs], **kwargs)

    async def generate_diagnostic(self, view_content: str, package: str, family: str, **kwargs) -> str:
        """
        Asynchronously generate a diagnostic report based on view content and family classification.

        :param view_content: The content of the view to analyze.
        :param package: The application package name, used to format the system prompt.
        :param family: The family classification of the application, used to format the system prompt.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated diagnostic report as a string.
        """
        inputs = {
            "role": "user",
            "content": view_content
        }
        system_prompt = {
            "role": DIAGNOSTIC_SYSTEM_PROMPT["role"],
            "content": DIAGNOSTIC_SYSTEM_PROMPT["content"].format(Package=package, family=family)
        }
        return await self.generate([system_prompt] + [inputs], **kwargs)
