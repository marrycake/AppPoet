# Load model directly
import json
from transformers import AutoTokenizer, AutoModel
import torch

tokenizer = AutoTokenizer.from_pretrained(
    "/home/rosen/workspace/agent/AppPoet/bge-large-en")
model = AutoModel.from_pretrained(
    "/home/rosen/workspace/agent/AppPoet/bge-large-en")


def encode_text(text):
    # 1. Tokenize 输入
    inputs = tokenizer(text, return_tensors="pt",
                       padding=True, truncation=True)

    # 2. 送入模型，获得输出
    with torch.no_grad():
        outputs = model(**inputs)

    # 3. outputs.last_hidden_state shape: (batch_size, seq_len, hidden_size)
    # 取平均池化（mean pooling）作为句向量
    embeddings = outputs.last_hidden_state.mean(
        dim=1)  # (batch_size, hidden_size)

    return embeddings


def encode_views_summary(feature_views, summary):

    permission_view = {
        "Permission View": feature_views.get("Permission View", {})}

    api_view = {"API View": feature_views.get("API View", {})}
    url_feature_view = {
        "URL & uses-feature View": feature_views.get("URL & uses-feature View", {})}

    summary_view = {"Summary View": summary}

    permission_tokens = encode_text(json.dumps(permission_view))
    api_tokens = encode_text(json.dumps(api_view))
    url_feature_tokens = encode_text(json.dumps(url_feature_view))
    summary_tokens = encode_text(json.dumps(summary_view))

    return torch.cat(
        [permission_tokens, api_tokens, url_feature_tokens, summary_tokens],
        dim=-1
    )
