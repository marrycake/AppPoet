
import json
from openai import OpenAI

from utils.textProcessing import extract_code_block
client = OpenAI(api_key="sk-fae386be24bd4dc19e919a8ac9903046",
                base_url="https://api.deepseek.com")


def get_deepseek_diagnostic(view_content, family):

    system_message = {
        "role": "system",
        "content": (
            f"You are an expert in the field of Android security, specializing in auditing Android applications by static analysis. Your task is to combine known information and your expert knowledge to generate a diagnostic report for the given Android application."
            f"<Task Description>: “‘ You must strictly follow the following steps to analyze the application with the package name \"{{Package}}\" and output a diagnostic report: 1- First, you should know that the application is classified as {family} by the classifier. 2- Then, you get the descriptions and summaries under different views as follows. 2.1- <Permission View>  2.1.1- <requested permission>: {{requested permission’s function description list}} 2.1.2- <used permission>: {{used permission’s function description list}} 2.1.3- <permission view summary>: {{permission view summary }} 2.2- <API View>  2.2.1- <restricted API>: {{restricted API’s function description list}} 2.2.2- <suspicious API>: {{suspicious API’s function description list}} 2.2.3- <API view summary>: {{API view summary }} 2.3- <URL & uses-feature View>  2.3.1- <uses-feature>: {{uses-feature’s function description list}} 2.3.2- <URL>: {{URL’s function description list}}  2.3.3- <URL & uses-feature view summary>: {{URL & uses-feature view summary }} 3- Now you have known not only the application is malicious or not, but also feature function descriptions and view behavior summaries from different views. You should start a static analysis with above information, and generate diagnostic report for the application based on <Output Description and Requirements>. “‘"
            f"<Output Description and Requirements>: “‘ 1- Your diagnostic report should be based on the above information, focusing on behavior about their potential risks. 2- Your report should contain a summary that describes all possible potential risks in points. The summary must take into account malicious behavior across all views. Each point of potentially malicious behavior needs to point out specific risk points, such as that one feature, API, etc. 3- Your report should provide detailed guidance on next steps for further detection based on summarized potentially malicious behavior. “‘"
            f"<Nouns Interpretation>: “‘1- <Permission View>: Perspectives on application behavior based on the permissions in the application. 2- <Permission>: Information about the permissions of the application, including: 2.1- <requested permission>: the set of permissions required by the application as declared in the xml file. 2.2- <used permission>: the set of permissions actually used in the application source code. 3- <API view>: Perspectives on application behavior based on the use of sensitive APIs in the application source code. 4- <API>: Sensitive APIs called by the application, including: 4.1- <restricted API>: a set of APIs that require specific permissions to be applied. 4.2- <suspicious API>: some other sensitive APIs used by the application, which may be related to the access of sensitive information and resources. 5- <URL & uses-feature View>: Perspectives on application behavior based on the uses-features declared in xml e and the URLs coding in the APP’s source code. 6- <uses-feature>: Hardware or software feature requirements registered in the xml file for a given application, requiring access to specific hardware clearly has security implications, as the use of certain hardware combinations often reflects potentially malicious behavior. 7- <URL>: URLs found in the source code, some of these addresses might be involved in botnets and thus present in several malware samples. “‘"
        )
    }
    # 你接下去调用接口的代码...

    inputs = {
        "role": "user",
        "content": view_content
    }

    messages = [system_message] + [inputs]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # 示例调用
    with open('features/apk_description.json', 'r', encoding='utf-8') as f:
        data = json.load(f)          # 解析为Python对象

    json_str = json.dumps(data)      # 转成字符串
    print(get_deepseek_diagnostic(json_str))
