
import re


def is_markdown_code_block(str: str):
    pattern = r"```(.*?)\{(.*?)\}(.*?)```"

    return re.search(pattern, str, re.DOTALL)


def extract_code_block(str: str):

    if (not is_markdown_code_block(str)):
        return str

    start = str.find('{')
    end = str.rfind('}')
    if start != -1 and end != -1 and end > start:
        return str[start:end+1]
    return ""  # 没找到符合要求的大括号对时返回空字符串
