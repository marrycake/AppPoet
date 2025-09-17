import logging
import uuid
from Modules import PScoutMapping as PScoutMapping
from Modules import BasicBlockAttrBuilder as BasicBlockAttrBuilder
import re
from androguard.misc import AnalyzeAPK
from logger import Logger
from utils.textProcessing import getFileBaseName, parse_descriptor

from persistence.persistence import Persistence


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


def extract_class_info(a, d, dx):
    class_infos = []
    for dex_index, dex_file in enumerate(d):
        for class_def in dex_file.get_classes():
            class_name = class_def.get_name()
            superclass_name = class_def.get_superclassname()
            class_id = str(uuid.uuid4())
            class_info = {
                "type": "class_info",
                "class_id": class_id,
                "dex_index": dex_index,
                "class_name": class_name,
                "superclass_name": superclass_name,
                "fields": [],
                "methods": []
            }

            # 提取字段
            for field in class_def.get_fields():
                class_info["fields"].append({
                    "field_name": field.get_name(),
                    "field_type": field.get_descriptor(),
                    "access_flags": field.get_access_flags_string()
                })

            for method in class_def.get_methods():
                params, return_type = parse_descriptor(method.get_descriptor())
                method_id = str(uuid.uuid4())
                method_info = {
                    "method_id": method_id,
                    "name": method.get_name(),
                    "input_params": params,
                    "return_type": return_type,
                    "access_flags": method.get_access_flags_string(),
                    "instructions": []
                }
                code_obj = method.get_code()
                if code_obj:
                    bytecode = code_obj.get_bc()
                    for ins in bytecode.get_instructions():
                        method_info["instructions"].append({
                            "opcode": ins.get_name(),
                            "operands": ins.get_output()
                        })
                class_info["methods"].append(method_info)
            class_infos.append(class_info)
    return class_infos


def ProcessingDataForGetApkData(ApkFile, PMap, persistence: Persistence):
    '''
    Produce .data file for a given ApkFile.

    :param String ApkDirectoryPath: absolute path of the ApkFile directory
    :param String ApkFile: absolute path of the ApkFile
    :param PScoutMapping.PScoutMapping() PMap: PMap for API mapping

    :return Tuple(String, Boolean)  ProcessingResult: The processing result, (ApkFile, True/False)
    True means successful. False means unsuccessful.
    '''
    try:
        a, d, dx = AnalyzeAPK(ApkFile)
        packageName, requestedPermissions,  activitys, services, contentProviders, broadcastReceivers, hardwareComponents, intentFilters = GetFromManifest(
            a, d, dx)

        usedPermissions, restrictedApiSet, suspiciousApiSet, URLDomainSet = GetFromInstructions(
            a, d, dx, PMap, requestedPermissions)

        class_infos = extract_class_info(a, d, dx)

        app_id = str(uuid.uuid4())

        appInfo = {
            "app_id": app_id,
            "type": "app_info",
            "package_name": packageName,
            "app_name": a.get_app_name(),
            "version": 1.0,
            "sha256": 123,
            "md5": 123,
            "requested_permissions": requestedPermissions,
            "used_permissions": list(usedPermissions),
            "activitys": activitys,
            "services": services,
            "content_providers": contentProviders,
            "broadcast_receivers": broadcastReceivers,
            "hardware_components": hardwareComponents,
            "restricted_apis": list(restrictedApiSet),
            "suspicious_apis": list(suspiciousApiSet),
            "urls": list(URLDomainSet),
        }
        persistence.insert(appInfo)

        for class_info in class_infos:
            class_info = {
                "app_id": app_id,
                **class_info
            }
            persistence.insert(class_info)

        persistence.save()
        return True

    except Exception as e:
        Logger.error(f"Error processing {ApkFile}: {e}")
        return False


def GetApkData(ApkPath, persistence: Persistence):
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

    return ProcessingDataForGetApkData(ApkPath, PMap, persistence)
