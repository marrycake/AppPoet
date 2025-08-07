import hashlib
import json

from LMMDescriptionGen import get_deepseek_response
from logger import Logger


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


def addDescription(featureList, featureType, memory
                   ):
    featureDict = {}
    for feature in featureList:
        if not memory.hexists(featureType, feature):
            description = get_deepseek_response(featureType, feature)
            memory.hset(featureType, feature, description)
            Logger.debug(
                f"\033[31mdescription for LLM\033[0m {featureType}: {feature} -> {description}"
            )
        else:
            description = memory.hget(featureType, feature)
            Logger.debug(
                f"description for CACHE {featureType}: {feature} -> {description}")
        featureDict[feature] = description
    return featureDict


def addSingleDescription(feature, featureType, memory):
    if not memory.hexists(featureType, feature):
        description = get_deepseek_response(featureType, feature)
        memory.hset(featureType, feature, description)
        Logger.debug(
            f"\033[31mdescription for LLM\033[0m {featureType}: {feature} -> {description}"
        )
    else:
        description = memory.hget(featureType, feature)
        Logger.debug(
            f"description for CACHE {featureType}: {feature} -> {description}")
    return description


def addSingleDescriptionToUnstructuredString(feature, featureType, memory):
    featureHash = hashlib.sha256(feature.encode()).hexdigest()
    if not memory.hexists(featureType, featureHash):
        description = get_deepseek_response(featureType, feature)
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


def descriptGen(file_path, memory, outputPath):
    jsonView = descriptGen(file_path, memory)

    with open(outputPath, 'w', encoding='utf-8') as f:
        json.dump(jsonView, f, indent=4)


def descriptGen(file_path, memory) -> str:
    RequestedPermission, UsedPermission, RestrictedAPIs, SuspiciousAPIs, HardwareComponentsList, URLDomains, classFeatures = parseApkFeatures(
        file_path)

    requestedPermissionFeatureDict = addDescription(
        RequestedPermission, "permission", memory)
    usedPermissionFeatureDict = addDescription(
        UsedPermission, "permission", memory)
    restrictedAPIFeatureDict = addDescription(
        RestrictedAPIs, "API", memory)
    suspiciousAPIFeatureDict = addDescription(
        SuspiciousAPIs, "API", memory)
    hardwareComponentsFeatureDict = addDescription(
        HardwareComponentsList, "uses-feature", memory)
    urlDomainFeatureDict = addDescription(URLDomains, "URL", memory)
    classFeatureDict = {}
    for classFeature in classFeatures:
        methodDict = {}
        className = classFeature["class_name"]
        classMethods = classFeature["methods"]
        for classMethod in classMethods:
            methodFullName = f"{classMethod["private constructor"]} {classMethod["name"]} {classMethod["descriptor"]}"
            methodDescription = addSingleDescriptionToUnstructuredString(
                classMethod, "Method", memory)
            methodDict[methodFullName] = methodDescription
        classFeatureDict[className] = methodDict

    return createView(requestedPermissionFeatureDict, usedPermissionFeatureDict,
                      restrictedAPIFeatureDict, suspiciousAPIFeatureDict,
                      hardwareComponentsFeatureDict, urlDomainFeatureDict, classFeatureDict)
