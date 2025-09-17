from typing import List, Dict, Optional
from collections import defaultdict
from collections import defaultdict, deque
import asyncio
import hashlib
import json

import re

from LLM import LLMAsyncGen
from LLM.LLMGen import LLMGen
from logger import Logger
from memory import Memory
from persistence.persistence import Persistence


FEATURE_SEMAPHORE = asyncio.Semaphore(50)  # 可调，特征描述
METHOD_SEMAPHORE = asyncio.Semaphore(50)   # 可调，方法描述
CLASS_SEMAPHORE = asyncio.Semaphore(20)     # 可调，类批次

black_filter_patterns = [
    # Java 核心库
    r"^Ljava/.*",                       # java.* 包
    r"^Ljavax/.*",                      # javax.* 包
    r"^Ljava/net/.*",                    # java.net.*
    r"^Ljava/io/.*",                     # java.io.*
    r"^Ljava/nio/.*",                    # java.nio.*
    r"^Ljava/util/.*",                   # java.util.*
    r"^Ljava/text/.*",                   # java.text.*
    r"^Ljava/math/.*",                   # java.math.*
    r"^Ljava/lang/ref/.*",               # java.lang.ref.*
    r"^Ljava/lang/reflect/.*",           # java.lang.reflect.*
    r"^Ljava/security/.*",               # java.security.*
    r"^Ljava/sql/.*",                     # java.sql.*

    # Kotlin 标准库
    r"^Lkotlin/.*",
    r"^Lkotlinx/.*",

    # Android 系统框架
    r"^Landroid/.*",                     # android.* 包
    r"^Landroidx/.*",                    # androidx.* 包
    r"^Ldalvik/.*",                      # Dalvik VM 内置类
    r"^Lcom/android/.*",                 # Android 官方类
    r"^Lcom/google/android/.*",          # Google 官方 Android 库
    r"^Lcom/google/common/.*",           # Guava 等 Google 常用库
    r"^Lcom/google/gson/.*",             # Gson 库
    r"^Lcom/google/firebase/.*",         # Firebase SDK
    r"^Lcom/google/protobuf/.*",         # Protobuf 库
    r"^Lorg/json/.*",                     # JSON 库
    r"^Lorg/w3c/dom/.*",                  # DOM
    r"^Lorg/xml/sax/.*",                  # SAX
    r"^Lorg/apache/.*",                   # Apache 常用库
    r"^Lorg/ietf/jgss/.*",                # 安全相关
    r"^Lorg/omg/.*",                      # CORBA 等
    r"^Lorg/junit/.*",                    # 测试库
    r"^Landroid/support/.*",             # 旧版 Support 库
    r"^Lcom/android/support/.*",         # 旧版 Support 库
]


def readFromFile(file_path):
    with open(file_path, 'r') as file:
        return json.load(fp=file)


def parseApkFeatures(file_path):
    features = readFromFile(file_path)
    RequestedPermission = features.get("RequestedPermission", [])
    UsedPermission = features.get("UsedPermission", [])
    RestrictedAPIs = features.get("RestrictedAPIs", [])
    SuspiciousAPIs = features.get("SuspiciousAPIs", [])
    HardwareComponentsList = features.get("HardwareComponentsList", [])
    URLDomains = features.get("URL", [])
    classFeatures = features.get("UsedMethods", [])
    return RequestedPermission, UsedPermission, RestrictedAPIs, SuspiciousAPIs, HardwareComponentsList, URLDomains, classFeatures


def addDescription(featureList, featureType, memory: Memory, llmGen: LLMGen
                   ):
    featureDict = {}
    for feature in featureList:
        featureDict[feature] = addSingleDescription(
            feature, featureType, memory, llmGen)
    return featureDict


