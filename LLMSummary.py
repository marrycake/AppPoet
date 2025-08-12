
import json
from openai import OpenAI

from utils.textProcessing import extract_code_block
client = OpenAI(api_key="sk-fae386be24bd4dc19e919a8ac9903046",
                base_url="https://api.deepseek.com")


def get_deepseek_summary(jsonStr):
    # 第一步：设置系统角色
    system_message = {
        "role": "system",
        "content": (
            "You are an expert in the field of Android security, specializing in auditing Android applications by static analysis. "
            "Your task is to combine known information and your expert knowledge to generate statements and summaries of objectivity for a given Android application."
            "<Task Description>: ‘You must strictly follow the following steps to analyze the application with the package name \"{Package}\" and output as <Output Description and Requirements> required: "
            "1- First, you get the descriptions under different views of the application as follows. "
            "1.1- <Permission View> "
            "1.1.1- <requested permission>: {requested permission function descriptions} "
            "1.1.2- <used permission>: {used permission function descriptions} "
            "1.2- <API View> "
            "1.2.1- <restricted API>: {restricted API function descriptions} "
            "1.2.2- <suspicious API>: {suspicious API function descriptions} "
            "1.3- <URL & uses-feature View> "
            "1.3.1- <uses-feature>: {uses-feature function function descriptions} "
            "1.3.2- <URL>: {URL function function descriptions} "
            "1.4- <Class View> "
            "1.4.1- <className>: [method, methodDescription}] "
            "2- Now you have known feature function descriptions from different views. You should start a static analysis with the above information and generate <view summary> for each view based on <Output Description and Requirements>."
            "<Output Description and Requirements>: ‘"
            "1- Please refer strictly to the following output format and requirement to output the contents of the JSON object, it means you should only output the JSON as follow, without any other thing: "
            "Output format: {"
            "  \"Permission View Summary\": Interpretation and summary of known information on <Permission View>, focusing on behavioral about high-risk permissions and their potential risks. "
            "  \"API View Summary\": Interpretation and summary of known information on <API View>, focusing on behavioral about high-risk APIs and their potential risks. "
            "  \"URL & uses-feature View Summary\": Interpretation and summary of known information on <URL & uses-feature View>, focusing on behavioral about high-risk URLs and uses-features and their potential risks. "
            "  \"Class View Summary\": Interpretation and summary of known information on <Class View>, focusing on behavioral about methods of the classes and their potential risks."
            "} "
            "2- Please provide objective summaries of the application strictly in terms of each view, and speculation about the behavior of the application should be strictly based on facts and known information. "
            "3- If there is missing information in some aspects, such as content is empty, it means that the application has no information about the aspects. "
            "4- Your output should be free of extensions and suggestions, such as \"Further exploration is required, \" \"Further dynamic analysis is required, \" \"Additional information needs to be combined, \" etc., as well as your own subjective assumptions, such as \"There may be a plausible explanation for these behaviors, but they may also be indicative of potential privacy risks or malicious behaviors of the application.\" "
            "5- When you output the result, do not appear extra descriptions such as ’JSON’ or “‘ etc. Just output the JSON object. "
            "<Nouns Interpretation>: ‘"
            "1- <Permission View>: Perspectives on application behavior based on the permissions in the application. "
            "2- <Permission>: Information about the permissions of the application, including: "
            "2.1- <requested permission>: the set of permissions required by the application as declared in the xml file. "
            "2.2- <used permission>: the set of permissions actually used in the application source code. "
            "3- <API view>: Perspectives on application behavior based on the use of sensitive APIs in the application source code. "
            "4- <API>: Sensitive APIs called by the application, including: "
            "4.1- <restricted API>: a set of APIs that require specific permissions to be applied. "
            "4.2- <suspicious API>: some other sensitive APIs used by the application, which may be related to the access of sensitive information and resources. "
            "5- <URL & uses-feature View>: Perspectives on application behavior based on the uses-features declared in xml and the URLs coding in the APP’s source code. "
            "6- <uses-feature>: Hardware or software feature requirements registered in the xml file for a given application, requiring access to specific hardware clearly has security implications, as the use of certain hardware combinations often reflects potentially malicious behavior. "
            "7- <URL>: URLs found in the source code, some of these addresses might be involved in botnets and thus present in several malware samples. "
            "8- <Class View>: Perspectives on application behavior based on the structure and methods of the application's classes, including how these methods interact with other parts of the application and their potential risks."
        )
    }

    inputs = {
        "role": "user",
        "content": jsonStr
    }

    messages = [system_message] + [inputs]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )

    return extract_code_block(response.choices[0].message.content)


if __name__ == "__main__":
    # 示例调用
    with open('features/apk_description.json', 'r', encoding='utf-8') as f:
        data = json.load(f)          # 解析为Python对象

    json_str = json.dumps(data)      # 转成字符串
    print(get_deepseek_summary(json_str))
