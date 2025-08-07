# coding:utf-8
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


# -> tuple[set, set, set, set]:
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


def extract_features(apk_path):
    try:
        a, d, dx = AnalyzeAPK(apk_path)

        # 提取在manifest中声明的权限
        requested_permissions = a.get_permissions()
        # 提取实际使用的权限
        used_permissions = extract_used_permissions(dx)
        # 提取活动
        activities = a.get_activities()

        # 提取服务
        services = a.get_services()
        # 提取接收器
        receivers = a.get_receivers()
        # 提取提供者
        providers = a.get_providers()

        # 判断 APK 是否有效
        valid = a.is_valid_APK()
        # 获取 APK 文件名，只保留文件名称部分
        filename = os.path.basename(a.get_filename())
        a.get_intent_filters()
        # 获取 APP 名
        appname = a.get_app_name()
        # 获取 package 名
        package = a.get_package()
        # 获取 android 版本名
        version = a.get_androidversion_code()
        # 获取 APK 文件列表
        filelist = a.get_files()

        CWD = os.getcwd()
        os.chdir(os.path.join(CWD, "Modules"))
        ''' Change current working directory to import the mapping '''
        PMap = PScoutMapping.PScoutMapping()
        os.chdir(CWD)
        # 提取 restricted API 和 suspicious API
        _, RestrictedApiSet, SuspiciousApiSet, URLDomainSet = GetFromInstructions(
            a, d, dx, PMap, requested_permissions)

        features = {
            "File": filename,
            "Requested Permissions": requested_permissions,
            "Used Permissions": used_permissions,
            "Activities": activities,
            "Services": services,
            "Receivers": receivers,
            "Providers": providers,
            "Valid": valid,
            "Filename": filename,
            "Appname": appname,
            "Package": package,
            "Version": version,
            "Filelist": filelist,
            # "API_calls": list(api_calls)
            "Restricted APIs": list(RestrictedApiSet),
            "Suspicious APIs": list(SuspiciousApiSet),
            "Url": list(URLDomainSet)
        }

        return features

    except Exception as e:
        print(f"Error processing {apk_path}: {e}")
        return None


def main():
    apk_folder = "datasets/folder"
    output_file = "apk_many_features.json"

    all_features = []

    for root, dirs, files in os.walk(apk_folder):
        for file in files:
            if file.endswith(".apk"):
                apk_path = os.path.join(root, file)
                features = extract_features(apk_path)
                if features:
                    all_features.append(features)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_features, f, indent=4)

    print("APK features have been saved to:", output_file)


if __name__ == '__main__':
    main()