def addSingleDescription(feature, featureType, memory: Memory, llmGen: LLMGen):
    if not memory.hexists(featureType, feature):
        description = llmGen.generate_field_description(featureType, feature)
        memory.hset(featureType, feature, description)
        Logger.debug(
            f"\033[31mdescription for LLM\033[0m {featureType}: {feature} -> {description}"
        )
    else:
        description = memory.hget(featureType, feature)
        Logger.debug(
            f"description for CACHE {featureType}: {feature} -> {description}")
    return description


def addSingleDescriptionToUnstructuredString(feature, featureType, memory: Memory, llmGen: LLMGen):
    featureHash = hashlib.sha256(feature.encode()).hexdigest()
    if not memory.hexists(featureType, featureHash):
        description = llmGen.generate_method_description(feature)
        memory.hset(featureType, featureHash, description)
        Logger.debug(
            f"\033[31mdescription for LLM\033[0m {featureType}: {featureHash} -> {description}"
        )
    else:
        description = memory.hget(featureType, featureHash)
        Logger.debug(
            f"description for CACHE {featureType}: {featureHash} -> {description}")
    return description


def createView(requestedPermissionFeatureDict, usedPermissionFeatureDict, restrictedAPIFeatureDict,
               suspiciousAPIFeatureDict, hardwareComponentsFeatureDict, urlDomainFeatureDict, classFeatureDict):
    view = {
        "Permission View": {"requested permission": requestedPermissionFeatureDict, "used permission": usedPermissionFeatureDict},
        "API View": {"restricted API": restrictedAPIFeatureDict, "suspicious API": suspiciousAPIFeatureDict},
        "URL & uses-feature View": {"uses-feature": hardwareComponentsFeatureDict, "URL": urlDomainFeatureDict},
        "Class View": classFeatureDict
    }
    return view


def descriptGen(file_path, memory: Memory, llmGen: LLMGen, outputPath):
    jsonView = descriptGen(file_path, memory, llmGen)

    with open(outputPath, 'w', encoding='utf-8') as f:
        json.dump(jsonView, f, indent=4)


def descriptGen(file_path, memory, llmGen: LLMGen) -> str:
    RequestedPermission, UsedPermission, RestrictedAPIs, SuspiciousAPIs, HardwareComponentsList, URLDomains, classFeatures = parseApkFeatures(
        file_path)

    requestedPermissionFeatureDict = addDescription(
        RequestedPermission, "permission", memory, llmGen)
    usedPermissionFeatureDict = addDescription(
        UsedPermission, "permission", memory, llmGen)
    restrictedAPIFeatureDict = addDescription(
        RestrictedAPIs, "API", memory, llmGen)
    suspiciousAPIFeatureDict = addDescription(
        SuspiciousAPIs, "API", memory, llmGen)
    hardwareComponentsFeatureDict = addDescription(
        HardwareComponentsList, "uses-feature", memory, llmGen)
    urlDomainFeatureDict = addDescription(URLDomains, "URL", memory, llmGen)
    classFeatureDict = {}
    for classFeature in classFeatures:
        methodDict = {}
        className = classFeature["class_name"]
        classMethods = classFeature["methods"]
        for classMethod in classMethods:
            methodFullName = f"{classMethod['access_flags']} {classMethod['name']} {classMethod['descriptor']}"
            methodDescription = addSingleDescriptionToUnstructuredString(
                json.dumps(classMethod), "Method", memory, llmGen)
            methodDict[methodFullName] = methodDescription
        classFeatureDict[className] = methodDict

    return createView(requestedPermissionFeatureDict, usedPermissionFeatureDict,
                      restrictedAPIFeatureDict, suspiciousAPIFeatureDict,
                      hardwareComponentsFeatureDict, urlDomainFeatureDict, classFeatureDict)


async def asyncAddDescription(featureList, featureType, memory: Memory, llmGen: LLMAsyncGen):
    tasks = [
        asyncAddSingleDescription(feature, featureType, memory, llmGen)
        for feature in featureList
    ]
    results = await asyncio.gather(*tasks)
    featureDict = dict(zip(featureList, results))
    return featureDict


