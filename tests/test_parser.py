
import sys
import os
from utils.textProcessing import parse_descriptor


def test_none_method():
    descriptor = "()V"
    params, ret = parse_descriptor(descriptor)
    assert params == []
    assert ret == "V"


def test_simple_method():
    descriptor = "(Ldfjg6/Gtr6H/B66gGh; J)V"
    params, ret = parse_descriptor(descriptor)
    assert params == ["Ldfjg6/Gtr6H/B66gGh", "J"]
    assert ret == "V"


def test_basic_types():
    descriptor = "(IZBC)I"
    params, ret = parse_descriptor(descriptor)
    assert params == ["I", "Z", "B", "C"]
    assert ret == "I"


def test_object_types():
    descriptor = "(Ljava/lang/String;Ljava/util/Map;)Z"
    params, ret = parse_descriptor(descriptor)
    assert params == ["Ljava/lang/String", "Ljava/util/Map"]
    assert ret == "Z"


def test_array_types():
    descriptor = "([I[[Ljava/lang/String; Landroid/content/Context; Ljava/lang/String; Ljava/lang/String; Z)V"
    params, ret = parse_descriptor(descriptor)
    assert params == ["[I", "[[Ljava/lang/String", "Landroid/content/Context",
                      "Ljava/lang/String", "Ljava/lang/String", "Z"]
    assert ret == "V"


def test_with_spaces():
    descriptor = "(Ljava/lang/String; [Ljava/util/List;)V"
    params, ret = parse_descriptor(descriptor)
    assert params == ["Ljava/lang/String", "[Ljava/util/List"]
    assert ret == "V"
