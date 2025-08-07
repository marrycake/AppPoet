import torch.nn as nn
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader


class MLPClassifier(nn.Module):
    def __init__(self, input_dim=4096, hidden_dim=512, num_classes=3, device=None, lr=0.001):

        super().__init__()

        self.device = device if device else torch.device(
            "cuda" if torch.cuda.is_available() else "cpu")
        self.model = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_classes)
        ).to(self.device)

        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)

    def forward(self, x):
        return self.model(x)

    def train(self, X: torch.Tensor, y: torch.Tensor, epochs=10, batch_size=64, shuffle=True):
        """
        训练模型
        Args:
            X (torch.Tensor): 输入特征，shape: [N, input_dim]
            y (torch.Tensor): 标签，shape: [N]
            epochs (int): 训练轮数
            batch_size (int): 批大小
            shuffle (bool): 是否打乱数据
        """
        dataset = TensorDataset(X, y)
        dataloader = DataLoader(
            dataset, batch_size=batch_size, shuffle=shuffle)

        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for xb, yb in dataloader:
                xb, yb = xb.to(self.device), yb.to(self.device)

                self.optimizer.zero_grad()
                output = self.model(xb)
                loss = self.criterion(output, yb)
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)
            print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")

    def predict(self, X: torch.Tensor):
        """
        预测类别
        Args:
            X (torch.Tensor): 输入特征，shape: [N, input_dim]
        Returns:
            torch.Tensor: 预测类别索引，shape: [N]
        """
        self.model.eval()
        X = X.to(self.device)
        with torch.no_grad():
            logits = self.model(X)
            predicted = torch.argmax(logits, dim=1)
        return predicted

    def save(self, path):
        """保存模型参数"""
        torch.save(self.model.state_dict(), path)

    def load(self, path):
        """加载模型参数"""
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