async def asyncAddSingleDescription(feature, featureType, memory: Memory, llmGen: LLMAsyncGen):
    if not memory.hexists(featureType, feature):
        description = await llmGen.generate_field_description(featureType, feature)
        memory.hset(featureType, feature, description)
        Logger.debug(
            f"\033[31mdescription for LLM\033[0m {featureType}: {feature} -> {description}"
        )
    else:
        description = memory.hget(featureType, feature)
        Logger.debug(
            f"description for CACHE {featureType}: {feature} -> {description}")
    return description


async def asyncAddSingleDescriptionToUnstructuredString(feature, featureType, memory: Memory, llmGen: LLMAsyncGen):
    featureHash = hashlib.sha256(feature.encode()).hexdigest()
    if not memory.hexists(featureType, featureHash):
        description = await llmGen.generate_method_description(feature)
        memory.hset(featureType, featureHash, description)
        Logger.debug(
            f"\033[31mdescription for LLM\033[0m {featureType}: {featureHash} -> {description}"
        )
    else:
        description = memory.hget(featureType, featureHash)
        Logger.debug(
            f"description for CACHE {featureType}: {featureHash} -> {description}")
    return description


async def asyncDescriptGen(file_path, memory: Memory, llmGen: LLMAsyncGen, outputPath):
    jsonView = await asyncDescriptGen(file_path, memory, llmGen)

    with open(outputPath, 'w', encoding='utf-8') as f:
        json.dump(jsonView, f, indent=4)


async def asyncDescriptGen(persistence: Persistence, memory, llmGen: LLMAsyncGen) -> str:

    appInfo = persistence.query({"type": "app_info"})[0]
    RequestedPermission = appInfo.get("requested_permissions", [])
    UsedPermission = appInfo.get("used_permissions", [])
    RestrictedAPIs = appInfo.get("restricted_apis", [])
    SuspiciousAPIs = appInfo.get("suspicious_apis", [])
    HardwareComponentsList = appInfo.get("hardware_components", [])
    URLDomains = appInfo.get("urls", [])

    (
        requestedPermissionFeatureDict,
        usedPermissionFeatureDict,
        restrictedAPIFeatureDict,
        suspiciousAPIFeatureDict,
        hardwareComponentsFeatureDict,
        urlDomainFeatureDict,
    ) = await asyncio.gather(
        asyncAddDescription(RequestedPermission, "permission", memory, llmGen),
        asyncAddDescription(UsedPermission, "permission", memory, llmGen),
        asyncAddDescription(RestrictedAPIs, "API", memory, llmGen),
        asyncAddDescription(SuspiciousAPIs, "API", memory, llmGen),
        asyncAddDescription(HardwareComponentsList,
                            "uses-feature", memory, llmGen),
        asyncAddDescription(URLDomains, "URL", memory, llmGen),
    )

    classInfos = persistence.query({"type": "class_info"})

    parent_map = build_parent_to_children_map(classInfos)
    class_dependency_map, method_dependency_map, method_self_dependency_map = build_class_dependency_map(
        classInfos, black_filter_patterns)

    Logger.debug(
        f"class_dependency_map over"
    )

    activity_subclasses = filter_by_superclass(
        parent_map, "Landroid/app/Activity;")
    service_subclasses = filter_by_superclass(
        parent_map, "Landroid/app/Service;")
    broadcast_receiver_subclasses = filter_by_superclass(
        parent_map, "Landroid/content/BroadcastReceiver;")
    content_provider_subclasses = filter_by_superclass(
        parent_map, "Landroid/content/ContentProvider;")
    application_subclasses = filter_by_superclass(
        parent_map, "Landroid/app/Application;")

    Logger.debug(
        f"filter over"
    )

    ordered_classes_batches = adjust_analysis_order_generic(
        class_dependency_map, activity_subclasses +
        service_subclasses + broadcast_receiver_subclasses + content_provider_subclasses + application_subclasses)

    Logger.debug(
        f"ordered_classes_batches over"
    )

    ordered_class_methods_batches = defaultdict(lambda: defaultdict(list))

    for class_item, class_method_item in method_self_dependency_map.items():
        method_batches = adjust_analysis_order_generic(
            class_method_item, None, False)
        ordered_class_methods_batches[class_item] = method_batches

    Logger.debug(
        f"ordered_class_methods_batches over"
    )

    classFeatureDict = defaultdict(lambda: defaultdict(str))
    classMethodFeatureDict = defaultdict(
        lambda: defaultdict(lambda: defaultdict(str)))
    for batch in ordered_classes_batches:
        batch_tasks = []
        for classInfo in classInfos:
            if classInfo["class_name"] in batch:
                batch_tasks.append(asyncAddDescriptionToClassMethods(
                    classInfo, classMethodFeatureDict, ordered_class_methods_batches, method_dependency_map, memory, llmGen))
        Logger.debug(
            f"in asyncio"
        )
        await asyncio.gather(*batch_tasks)

    for className in activity_subclasses:
        classFeatureDict["Activitys"][className] = classMethodFeatureDict[className]
    for className in service_subclasses:
        classFeatureDict["Services"][className] = classMethodFeatureDict[className]
    for className in broadcast_receiver_subclasses:
        classFeatureDict["BroadcastReceivers"][className] = classMethodFeatureDict[className]
    for className in content_provider_subclasses:
        classFeatureDict["ContentProviders"][className] = classMethodFeatureDict[className]
    for className in application_subclasses:
        classFeatureDict["Applications"][className] = classMethodFeatureDict[className]

    return createView(requestedPermissionFeatureDict, usedPermissionFeatureDict,
                      restrictedAPIFeatureDict, suspiciousAPIFeatureDict,
                      hardwareComponentsFeatureDict, urlDomainFeatureDict, classFeatureDict)


