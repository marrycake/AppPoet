from collections import defaultdict
import json
from descriptioniGen import adjust_analysis_order, adjust_analysis_order_generic, build_class_dependency_map, build_parent_to_children_map, filter_by_superclass
from persistence.mongoPersistence import MongoPersistence
from bson import json_util

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


def test_activity_filter():
    persistence = MongoPersistence(
        "mongodb://admin:secret@localhost:27017/?authSource=admin", "AppPoet")
    persistence.set_target(
        "f0ce2764655d267d6f322da34c4987753debd2921fd2d7f16d542a5a5e28d06c")
    classInfos = persistence.query({"type": "class_info"})

    parent_map = build_parent_to_children_map(classInfos)
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

    print("Activities:", activity_subclasses)


def test_class_dependency_map():
    persistence = MongoPersistence(
        "mongodb://admin:secret@localhost:27017/?authSource=admin", "AppPoet")
    persistence.set_target(
        "f0ce2764655d267d6f322da34c4987753debd2921fd2d7f16d542a5a5e28d06c")
    classInfos = persistence.query({"type": "class_info"})

    class_dependency_map, method_dependency_map = build_class_dependency_map(
        classInfos, black_filter_patterns)
    pass


def test_analysis_order_complex():
    # 构造复杂的类依赖关系
    class_dependency_map = {
        "ActivityA": ["ServiceA", "UtilsA"],
        "ActivityB": ["ServiceB", "UtilsC"],
        "ServiceA": ["UtilsB", "CoreLib"],
        "ServiceB": ["CoreLib"],
        "UtilsA": [],
        "UtilsB": ["CoreLib"],
        "UtilsC": [],
        "CoreLib": [],
        "Standalone": []  # 没有依赖的独立类
    }

    # 主要分析的类列表
    main_classes = ["ActivityA", "ActivityB", "Standalone"]

    # 调用函数
    ordered = adjust_analysis_order(class_dependency_map, main_classes)
    print("复杂依赖调整后的分析顺序：", ordered)

    # 断言：依赖类应先于被依赖类
    assert ordered.index("CoreLib") < ordered.index(
        "ServiceA"), "CoreLib 应在 ServiceA 之前"
    assert ordered.index("UtilsB") < ordered.index(
        "ServiceA"), "UtilsB 应在 ServiceA 之前"
    assert ordered.index("ServiceA") < ordered.index(
        "ActivityA"), "ServiceA 应在 ActivityA 之前"
    assert ordered.index("UtilsA") < ordered.index(
        "ActivityA"), "UtilsA 应在 ActivityA 之前"
    assert ordered.index("ServiceB") < ordered.index(
        "ActivityB"), "ServiceB 应在 ActivityB 之前"
    assert ordered.index("UtilsC") < ordered.index(
        "ActivityB"), "UtilsC 应在 ActivityB 之前"
    assert "Standalone" in ordered, "Standalone 类应该在结果列表中"

    # 测试循环依赖（函数应该能处理而不无限递归）
    cycle_map = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"]  # 循环依赖
    }
    try:
        ordered_cycle = adjust_analysis_order(cycle_map, ["A"])
        print("循环依赖调整后的分析顺序：", ordered_cycle)
        assert "A" in ordered_cycle, "循环依赖测试结果中应包含 A"
    except RecursionError:
        print("循环依赖导致递归错误！")

    print("所有测试通过！")


def test_adjust_analysis_order_batch():
    class_dependency_map = {
        "ActivityA": ["ServiceA", "UtilsA"],
        "ActivityB": ["ServiceB"],
        "ServiceA": ["UtilsB"],
        "ServiceB": [],
        "UtilsA": ["HelperA"],
        "UtilsB": [],
        "HelperA": []
    }

    main_classes = ["ActivityA", "ActivityB"]
    batches = adjust_analysis_order_batch(class_dependency_map, main_classes)

    print("分批结果：", batches)

    # 每个主要类都必须出现在结果里
    for mc in main_classes:
        assert any(mc in batch for batch in batches), f"{mc} 没有出现在结果里"

    # ActivityA 的依赖必须在它之前
    idx_activityA = next(i for i, b in enumerate(batches) if "ActivityA" in b)
    for dep in ["UtilsA", "ServiceA", "UtilsB", "HelperA"]:
        idx_dep = next(i for i, b in enumerate(batches) if dep in b)
        assert idx_dep < idx_activityA, f"{dep} 应该在 ActivityA 之前"

    # ActivityB 的依赖必须在它之前
    idx_activityB = next(i for i, b in enumerate(batches) if "ActivityB" in b)
    idx_serviceB = next(i for i, b in enumerate(batches) if "ServiceB" in b)
    assert idx_serviceB < idx_activityB, "ServiceB 应该在 ActivityB 之前"

    print("所有断言测试通过！")


