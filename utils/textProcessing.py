
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


def getFileBaseName(filePath: str) -> str:
    import os
    baseName = os.path.basename(filePath)
    name, _ = os.path.splitext(baseName)
    return name


def parse_descriptor(descriptor: str):
    """解析 JVM / Dalvik descriptor，忽略空格，不保留分号"""
    descriptor = descriptor.replace(" ", "")

    params_str = descriptor[descriptor.find("(") + 1: descriptor.find(")")]
    return_type_str = descriptor[descriptor.find(")") + 1:]

    params = []
    i = 0
    while i < len(params_str):
        c = params_str[i]
        if c in "BCDFIJSZV":  # 基本类型
            params.append(c)
            i += 1
        elif c == 'L':  # 对象类型
            end = params_str.find(";", i)
            if end == -1:
                raise ValueError(f"缺少分号结束对象类型: {params_str[i:]}")
            params.append(params_str[i:end])  # 去掉分号
            i = end + 1
        elif c == '[':  # 数组类型
            start = i
            i += 1
            while i < len(params_str) and params_str[i] == '[':
                i += 1
            if i < len(params_str) and params_str[i] == 'L':
                end = params_str.find(";", i)
                if end == -1:
                    raise ValueError(f"缺少分号结束对象类型: {params_str[i:]}")
                params.append(params_str[start:end])  # 包含所有前缀 [
                i = end + 1
            else:
                params.append(params_str[start:i + 1])  # 基本类型数组
                i += 1
        else:
            raise ValueError(f"未知类型前缀: {c}")

    return params, return_type_str