# async def asyncAddDescriptionToClassMethods(classInfo, classMethodFeatureDict,
#                                             ordered_class_methods_batches, method_dependency_map,
#                                             memory: Memory, llmGen: LLMAsyncGen):
#     for method_batch in ordered_class_methods_batches[classInfo["class_name"]]:
#         tasks = {}
#         # 创建任务字典，键为方法名，值为异步任务
#         for method_item in classInfo["methods"]:
#             if method_item["name"] in method_batch:
#                 dep_classes_descriptions = {
#                     depClassName: classMethodFeatureDict[depClassName]
#                     for depClassName in method_dependency_map.get(classInfo["class_name"], {}).get(method_item["name"], [])
#                 }
#                 dep_classes_descriptions.update({
#                     classInfo["class_name"]: classMethodFeatureDict[classInfo["class_name"]]
#                 })
#                 tasks[method_item["name"]] = tasks[method_item["name"]] = asyncio.create_task(
#                     asyncAddSingleMethodDescription(
#                         method_item, dep_classes_descriptions, memory, llmGen)
#                 )

#         # 并行执行所有任务
#         # batch_results = await asyncio.gather(*tasks.values())

#         # 使用字典映射保证结果与方法名对应
#         for method_name, result in zip(tasks.keys(), batch_results):
#             classMethodFeatureDict[classInfo["class_name"]
#                                    ]["methods"][method_name] = result

#     classDescription = await asyncAddDescriptionToClass(classInfo, classMethodFeatureDict, memory, llmGen)
#     classMethodFeatureDict[classInfo["class_name"]
#                            ]["description"] = classDescription

