import json
import os

from sklearn.model_selection import train_test_split
import torch
from GetApkData import GetApkData
from classification.MLPClassification import MLPClassifier
from logger import Logger
from descriptioniGen import descriptGen
from memory import Memory
from LLMSummary import get_deepseek_summary
from tokenizer import encode_views_summary
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, cohen_kappa_score, balanced_accuracy_score,
    matthews_corrcoef, classification_report
)
import joblib


def release_gpu():
    torch.cuda.empty_cache()    # 清理未使用的显存缓存
    torch.cuda.synchronize()    # 等待所有 CUDA 任务完成
    # 如果用到显式变量，可以手动删除并调用 gc
    import gc
    gc.collect()


def evaluate_metrics(y_true, y_pred, labels=None):
    print("Accuracy:", accuracy_score(y_true, y_pred))

    print("Precision (macro):", precision_score(
        y_true, y_pred, average='macro', zero_division=0))
    print("Precision (micro):", precision_score(
        y_true, y_pred, average='micro', zero_division=0))
    print("Precision (weighted):", precision_score(
        y_true, y_pred, average='weighted', zero_division=0))

    print("Recall (macro):", recall_score(
        y_true, y_pred, average='macro', zero_division=0))
    print("Recall (micro):", recall_score(
        y_true, y_pred, average='micro', zero_division=0))
    print("Recall (weighted):", recall_score(
        y_true, y_pred, average='weighted', zero_division=0))

    print("F1-score (macro):", f1_score(y_true,
          y_pred, average='macro', zero_division=0))
    print("F1-score (micro):", f1_score(y_true,
          y_pred, average='micro', zero_division=0))
    print("F1-score (weighted):", f1_score(y_true,
          y_pred, average='weighted', zero_division=0))

    print("Balanced Accuracy:", balanced_accuracy_score(y_true, y_pred))
    print("Cohen's Kappa:", cohen_kappa_score(y_true, y_pred))
    print("Matthews Correlation Coefficient:",
          matthews_corrcoef(y_true, y_pred))

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print(cm)

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))


def main():

    embeddings = torch.load("all_embeddings.pt", weights_only=False)
    families = torch.load("all_families.pt", weights_only=False)

    X = torch.stack([torch.tensor(x).view(-1)
                    for x in embeddings])  # shape: (N, D)

    le = LabelEncoder()

    y_encoded = le.fit_transform(families)
    joblib.dump(le, "label_encoder.pkl")
    # y_encoded 是 numpy array，可以转成 tensor：
    y = torch.tensor(y_encoded, dtype=torch.long)

    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    # 创建模型
    module = MLPClassifier(
        input_dim=4096, hidden_dim=512, num_classes=len(set(y)))

    # 训练模型
    module.train(X_train, y_train, epochs=500)

    # 保存模型
    module.save("mlp_classifier.pth")

    # 测试模型性能
    # module = MLPClassifier(
    #     input_dim=4096, hidden_dim=512, num_classes=len(set(y)))
    module.load("mlp_classifier.pth")
    module.model.eval()
    with torch.no_grad():
        logits = module.model(X_test.to(module.device))
        preds = torch.argmax(logits, dim=1).cpu()

    evaluate_metrics(y_test.cpu().numpy(), preds.cpu().numpy())
    release_gpu()


if __name__ == "__main__":
    main()
