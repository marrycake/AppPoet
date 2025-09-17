from abc import ABC, abstractmethod

from .prompts import CLASS_EXAMPLES_PROMPT, CLASS_SYSTEM_PROMPT, DIAGNOSTIC_SYSTEM_PROMPT, FIELD_EXAMPLES_PROMPT, FIELD_SYSTEM_PROMPT, METHOD_EXAMPLES_PROMPT, METHOD_SYSTEM_PROMPT, SUMMARY_SYSTEM_PROMPT


class LLMGen(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the LLM based on the provided prompt.

        :param prompt: The input prompt to generate a response for.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated response as a string.
        """
        pass

    def generate_field_description(self, feature_type: str, feature: str, **kwargs) -> str:
        """
        Generate a field description for a specific feature type and feature.

        :param feature_type: The type of the feature (e.g., 'permission', 'API').
        :param feature: The specific feature to describe.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated field description as a string.
        """
        inputs = {
            "role": "user",
            "content": f"{feature_type}: {feature}"
        }
        return self.generate([FIELD_SYSTEM_PROMPT] + FIELD_EXAMPLES_PROMPT + [inputs], **kwargs)

    def generate_method_description(self, feature: str, **kwargs) -> str:
        """
        Generate a method description for a specific feature.

        :param feature: The specific feature to describe.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated method description as a string.
        """
        inputs = {
            "role": "user",
            "content": f"Method: {feature}"
        }
        return self.generate([METHOD_SYSTEM_PROMPT] + METHOD_EXAMPLES_PROMPT + [inputs], **kwargs)

    def generate_class_description(self, class_content: str, **kwargs) -> str:
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
        return self.generate([CLASS_SYSTEM_PROMPT] + CLASS_EXAMPLES_PROMPT + [inputs], **kwargs)

    def generate_summary(self, feature: str, package: str, **kwargs) -> str:
        """
        Generate a summary for a specific feature.

        :param feature: The specific feature to summarize.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated summary as a string.
        """
        inputs = {
            "role": "user",
            "content": feature
        }

        system_prompt = {
            "role": SUMMARY_SYSTEM_PROMPT["role"],   # 保持role不变
            # 替换内容
            "content": SUMMARY_SYSTEM_PROMPT["content"].format(Package=package)
        }

        return self.generate([system_prompt] + [inputs], **kwargs)

    def generate_diagnostic(self, view_content: str, package: str,  family: str,  **kwargs) -> str:
        """
        Generate a diagnostic report based on the view content and family classification.

        :param view_content: The content of the view to analyze.
        :param family: The family classification of the application.
        :param kwargs: Additional parameters for the generation process.
        :return: The generated diagnostic report as a string.
        """
        inputs = {
            "role": "user",
            "content": view_content
        }

        system_prompt = {
            "role": DIAGNOSTIC_SYSTEM_PROMPT["role"],   # 保持role不变
            # 替换内容
            "content": DIAGNOSTIC_SYSTEM_PROMPT["content"].format(Package=package, family=family)
        }
        return self.generate([system_prompt] + inputs, **kwargs)