def test_adjust_analysis_order_batch_complex():
    class_dependency_map = {
        # 主流程 A -> B -> C -> D
        "ActivityA": ["ServiceA"],
        "ServiceA": ["UtilsA"],
        "UtilsA": ["CoreA"],
        "CoreA": [],

        # 分支依赖
        "ActivityB": ["ServiceB", "HelperB"],
        "ServiceB": ["UtilsB"],
        "HelperB": [],
        "UtilsB": [],

        # 环依赖 X <-> Y
        "X": ["Y"],
        "Y": ["X"],

        # 一个完全独立的类
        "Lonely": []
    }

    main_classes = ["ActivityA", "ActivityB", "X"]

    batches = adjust_analysis_order_batch(class_dependency_map, main_classes)
    print("复杂用例分批结果：", batches)

    # ================== 验证逻辑 ==================
    # main_classes 必须都出现
    for mc in main_classes:
        assert any(mc in batch for batch in batches), f"{mc} 没有出现在结果里"

    # ActivityA 的依赖链必须在它之前
    idx_A = next(i for i, b in enumerate(batches) if "ActivityA" in b)
    for dep in ["ServiceA", "UtilsA", "CoreA"]:
        idx_dep = next(i for i, b in enumerate(batches) if dep in b)
        assert idx_dep < idx_A, f"{dep} 应该在 ActivityA 之前"

    # ActivityB 的依赖必须在它之前
    idx_B = next(i for i, b in enumerate(batches) if "ActivityB" in b)
    for dep in ["ServiceB", "HelperB", "UtilsB"]:
        idx_dep = next(i for i, b in enumerate(batches) if dep in b)
        assert idx_dep < idx_B, f"{dep} 应该在 ActivityB 之前"

    # 环依赖 (X, Y) 必须放在最后一批
    last_batch = batches[-1]
    assert "X" in last_batch and "Y" in last_batch, "X 和 Y 应该在最后一批（环依赖）"

    # Lonely 不在 main_classes 下游，所以不应出现在结果中
    assert all("Lonely" not in batch for batch in batches), "Lonely 不应出现在结果里"

    print("复杂用例测试通过！")


def test_real_example():
    persistence = MongoPersistence(
        "mongodb://admin:secret@localhost:27017/?authSource=admin", "AppPoet")
    persistence.set_target(
        "f0ce2764655d267d6f322da34c4987753debd2921fd2d7f16d542a5a5e28d06c")
    classInfos = persistence.query({"type": "class_info"})

    parent_map = build_parent_to_children_map(classInfos)
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

    class_dependency_map = build_class_dependency_map(
        classInfos, black_filter_patterns)

    batches = adjust_analysis_order_batch(
        class_dependency_map, activity_subclasses + service_subclasses + broadcast_receiver_subclasses + content_provider_subclasses + application_subclasses)

    pass


