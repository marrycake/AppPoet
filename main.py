import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import torch
from GetApkData import GetApkData
from LLMDiagnostic import get_deepseek_diagnostic
from classification.MLPClassification import MLPClassifier
from descriptioniGen import descriptGen
from memory import Memory
from LLMSummary import get_deepseek_summary
from tokenizer import encode_views_summary
import torch
from sklearn.preprocessing import LabelEncoder
import pandas as pd

NUM_WORKERS = 32  # 根据你的 CPU 核心数调整


def release_gpu():
    torch.cuda.empty_cache()    # 清理未使用的显存缓存
    torch.cuda.synchronize()    # 等待所有 CUDA 任务完成
    # 如果用到显式变量，可以手动删除并调用 gc
    import gc
    gc.collect()


def data_process():
    train_df = pd.read_csv("./datasets/Derbin-20Dataset-20Hashes.csv")
    sha256 = train_df['sha256'].values
    family = train_df['family'].values

    return sha256, family


def process_single_file(i, file_name, family, folder, feature_folder, memory):
    file_path = os.path.join(folder, file_name)
    features_output_path = os.path.join(
        feature_folder, file_name + "_features.json")

    if not GetApkData(file_path, features_output_path):
        return None

    if not os.path.exists(features_output_path):
        return None  # 文件不存在则跳过

    try:
        feature_views = descriptGen(features_output_path, memory)
        summary_views = json.loads(
            get_deepseek_summary(json.dumps(feature_views)))
        combine_tokens = encode_views_summary(feature_views, summary_views)
        return combine_tokens.numpy(), family

    except Exception as e:
        print(f"[!] Error processing {file_name}: {e}")
        return None


def process_single_file_more_info(i, file_name, family, folder, feature_folder, memory):
    file_path = os.path.join(folder, file_name)
    features_output_path = os.path.join(
        feature_folder, file_name + "_features.json")

    if not GetApkData(file_path, features_output_path):
        return None

    if not os.path.exists(features_output_path):
        return None  # 文件不存在则跳过

    try:
        feature_views = descriptGen(features_output_path, memory)
        summary_views = json.loads(
            get_deepseek_summary(json.dumps(feature_views)))
        combine_tokens = encode_views_summary(feature_views, summary_views)
        return combine_tokens.numpy(), family, feature_views, summary_views
    except Exception as e:
        print(f"[!] Error processing {file_name}: {e}")
        return None


def main():
    memory = Memory("localhost", 6379, "123456")
    folder = "./datasets"
    feature_folder = "./features"
    sha256_list, familys = data_process()

    all_embeddings = []
    all_families = []

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = []
        for i in range(len(sha256_list)):
            file_name = sha256_list[i]
            family = familys[i]
            futures.append(executor.submit(
                process_single_file, i, file_name, family, folder, feature_folder, memory))

        for future in as_completed(futures):
            result = future.result()
            if result:
                emb, fam = result
                all_embeddings.append(emb)
                all_families.append(fam)

    torch.save(all_embeddings, "all_embeddings.pt")
    torch.save(all_families, "all_families.pt")


def diagnostic_test():
    memory = Memory("localhost", 6379, "123456")
    folder = "./datasets"
    feature_folder = "./features"
    sha256_list, familys = data_process()

    i = random.randint(0, len(sha256_list) - 1)
    file_name = sha256_list[i]
    family = familys[i]
    combine_tokens, family, feature_views, summary_views = process_single_file_more_info(
        i, file_name, family, folder, feature_folder, memory)

    families = torch.load("all_families.pt", weights_only=False)

    le = LabelEncoder()
    y_encoded = le.fit_transform(families)
    y = torch.tensor(y_encoded, dtype=torch.long)

    # 创建模型
    module = MLPClassifier(
        input_dim=4096, hidden_dim=512, num_classes=len(set(y)))

    module.load("mlp_classifier.pth")
    family_code = module.predict(torch.tensor(
        combine_tokens, dtype=torch.float32)).cpu().item()

    release_gpu()

    print(get_deepseek_diagnostic(json.dumps(feature_views),
          le.inverse_transform([family_code])[0]))
    print(family)
    print(summary_views)
    print(feature_views)


if __name__ == "__main__":
    # main()
    diagnostic_test()
