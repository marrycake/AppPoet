import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import torch
from GetApkData import GetApkData
from LLM.LLMAsyncGen import LLMAsyncGen
from LLM.deepseekAsyncGen import DeepseekAsyncGen
from LLM.ollamaGen import OllamaGen
from classification.MLPClassification import MLPClassifier
from descriptioniGen import asyncDescriptGen, descriptGen
from logger import Logger
from memory import Memory
from persistence.mongoPersistence import MongoPersistence
from tokenizer import encode_views_summary
import torch
from sklearn.preprocessing import LabelEncoder
import pandas as pd
from dbHandler.mongoDBHandler import MongoDBHandler
from persistence.persistence import Persistence

NUM_WORKERS = 32  # 根据你的 CPU 核心数调整
# llmGen = OllamaGen("gpt-oss:latest", "http://localhost:11434")
llmGen = DeepseekAsyncGen(api_key="sk-9ede8c842c0a4588879be08bda35abde",
                          base_url="https://api.deepseek.com/v1")
mongoDBHandler = MongoDBHandler()
memory = Memory("localhost", 6379, "123456")
persistence = MongoPersistence(
    "mongodb://admin:secret@localhost:27017/?authSource=admin", "AppPoet")


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


def process_single_file(i, file_name, family, folder, feature_folder, memory: Memory, llmGen: LLMAsyncGen):
    file_path = os.path.join(folder, file_name)
    features_output_path = os.path.join(
        feature_folder, file_name + "_features.json")

    if not GetApkData(file_path, features_output_path):
        return None

    if not os.path.exists(features_output_path):
        return None  # 文件不存在则跳过

    try:
        feature_views = descriptGen(features_output_path, memory, llmGen)
        Logger.debug(
            f"<feature_views>: {json.dumps(feature_views)}")
        summary_views = json.loads(
            llmGen.generate_summary(json.dumps(feature_views)))
        Logger.debug(
            f"<summary_views>: {json.dumps(summary_views)}")
        combine_tokens = encode_views_summary(feature_views, summary_views)
        return combine_tokens.numpy(), family

    except Exception as e:
        print(f"[!] Error processing {file_name}: {e}")
        return None


def process_single_file_more_info(i, file_name, family, folder, feature_folder, memory: Memory, llmGen: LLMAsyncGen):
    file_path = os.path.join(folder, file_name)
    features_output_path = os.path.join(
        feature_folder, file_name + "_features.json")
    if not persistence.set_target(file_name):
        if not GetApkData(file_path, persistence):
            return None

    feature_views = asyncio.run(asyncDescriptGen(
        persistence, memory, llmGen))
    json.dump(feature_views, open(
        f"./{file_name}_feature_views.json", "w"))
    summary_views = json.loads(
        asyncio.run(llmGen.generate_summary(json.dumps(feature_views))))
    combine_tokens = encode_views_summary(feature_views, summary_views)
    return combine_tokens.numpy(), family, feature_views, summary_views


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
    folder = "./datasets"
    feature_folder = "./features"
    sha256_list, familys = data_process()

    # i = random.randint(0, len(sha256_list) - 1)
    # file_name = sha256_list[i]

    # file_name = "f0ce2764655d267d6f322da34c4987753debd2921fd2d7f16d542a5a5e28d06c"
    file_name = "e07c72efa6141e4c6c5f426105919b3813aa63cbd4ca5f359874d61dac76955d"
    family = familys[0]
    combine_tokens, family, feature_views, summary_views = process_single_file_more_info(
        0, file_name, family, folder, feature_folder, memory, llmGen)

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

    print(llmGen.generate_diagnostic(json.dumps(feature_views),
          le.inverse_transform([family_code])[0]))
    print(family)
    print(summary_views)
    print(feature_views)


if __name__ == "__main__":
    # main()
    diagnostic_test()

    # process_single_file(0, "fded1ec2d17f957b230feb5fff518ec98322a1617e4e28953ff38270cb16098a", "example_family", "./datasets",
    #                     "./features", Memory("localhost", 6379, "123456"))
