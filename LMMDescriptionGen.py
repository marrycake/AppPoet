import openai
from openai import OpenAI
client = OpenAI(api_key="sk-fae386be24bd4dc19e919a8ac9903046",
                base_url="https://api.deepseek.com")


def LLMFieldDescription(feature_type, feature_name):
    # 第一步：设置系统角色
    system_message = {
        "role": "system",
        "content": (
            "You are an Android security expert. "
            "You are familiar with permission, API, URL, uses-feature, method and their function."
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


def LLMMethodDescription(method):
    # 第一步：设置系统角色
    system_message = {
        "role": "system",
        "content": (
            "You are an expert in Dalvik function analysis. "
            "You are skilled in interpreting Dalvik method signatures, instructions, and their behaviors. "
            "Your task is to provide concise descriptions of each method's functionality. "
            "For each analysis, include the method's parameters, what it does, and its return type. "
            "Output only the **function description**, without repeating the input or adding prefixes like 'function:' or 'method:'."
        )
    }

    # 第二步：提供参考示例
    examples = [
        {
            "role": "user",
            "content": """
            {
                "name": "<init>",
                "descriptor": "()V",
                "access_flags": "private constructor",
                "instructions": [
                    {
                        "opcode": "invoke-direct",
                        "operands": "v0, Ljava/lang/Object;-><init>()V"
                    },
                    {
                        "opcode": "return-void",
                        "operands": ""
                    }
                ]
            }
        """
        },
        {
            "role": "assistant",
            "content": "Input: None, Output: None. Initializes an object of the class."
        },
        {
            "role": "user",
            "content": """
            {
                "name": "doSomething",
                "descriptor": "(I)V",
                "access_flags": "public",
                "instructions": [
                    {
                        "opcode": "const",
                        "operands": "v0, 10"
                    },
                    {
                        "opcode": "invoke-virtual",
                        "operands": "v1, v0, Lcom/example/MyClass;->methodToCall(I)V"
                    },
                    {
                        "opcode": "return-void",
                        "operands": ""
                    }
                ]
            }
        """
        },
        {
            "role": "assistant",
            "content": "Input: Integer (I), Output: None. Performs an action with an integer input."
        }
    ]

    inputs = {
        "role": "user",
        "content": f"Method: {method}"
    }

    messages = [system_message] + examples + [inputs]

    return client.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    ).choices[0].message.content


if __name__ == "__main__":
    # 示例调用
    # print(LLMFieldDescription("permission",
    #       "com.google.android.gms.permission.AD_ID"))
    # print("-------------")
    # print(LLMFieldDescription(
    #     "permission", "android.permission.FOREFGROUND_SERVICE"))
    # print("-------------")
    # print(LLMFieldDescription("API",
    #       "android.app.ActivityManager.killBackgroundProcesses"))
    # print("-------------")
    # print(LLMFieldDescription("URL", "p1-lm.adkwai.com"))

    print(LLMMethodDescription("""{
          "name": "switchLeaderboard",
          "descriptor": "(I)V",
          "access_flags": "private",
          "instructions": [
            {
              "opcode": "iget",
              "operands": "v8, v11, Lcom/nom/lib/app/LeaderboardActivity;->mLeaderboardType I"
            },
            {
              "opcode": "if-eq",
              "operands": "v12, v8, +032h"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v11, Lcom/nom/lib/app/LeaderboardActivity;->getApplication()Landroid/app/Application;"
            },
            {
              "opcode": "move-result-object",
              "operands": "v0"
            },
            {
              "opcode": "check-cast",
              "operands": "v0, Lcom/nom/lib/app/YGApplication;"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v0, Lcom/nom/lib/app/YGApplication;->getNumLeaderboardType()I"
            },
            {
              "opcode": "move-result",
              "operands": "v4"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v0, Lcom/nom/lib/app/YGApplication;->getLeaderboardTypeMetaData()[[I"
            },
            {
              "opcode": "move-result-object",
              "operands": "v3"
            },
            {
              "opcode": "const/4",
              "operands": "v1, 0"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v11, Lcom/nom/lib/app/LeaderboardActivity;->getResources()Landroid/content/res/Resources;"
            },
            {
              "opcode": "move-result-object",
              "operands": "v6"
            },
            {
              "opcode": "const/4",
              "operands": "v2, 0"
            },
            {
              "opcode": "if-lt",
              "operands": "v2, v4, +02dh"
            },
            {
              "opcode": "iput",
              "operands": "v12, v11, Lcom/nom/lib/app/LeaderboardActivity;->mLeaderboardType I"
            },
            {
              "opcode": "iget-object",
              "operands": "v8, v11, Lcom/nom/lib/app/LeaderboardActivity;->mlvAdapter Lcom/nom/lib/adapter/LeaderboardArrayAdapterFlip;"
            },
            {
              "opcode": "iget",
              "operands": "v9, v11, Lcom/nom/lib/app/LeaderboardActivity;->mLeaderboardType I"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v8, v9, Lcom/nom/lib/adapter/LeaderboardArrayAdapterFlip;->setScoreType(I)V"
            },
            {
              "opcode": "new-instance",
              "operands": "v7, Lcom/nom/lib/database/LeaderboardCacheUpdateService;"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v11, Lcom/nom/lib/app/LeaderboardActivity;->getApplication()Landroid/app/Application;"
            },
            {
              "opcode": "move-result-object",
              "operands": "v8"
            },
            {
              "opcode": "check-cast",
              "operands": "v8, Lcom/nom/lib/app/YGApplication;"
            },
            {
              "opcode": "iget",
              "operands": "v9, v11, Lcom/nom/lib/app/LeaderboardActivity;->mLeaderboardType I"
            },
            {
              "opcode": "const/4",
              "operands": "v10, 0"
            },
            {
              "opcode": "invoke-direct",
              "operands": "v7, v8, v9, v10, Lcom/nom/lib/database/LeaderboardCacheUpdateService;-><init>(Lcom/nom/lib/app/YGApplication; I Landroid/os/Handler;)V"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v7, Lcom/nom/lib/database/LeaderboardCacheUpdateService;->start()V"
            },
            {
              "opcode": "invoke-direct",
              "operands": "v11, Lcom/nom/lib/app/LeaderboardActivity;->refreshLeaderboard()V"
            },
            {
              "opcode": "iget-object",
              "operands": "v8, v11, Lcom/nom/lib/app/LeaderboardActivity;->mlvAdapter Lcom/nom/lib/adapter/LeaderboardArrayAdapterFlip;"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v8, Lcom/nom/lib/adapter/LeaderboardArrayAdapterFlip;->getPlayersPosition()I"
            },
            {
              "opcode": "move-result",
              "operands": "v5"
            },
            {
              "opcode": "if-lez",
              "operands": "v5, +007h"
            },
            {
              "opcode": "iget-object",
              "operands": "v8, v11, Lcom/nom/lib/app/LeaderboardActivity;->mlvLeaderboard Landroid/widget/ListView;"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v8, v5, Landroid/widget/ListView;->setSelection(I)V"
            },
            {
              "opcode": "return-void",
              "operands": ""
            },
            {
              "opcode": "aget-object",
              "operands": "v8, v3, v2"
            },
            {
              "opcode": "const/4",
              "operands": "v9, 2"
            },
            {
              "opcode": "aget",
              "operands": "v8, v8, v9"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v11, v8, Lcom/nom/lib/app/LeaderboardActivity;->findViewById(I)Landroid/view/View;"
            },
            {
              "opcode": "move-result-object",
              "operands": "v1"
            },
            {
              "opcode": "check-cast",
              "operands": "v1, Landroid/widget/ImageButton;"
            },
            {
              "opcode": "aget-object",
              "operands": "v8, v3, v2"
            },
            {
              "opcode": "const/4",
              "operands": "v9, 0"
            },
            {
              "opcode": "aget",
              "operands": "v8, v8, v9"
            },
            {
              "opcode": "if-ne",
              "operands": "v12, v8, +00dh"
            },
            {
              "opcode": "aget-object",
              "operands": "v8, v3, v2"
            },
            {
              "opcode": "const/4",
              "operands": "v9, 6"
            },
            {
              "opcode": "aget",
              "operands": "v8, v8, v9"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v1, v8, Landroid/widget/ImageButton;->setImageResource(I)V"
            },
            {
              "opcode": "add-int/lit8",
              "operands": "v2, v2, 1"
            },
            {
              "opcode": "goto",
              "operands": "-49h"
            },
            {
              "opcode": "aget-object",
              "operands": "v8, v3, v2"
            },
            {
              "opcode": "const/4",
              "operands": "v9, 5"
            },
            {
              "opcode": "aget",
              "operands": "v8, v8, v9"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v1, v8, Landroid/widget/ImageButton;->setImageResource(I)V"
            },
            {
              "opcode": "goto",
              "operands": "-bh"
            }
          ]
        },"""))

    print(LLMMethodDescription("""{
          "name": "getFriendRank",
          "descriptor": "()J",
          "access_flags": "public",
          "instructions": [
            {
              "opcode": "iget-object",
              "operands": "v0, v2, Lcom/nom/lib/ws/model/LeaderboardScoreObject;->jsonObj Lorg/json/JSONObject;"
            },
            {
              "opcode": "const-string",
              "operands": "v1, \"friend_rank\""
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v0, v1, Lorg/json/JSONObject;->optLong(Ljava/lang/String;)J"
            },
            {
              "opcode": "move-result-wide",
              "operands": "v0"
            },
            {
              "opcode": "return-wide",
              "operands": "v0"
            }
          ]
        },"""))

    print(LLMMethodDescription("""{
      "class_name": "Lcom/google/gson/bf;",
      "methods": [
        {
          "name": "<init>",
          "descriptor": "(Ljava/lang/reflect/Type;)V",
          "access_flags": "public constructor",
          "instructions": [
            {
              "opcode": "invoke-direct",
              "operands": "v3, Ljava/lang/Object;-><init>()V"
            },
            {
              "opcode": "instance-of",
              "operands": "v1, v4, Ljava/lang/Class;"
            },
            {
              "opcode": "if-eqz",
              "operands": "v1, +017h"
            },
            {
              "opcode": "const-class",
              "operands": "v2, Ljava/util/Properties;"
            },
            {
              "opcode": "move-object",
              "operands": "v0, v4"
            },
            {
              "opcode": "check-cast",
              "operands": "v0, Ljava/lang/Class;"
            },
            {
              "opcode": "move-object",
              "operands": "v1, v0"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v2, v1, Ljava/lang/Class;->isAssignableFrom(Ljava/lang/Class;)Z"
            },
            {
              "opcode": "move-result",
              "operands": "v1"
            },
            {
              "opcode": "if-eqz",
              "operands": "v1, +00bh"
            },
            {
              "opcode": "const-class",
              "operands": "v1, Ljava/lang/String;"
            },
            {
              "opcode": "iput-object",
              "operands": "v1, v3, Lcom/google/gson/bf;->a Ljava/lang/reflect/Type;"
            },
            {
              "opcode": "const-class",
              "operands": "v1, Ljava/lang/String;"
            },
            {
              "opcode": "iput-object",
              "operands": "v1, v3, Lcom/google/gson/bf;->b Ljava/lang/reflect/Type;"
            },
            {
              "opcode": "return-void",
              "operands": ""
            },
            {
              "opcode": "instance-of",
              "operands": "v1, v4, Ljava/lang/reflect/ParameterizedType;"
            },
            {
              "opcode": "if-eqz",
              "operands": "v1, +029h"
            },
            {
              "opcode": "new-instance",
              "operands": "v1, Lcom/google/gson/bb;"
            },
            {
              "opcode": "invoke-direct",
              "operands": "v1, v4, Lcom/google/gson/bb;-><init>(Ljava/lang/reflect/Type;)V"
            },
            {
              "opcode": "const-class",
              "operands": "v2, Ljava/util/Map;"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v1, Lcom/google/gson/bb;->b()Ljava/lang/Class;"
            },
            {
              "opcode": "move-result-object",
              "operands": "v1"
            },
            {
              "opcode": "invoke-virtual",
              "operands": "v2, v1, Ljava/lang/Class;->isAssignableFrom(Ljava/lang/Class;)Z"
            },
            {
              "opcode": "move-result",
              "operands": "v1"
            },
            {
              "opcode": "invoke-static",
              "operands": "v1, Lcom/google/gson/at;->a(Z)V"
            },
            {
              "opcode": "check-cast",
              "operands": "v4, Ljava/lang/reflect/ParameterizedType;"
            },
            {
              "opcode": "invoke-interface",
              "operands": "v4, Ljava/lang/reflect/ParameterizedType;->getActualTypeArguments()[Ljava/lang/reflect/Type;"
            },
            {
              "opcode": "move-result-object",
              "operands": "v1"
            },
            {
              "opcode": "const/4",
              "operands": "v2, 0"
            },
            {
              "opcode": "aget-object",
              "operands": "v1, v1, v2"
            },
            {
              "opcode": "iput-object",
              "operands": "v1, v3, Lcom/google/gson/bf;->a Ljava/lang/reflect/Type;"
            },
            {
              "opcode": "invoke-interface",
              "operands": "v4, Ljava/lang/reflect/ParameterizedType;->getActualTypeArguments()[Ljava/lang/reflect/Type;"
            },
            {
              "opcode": "move-result-object",
              "operands": "v1"
            },
            {
              "opcode": "const/4",
              "operands": "v2, 1"
            },
            {
              "opcode": "aget-object",
              "operands": "v1, v1, v2"
            },
            {
              "opcode": "iput-object",
              "operands": "v1, v3, Lcom/google/gson/bf;->b Ljava/lang/reflect/Type;"
            },
            {
              "opcode": "goto",
              "operands": "-2bh"
            },
            {
              "opcode": "new-instance",
              "operands": "v1, Ljava/lang/IllegalArgumentException;"
            },
            {
              "opcode": "const-string",
              "operands": "v2, \"Map objects need to be parameterized unless you use a custom serializer. Use the com.google.gson.reflect.TypeToken to extract the ParameterizedType.\""
            },
            {
              "opcode": "invoke-direct",
              "operands": "v1, v2, Ljava/lang/IllegalArgumentException;-><init>(Ljava/lang/String;)V"
            },
            {
              "opcode": "throw",
              "operands": "v1"
            }
          ]
        },"""))
