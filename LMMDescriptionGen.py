import openai
from openai import OpenAI
client = OpenAI(api_key="sk-fae386be24bd4dc19e919a8ac9903046",
                base_url="https://api.deepseek.com")


def get_deepseek_response(feature_type, feature_name):
    # 第一步：设置系统角色
    system_message = {
        "role": "system",
        "content": (
            "You are an Android security expert. "
            "You are familiar with permission, API, URL, uses-feature and their function."
            "Your responses must strictly follow the format used in the examples. "
            "Output only the **function description**, without repeating the input or using any prefixes like 'function:'."
        )
    }

    # 第二步：提供参考示例
    examples = [
        {"role": "user", "content": "permission: android.permission.WRITE_SMS"},
        {"role": "assistant", "content": "allow sending and editing SMS"},
        {"role": "user", "content": "API: android.telephony.TelephonyManager.getSubscriberId"},
        {"role": "assistant", "content": "subscriber ID retrieval"},
        {"role": "user", "content": "uses-feature: android.hardware.screen.landscape"},
        {"role": "assistant",
            "content": "landscape screen orientation support for Android devices"},
        {"role": "user", "content": "URL: 360.cn"},
        {"role": "assistant",
            "content": "Qihoo 360-related domains (a Chinese internet security company known for antivirus software, web browsers, and mobile application stores)"}
    ]

    inputs = {
        "role": "user",
        "content": f"{feature_type}: {feature_name}"
    }

    messages = [system_message] + examples + [inputs]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # 示例调用
    print(get_deepseek_response("permission",
          "com.google.android.gms.permission.AD_ID"))
    print("-------------")
    print(get_deepseek_response(
        "permission", "android.permission.FOREFGROUND_SERVICE"))
    print("-------------")
    print(get_deepseek_response("API",
          "android.app.ActivityManager.killBackgroundProcesses"))
    print("-------------")
    print(get_deepseek_response("URL", "p1-lm.adkwai.com"))