# async def asyncAddDescriptionToClassMethods(classInfo, classMethodFeatureDict,
#                                             ordered_class_methods_batches, method_dependency_map,
#                                             memory: Memory, llmGen: LLMAsyncGen):
#     for method_batch in ordered_class_methods_batches[classInfo["class_name"]]:
#         tasks = {}
#         for method_item in classInfo["methods"]:
#             if method_item["name"] in method_batch:
#                 dep_classes_descriptions = {
#                     depClassName: classMethodFeatureDict.get(depClassName, {})
#                     for depClassName in method_dependency_map.get(classInfo["class_name"], {}).get(method_item["name"], [])
#                 }
#                 dep_classes_descriptions[classInfo["class_name"]] = classMethodFeatureDict.get(
#                     classInfo["class_name"], {})

#                 tasks[method_item["name"]] = asyncio.create_task(
#                     asyncAddSingleMethodDescription(
#                         method_item, dep_classes_descriptions, memory, llmGen)
#                 )

#         # 并行执行所有任务并更新结果
#         for method_name, task in tasks.items():
#             classMethodFeatureDict[classInfo["class_name"]]["methods"][method_name] = await task

#     classDescription = await asyncAddDescriptionToClass(classInfo, classMethodFeatureDict, memory, llmGen)
#     classMethodFeatureDict[classInfo["class_name"]
#                            ]["description"] = classDescription

# async def asyncAddDescriptionToClassMethods(classInfo, classMethodFeatureDict,
#                                             ordered_class_methods_batches, method_dependency_map,
#                                             memory: Memory, llmGen: LLMAsyncGen):
#     # 遍历每个方法批次
#     for method_batch in ordered_class_methods_batches[classInfo["class_name"]]:
#         # 批内顺序执行每个方法
#         for method_item in classInfo["methods"]:
#             if method_item["name"] in method_batch:
#                 # 收集依赖描述
#                 dep_classes_descriptions = {
#                     depClassName: classMethodFeatureDict.get(depClassName, {})
#                     for depClassName in method_dependency_map.get(classInfo["class_name"], {}).get(method_item["name"], [])
#                 }
#                 dep_classes_descriptions[classInfo["class_name"]] = classMethodFeatureDict.get(
#                     classInfo["class_name"], {}
#                 )

#                 # 顺序 await，避免批内死锁
#                 result = await asyncAddSingleMethodDescription(
#                     method_item, dep_classes_descriptions, memory, llmGen
#                 )
#                 # 更新 classMethodFeatureDict
#                 classMethodFeatureDict[classInfo["class_name"]
#                                        ]["methods"][method_item["name"]] = result

#     # 最后生成类描述
#     classDescription = await asyncAddDescriptionToClass(classInfo, classMethodFeatureDict, memory, llmGen)
#     classMethodFeatureDict[classInfo["class_name"]
#                            ]["description"] = classDescription

async def asyncAddDescriptionToClassMethods(classInfo, classMethodFeatureDict,
                                            ordered_class_methods_batches, method_dependency_map,
                                            memory: Memory, llmGen: LLMAsyncGen):
    async with CLASS_SEMAPHORE:  # 控制同批并发类数量
        for method_batch in ordered_class_methods_batches[classInfo["class_name"]]:
            # 批内顺序执行
            for method_item in classInfo["methods"]:
                if method_item["name"] in method_batch:
                    dep_classes_descriptions = {
                        depClassName: classMethodFeatureDict.get(
                            depClassName, {})
                        for depClassName in method_dependency_map.get(classInfo["class_name"], {}).get(method_item["name"], [])
                    }
                    dep_classes_descriptions[classInfo["class_name"]] = classMethodFeatureDict.get(
                        classInfo["class_name"], {})

                    async with METHOD_SEMAPHORE:  # 控制方法级别并发
                        result = await asyncAddSingleMethodDescription(
                            method_item, dep_classes_descriptions, memory, llmGen
                        )
                    classMethodFeatureDict[classInfo["class_name"]
                                           ]["methods"][method_item["name"]] = result

        # 类描述最后生成
        classDescription = await asyncAddDescriptionToClass(classInfo, classMethodFeatureDict, memory, llmGen)
        classMethodFeatureDict[classInfo["class_name"]
                               ]["description"] = classDescription