def test_build_class_dependency_map():
    # 模拟 class_info（取你给的文档结构）
    class_info = [
        {
            "class_name": "LI1/IlIL1丨Il;",
            "superclass_name": "Ljava/lang/Object;",
            "fields": [
                {
                    "field_name": "i1",
                    "field_type": "L丨l丨LLlI丨I/ILl11丨11i$i1;",
                    "access_flags": "public static"
                }
            ],
            "methods": [
                {
                    "method_id": "09dbf0b7-d686-466e-9812-f3b970f3a47b",
                    "name": "<clinit>",
                    "input_params": [],
                    "return_type": "V",
                    "access_flags": "public static constructor",
                    "instructions": [
                        {"opcode": "const-string", "operands": "v0, \"k\""},
                        {"opcode": "filled-new-array",
                            "operands": "v0, [Ljava/lang/String;"},
                        {"opcode": "move-result-object", "operands": "v0"},
                        {"opcode": "invoke-static",
                            "operands": "v0, L丨l丨LLlI丨I/ILl11丨11i$i1;->i1([Ljava/lang/String;)L丨l丨LLlI丨I/ILl11丨11i$i1;"},
                        {"opcode": "move-result-object", "operands": "v0"},
                        {"opcode": "sput-object",
                            "operands": "v0, LI1/IlIL1丨Il;->i1 L丨l丨LLlI丨I/ILl11丨11i$i1;"},
                        {"opcode": "return-void", "operands": ""}
                    ]
                }
            ]
        }
    ]

    # 黑名单（排除 Java / Android 基础类）
    black_filter_patterns = [
        r"^Ljava/.*",
        r"^Landroid/.*"
    ]

    class_map, method_map = build_class_dependency_map(
        class_info, black_filter_patterns)

    print("类依赖：", class_map)
    print("方法依赖：", method_map)

    # ====== 断言测试 ======
    # 类依赖必须包含 "LI1/IlIL1丨Il;" -> "L丨l丨LLlI丨I/ILl11丨11i$i1;"
    assert "LI1/IlIL1丨Il;" in class_map
    assert any(
        "L丨l丨LLlI丨I/ILl11丨11i$i1;" in dep for dep in class_map["LI1/IlIL1丨Il;"])

    # 方法依赖必须包含 <clinit>
    key = "LI1/IlIL1丨Il;-><clinit>"
    assert key in method_map
    assert any("L丨l丨LLlI丨I/ILl11丨11i$i1;" in dep for dep in method_map[key])

    print("测试通过！")


def test_max_len_class():
    persistence = MongoPersistence(
        "mongodb://admin:secret@localhost:27017/?authSource=admin", "AppPoet")
    persistence.set_target(
        "f0ce2764655d267d6f322da34c4987753debd2921fd2d7f16d542a5a5e28d06c")
    classInfos = persistence.query({"type": "class_info"})

    max_len = max(len(json_util.dumps(class_info))
                  for class_info in classInfos)

    pass


def test_pattern(capsys):
    import re

    s1 = "LI1/llI;->ILl11丨11i(L丨l丨LLlI丨I/ILl11丨11i; LiIiLL1ll/III; F LI1/I丨1lI; Z Z)"

    s2 = "Lcom/example/MyClass;"

    # 类名 + 可选方法名 + 可选参数列表
    pattern = re.compile(r"(L[\w/$]+;)(?:->(\w+)\(([^\)]*)\))?")

    m = pattern.match(s1)
    class_name = m.group(1)       # 类名
    method_name = m.group(2)      # 方法名，可为 None
    params = m.group(3)

    assert class_name == "LI1/llI;"
    assert method_name == "ILl11丨11i"
    assert params == "L丨l丨LLlI丨I/ILl11丨11i; LiIiLL1ll/III; F LI1/I丨1lI; Z Z"

    m = pattern.match(s2)
    class_name = m.group(1)       # 类名
    method_name = m.group(2)      # 方法名，可为 None
    params = m.group(3)
    assert class_name == "Lcom/example/MyClass;"
    assert method_name is None
    assert params is None


def test_build_class_dependency_map():
    class_info = [
        {
            "class_name": "Lcom/example/A;",
            "methods": [
                {
                    "name": "foo",
                    "instructions": [
                        {"operands": "Lcom/example/B;->bar()"},
                        {"operands": "Lcom/example/A;->baz(I)"}
                    ]
                },
                {
                    "name": "baz",
                    "instructions": []
                }
            ]
        },
        {
            "class_name": "Lcom/example/B;",
            "methods": [
                {
                    "name": "bar",
                    "instructions": [
                        {"operands": "Lcom/example/C;"}
                    ]
                },
                {
                    "name": "abc",
                    "instructions": [
                        {"operands": "Lcom/example/C;"}
                    ]
                }

            ]
        },
        {
            "class_name": "Lcom/example/C;",
            "methods": []
        },
        {
            "class_name": "Landroid/util/Log;",  # 黑名单类
            "methods": [
                {
                    "name": "d",
                    "instructions": []
                }
            ]
        }
    ]

    black_filter_patterns = [r"Landroid/.*"]  # 黑名单正则

    class_dep, method_dep, method_self_dep = build_class_dependency_map(
        class_info, black_filter_patterns)

    ordered_class_methods_batches = defaultdict(lambda: defaultdict(list))
    for class_item, class_method_item in method_self_dep.items():
        method_batches = adjust_analysis_order_generic(
            class_method_item, None, False)
        ordered_class_methods_batches[class_item] = method_batches
    pass
