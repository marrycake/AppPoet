import logging
from Modules import PScoutMapping as PScoutMapping
from Modules import BasicBlockAttrBuilder as BasicBlockAttrBuilder
import re
from androguard.misc import AnalyzeAPK
import os
import json


def extract_used_permissions(dx):
    used_permissoins = set()
    for _, perm in dx.get_permissions():
        if isinstance(perm, list):
            used_permissoins.update(perm)  # 展开多个权限
        else:
            used_permissoins.add(perm)     # 单个权限
    return list(used_permissoins)


def GetFromManifest(a, d, dx):
    packageName = a.get_package()
    requestedPermissions = a.get_permissions()
    # usedPermissions = extract_used_permissions(dx)
    activitys = a.get_activities()
    services = a.get_services()
    contentProviders = a.get_providers()
    broadcastReceivers = a.get_receivers()
    hardwareComponents = a.get_features()
    intentFilters = {}
    for typ, items in [("activity", activitys), ("service", services), ("receiver", broadcastReceivers)]:
        for name in items:
            filters = a.get_intent_filters(typ, name)
            if filters:
                intentFilters[f"{typ}:{name}"] = filters

    return packageName, requestedPermissions, activitys, services, contentProviders, broadcastReceivers, hardwareComponents, intentFilters


def GetFromInstructions(a, d, dx, PMap, RequestedPermissionList):
    '''
    获取APK文件所需的权限、使用的API和HTTP信息。
    重载版本的GetPermissions。
    :param String ApkDirectoryPath: APK文件目录路径
    :param String ApkFile: APK文件名
    :param PScoutMapping.PScoutMapping PMap: API映射
    :param RequestedPermissionList List([String]): 请求的权限列表
    :return 使用的权限集合, 受限API集合, 可疑API集合, URL域名集合
    :rtype Set([String])
    '''

    UsedPermissions = set()  # 1、使用的权限集合
    RestrictedApiSet = set()  # 2、受限API集合
    SuspiciousApiSet = set()  # 3、可疑API集合
    URLDomainSet = set()  # 4、URL域名集合

    for method in dx.get_methods():
        if method.is_external():
            continue
        for basic_block in method.get_basic_blocks().get():
            # your BasicBlockAttrBuilder logic here
            Instructions = BasicBlockAttrBuilder.GetBasicBlockDalvikCode(
                basic_block)
            apis, SuspiciousApis = BasicBlockAttrBuilder.GetInvokedAndroidApis(
                Instructions)
            Permissions, RestrictedApis = BasicBlockAttrBuilder.GetPermissionsAndApis(
                apis, PMap, RequestedPermissionList)

            UsedPermissions = UsedPermissions.union(Permissions)
            RestrictedApiSet = RestrictedApiSet.union(RestrictedApis)
            SuspiciousApiSet = SuspiciousApiSet.union(SuspiciousApis)
            for Instruction in Instructions:
                URLSearch = re.search(
                    "https?://([\da-z\.-]+\.[a-z\.]{2,6}|[\d.]+)[^'\"]*", Instruction, re.IGNORECASE)
                if URLSearch:
                    URL = URLSearch.group()
                    Domain = re.sub("https?://(.*)", "\g<1>",
                                    re.search("https?://([^/:\\\\]*)", URL, re.IGNORECASE).group(), 0, re.IGNORECASE)
                    URLDomainSet.add(Domain)

    # 得到Drebin论文中描述的集合S6, S5, S7
    return UsedPermissions, RestrictedApiSet, SuspiciousApiSet, URLDomainSet


def extract_apk_methods_via_dx_internal_only(a, d, dx):
    result = []

    for method_analysis in dx.get_methods():
        if method_analysis.is_external():
            # 跳过外部方法
            continue

        m = method_analysis.get_method()
        cls_name = m.get_class_name()

        # 查找该类是否已添加
        existing_class = next(
            (c for c in result if c["class_name"] == cls_name), None)
        if not existing_class:
            existing_class = {
                "class_name": cls_name,
                "methods": []
            }
            result.append(existing_class)

        method_info = {
            "name": m.get_name(),
            "descriptor": m.get_descriptor(),
            "access_flags": m.get_access_flags_string(),
            "instructions": []
        }

        code_obj = m.get_code()
        if code_obj:
            bytecode = code_obj.get_bc()
            for ins in bytecode.get_instructions():
                method_info["instructions"].append({
                    "opcode": ins.get_name(),
                    "operands": ins.get_output()
                })
        else:
            method_info["instructions"] = None  # native or abstract

        existing_class["methods"].append(method_info)

    return result


def ProcessingDataForGetApkData(ApkFile, PMap, outputPath):
    '''
    Produce .data file for a given ApkFile.

    :param String ApkDirectoryPath: absolute path of the ApkFile directory
    :param String ApkFile: absolute path of the ApkFile
    :param PScoutMapping.PScoutMapping() PMap: PMap for API mapping

    :return Tuple(String, Boolean)  ProcessingResult: The processing result, (ApkFile, True/False)
    True means successful. False means unsuccessful.
    '''
    try:
        DataDictionary = {}
        logging.getLogger("androguard").setLevel(logging.INFO)
        a, d, dx = AnalyzeAPK(ApkFile)
        packageName, requestedPermissions,  activitys, services, contentProviders, broadcastReceivers, hardwareComponents, intentFilters = GetFromManifest(
            a, d, dx)

        usedPermissions, restrictedApiSet, suspiciousApiSet, URLDomainSet = GetFromInstructions(
            a, d, dx, PMap, requestedPermissions)

        usedMethods = extract_apk_methods_via_dx_internal_only(a, d, dx)

        DataDictionary["PackageName"] = packageName
        DataDictionary["RequestedPermission"] = requestedPermissions
        DataDictionary["UsedPermission"] = list(usedPermissions)
        DataDictionary["Activitie"] = activitys
        DataDictionary["ServiceList"] = services
        DataDictionary["ContentProviderList"] = contentProviders
        DataDictionary["BroadcastReceiverList"] = broadcastReceivers
        DataDictionary["HardwareComponentsList"] = hardwareComponents
        DataDictionary["IntentFilterList"] = intentFilters
        # Got Set S2 and others
        DataDictionary["UsedMethods"] = usedMethods

        DataDictionary["RestrictedAPIs"] = list(restrictedApiSet)
        DataDictionary["SuspiciousAPIs"] = list(suspiciousApiSet)
        DataDictionary["URL"] = list(URLDomainSet)
        # Set S6, S5, S7, S8

        with open(outputPath, 'w', encoding='utf-8') as f:
            json.dump(DataDictionary, f, indent=4)

        return True

    except Exception as e:
        print(e)
        return False


def GetApkData(ApkPath, outputPath):
    '''
    Get Apk data dictionary for all Apk files under ApkDirectoryPath and store them in ApkDirectoryPath
    Used for next step's classification

    :param Tuple<string> *ApkDirectoryPaths: absolute path of the directories contained Apk files
    '''
    # Because some apk files may not have extension....
    # CWD = os.getcwd()
    # os.chdir(os.path.join(CWD, "Modules"))
    # ''' Change current working directory to import the mapping '''
    PMap = PScoutMapping.PScoutMapping()
    # os.chdir(CWD)

    return ProcessingDataForGetApkData(ApkPath, PMap, outputPath)