async def asyncAddSingleMethodDescription(method_item, dep_classes_descriptions, memory: Memory, llmGen: LLMAsyncGen):
    method_uuid = str(method_item["method_id"])
    if not memory.hexists("Methods", method_uuid):
        feature = {k: v for k, v in method_item.items() if k != "method_id"}
        feature.update({"ref_classes": dep_classes_descriptions})
        description = await llmGen.generate_method_description(feature)
        memory.hset("Methods", method_uuid, description)
        Logger.debug(
            f"\033[31mdescription for LLM\033[0m Methods {method_uuid} -> {description}"
        )
    else:
        description = memory.hget("Methods", method_uuid)
        Logger.debug(
            f"description for CACHE Methods: {method_uuid} -> {description}")
    return description


async def asyncAddDescriptionToClass(classInfo, classMethodFeatureDict, memory: Memory, llmGen: LLMAsyncGen):
    class_uuid = str(classInfo["class_id"])
    if not memory.hexists("Classes", class_uuid):
        feature = {
            "class_name": classInfo["class_name"],
            "superclass_name": classInfo["superclass_name"],
            "fields": classInfo["fields"],
            "methods": classMethodFeatureDict[classInfo["class_name"]]["methods"]
        }
        description = await llmGen.generate_method_description(feature)
        memory.hset("Classes", class_uuid, description)
        Logger.debug(
            f"\033[31mdescription for LLM\033[0m Classes {class_uuid} -> {description}"
        )
    else:
        description = memory.hget("Classes", class_uuid)
        Logger.debug(
            f"description for CACHE Classes: {class_uuid} -> {description}")
    return description


def build_parent_to_children_map(class_infos):
    parent_map = defaultdict(list)
    for cls in class_infos:
        parent = cls.get("superclass_name")
        if parent:
            parent_map[parent].append(cls.get("class_name"))
    return parent_map


def build_class_dependency_map(class_info, black_filter_patterns):
    """
    构建类依赖关系映射 + 方法依赖关系映射。
    :param class_info: 类信息列表
    :param black_filter_patterns: 正则表达式字符串列表，用于过滤不需要的类
    :return: (class_dependency_map, method_dependency_map)
    """
    class_dependency_map = defaultdict(set)
    method_dependency_map = defaultdict(
        lambda: defaultdict(set))
    method_self_dependency_map = defaultdict(
        lambda: defaultdict(set))  # 方法对自身类内方法的依赖

    blacklist = [re.compile(p) for p in black_filter_patterns]

    def is_blacklisted(class_name: str) -> bool:
        return any(p.match(class_name) for p in blacklist)

    # pattern = re.compile(r"L[\w/$]+;")  # 匹配 Lxxx/xxx; 形式的类名
    pattern = re.compile(r"(L[\w/$]+;)(?:->(\w+)\(([^\)]*)\))?")

    for cls in class_info:
        class_name = cls["class_name"]
        if is_blacklisted(class_name):
            continue

        if not is_blacklisted(cls["superclass_name"]):
            class_dependency_map[class_name].add(cls["superclass_name"])

        for method in cls.get("methods", []):
            method_name = f"{method['name']}"
            method_self_dependency_map[class_name][method_name] = set()
            for instruction in method.get("instructions", []):
                operands = instruction.get("operands", "")
                matches = set(pattern.findall(operands))
                for match in matches:
                    m_class_name = match[0]
                    m_method_name = match[1]
                    # m_params = match[2]

                    if not is_blacklisted(m_class_name):
                        if m_class_name == class_name and m_method_name:
                            method_self_dependency_map[class_name][method_name].add(
                                m_method_name)
                        else:
                            # 更新类依赖
                            class_dependency_map[class_name].add(m_class_name)
                            # 更新方法依赖
                            method_dependency_map[class_name][method_name].add(
                                m_class_name)

    # 转 list 方便存储/序列化
    return (
        {k: list(v) for k, v in class_dependency_map.items()},
        {cls: {m: list(deps) for m, deps in mdeps.items()}
         for cls, mdeps in method_dependency_map.items()},
        {cls: {m: list(deps) for m, deps in mdeps.items()}
         for cls, mdeps in method_self_dependency_map.items()}
    )


def filter_by_superclass(parent_map, superclass_name):
    """
    返回所有直接或间接继承自 superclass_name 的类（不包含父类本身）
    """
    result = []
    queue = deque(parent_map.get(superclass_name, []))  # 直接子类

    while queue:
        class_name = queue.popleft()
        result.append(class_name)
        # 将当前类的子类加入队列继续遍历
        queue.extend(parent_map.get(class_name, []))

    return result


def adjust_analysis_order(class_dependency_map, main_classes):
    """
    根据类依赖关系调整分析顺序，确保依赖的类先被分析。
    :param class_dependency_map: 类依赖关系映射
    :param main_classes: 主要类列表（如 Activity、Service 等）
    :return: 调整后的类列表
    """
    visited = set()
    ordered_classes = []

    def dfs(class_name):
        if class_name in visited:
            return
        visited.add(class_name)
        for dep in class_dependency_map.get(class_name, []):
            dfs(dep)
        ordered_classes.append(class_name)

    for main_class in main_classes:
        dfs(main_class)

    return ordered_classes


def adjust_analysis_order_generic(
    dependency_map: Dict[str, List[str]],
    main_classes: Optional[List[str]] = None,
    prioritize_main: bool = True
) -> List[List[str]]:
    """
    批量分层拓扑排序。
    - 可选择只分析 main_classes 的依赖闭包
    - 批内排序可选择将主要类放后
    - 若存在环，最后一批包含环中剩余节点

    :param dependency_map: 类或方法依赖映射
    :param main_classes: 可选，主要类列表
    :param prioritize_main: 批内是否把主要类放后
    :return: List[List[str]]，每批次一个列表
    """
    # -------- Step 1: 收集分析节点 --------
    if main_classes:
        relevant_nodes = set()

        def dfs(node):
            if node in relevant_nodes:
                return
            relevant_nodes.add(node)
            for dep in dependency_map.get(node, []):
                dfs(dep)

        for m in main_classes:
            dfs(m)
        main_set = set(main_classes)
    else:
        relevant_nodes = set(dependency_map.keys())
        for deps in dependency_map.values():
            relevant_nodes.update(deps)
        main_set = set()

    # -------- Step 2: 构建子图 --------
    adj = defaultdict(list)  # dep -> [node...]
    indeg = {n: 0 for n in relevant_nodes}

    for node in relevant_nodes:
        for dep in dependency_map.get(node, []):
            if dep in relevant_nodes:
                adj[dep].append(node)
                indeg[node] += 1

    # -------- Step 3: Kahn 分层拓扑 --------
    dq = deque(sorted(n for n, d in indeg.items() if d == 0))
    batches, processed = [], set()

    while dq:
        size = len(dq)
        current_layer = []
        for _ in range(size):
            n = dq.popleft()
            if n not in processed:
                current_layer.append(n)

        # 批内排序
        if prioritize_main and main_set:
            current_layer.sort(key=lambda x: (x in main_set, x))
        else:
            current_layer.sort()

        batch, next_zero = [], []
        for n in current_layer:
            batch.append(n)
            processed.add(n)
            for v in adj.get(n, []):
                indeg[v] -= 1
                if indeg[v] == 0:
                    next_zero.append(v)

        if batch:
            batches.append(batch)
        if next_zero:
            dq.extend(sorted(set(next_zero)))

    # -------- Step 4: 检测环 --------
    if len(processed) < len(relevant_nodes):
        remaining = sorted(n for n in relevant_nodes if n not in processed)
        batches.append(remaining)

    return batches
