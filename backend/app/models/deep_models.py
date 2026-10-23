"""
CryptoScope Deep Learning Models (PyTorch)
Paper Section III-E:
- 1D CNN over instruction-class sequences
- Bidirectional LSTM (Bi-LSTM) over tokenized sequences
- Transformer Encoder with Positional Encoding and Multi-Head Self-Attention
Fully CPU-compatible (GPU optional), wrapped with scikit-learn compatible fit/predict/predict_proba API.
"""

import math
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

# Map 14 semantic classes + padding to vocabulary integers
VOCAB_SIZE = 16
PAD_TOKEN = 0

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 512):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: [batch_size, seq_len, d_model]
        return x + self.pe[:, :x.size(1)]

class CNN1DNetwork(nn.Module):
    def __init__(self, num_classes: int, d_model: int = 64):
        super().__init__()
        self.embedding = nn.Embedding(VOCAB_SIZE, d_model, padding_idx=PAD_TOKEN)
        self.conv1 = nn.Conv1d(d_model, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=5, padding=2)
        self.relu = nn.ReLU()
        self.pool = nn.AdaptiveMaxPool1d(1)
        self.fc = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, seq_len]
        emb = self.embedding(x).transpose(1, 2) # [batch, d_model, seq_len]
        c1 = self.relu(self.conv1(emb))
        c2 = self.relu(self.conv2(c1))
        pooled = self.pool(c2).squeeze(2) # [batch, 128]
        logits = self.fc(pooled)
        return logits

class BiLSTMNetwork(nn.Module):
    def __init__(self, num_classes: int, d_model: int = 64, hidden_dim: int = 64):
        super().__init__()
        self.embedding = nn.Embedding(VOCAB_SIZE, d_model, padding_idx=PAD_TOKEN)
        self.lstm = nn.LSTM(d_model, hidden_dim, num_layers=2, bidirectional=True, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        emb = self.embedding(x)
        out, (hn, _) = self.lstm(emb)
        # Concatenate forward and backward last hidden states
        h_last = torch.cat((hn[-2, :, :], hn[-1, :, :]), dim=1)
        return self.fc(h_last)

class TransformerNetwork(nn.Module):
    def __init__(self, num_classes: int, d_model: int = 64, nhead: int = 4, num_layers: int = 2):
        super().__init__()
        self.embedding = nn.Embedding(VOCAB_SIZE, d_model, padding_idx=PAD_TOKEN)
        self.pos_encoder = PositionalEncoding(d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dim_feedforward=128, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        mask = (x == PAD_TOKEN)
        emb = self.embedding(x)
        emb = self.pos_encoder(emb)
        encoded = self.transformer_encoder(emb, src_key_padding_mask=mask)
        # Global average pooling over non-padding tokens
        mask_expanded = (~mask).unsqueeze(-1).float()
        sum_pooled = (encoded * mask_expanded).sum(dim=1)
        lens = mask_expanded.sum(dim=1).clamp(min=1.0)
        pooled = sum_pooled / lens
        return self.fc(pooled)


class PyTorchClassifierWrapper:
    """
    Scikit-learn compatible wrapper for CNN, LSTM, and Transformer models.
    """
    def __init__(self, model_type: str = "cnn", num_classes: int = 2, max_seq_len: int = 64, epochs: int = 8, batch_size: int = 32, lr: float = 0.003):
        self.model_type = model_type.lower()
        self.num_classes = num_classes
        self.max_seq_len = max_seq_len
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.classes_ = np.arange(num_classes)
        self.network = self._create_network()

    def _create_network(self) -> nn.Module:
        if self.model_type in ["cnn", "cnn1d"]:
            net = CNN1DNetwork(self.num_classes)
        elif self.model_type in ["lstm", "bilstm"]:
            net = BiLSTMNetwork(self.num_classes)
        elif self.model_type in ["transformer"]:
            net = TransformerNetwork(self.num_classes)
        else:
            net = CNN1DNetwork(self.num_classes)
        return net.to(self.device)

    def _prepare_sequences(self, X: np.ndarray) -> torch.Tensor:
        """
        Converts feature vector or token sequence into bounded integer tensor for neural net.
        """
        # If 2D feature matrix, discretize features into token indices 1..15
        if X.ndim == 2:
            norm_X = np.nan_to_num(X)
            # Map features into discrete pseudo-tokens
            tokens = np.clip((np.abs(norm_X * 10)).astype(int) % (VOCAB_SIZE - 1) + 1, 1, VOCAB_SIZE - 1)
            # Pad or truncate to max_seq_len
            if tokens.shape[1] < self.max_seq_len:
                pad_width = ((0, 0), (0, self.max_seq_len - tokens.shape[1]))
                tokens = np.pad(tokens, pad_width, mode="constant", constant_values=PAD_TOKEN)
            else:
                tokens = tokens[:, :self.max_seq_len]
            return torch.tensor(tokens, dtype=torch.long)
        else:
            return torch.tensor(X, dtype=torch.long)

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.classes_ = np.unique(y)
        self.num_classes = len(self.classes_)
        self.network = self._create_network()

        # Map y to 0..num_classes-1
        label_to_idx = {cls: idx for idx, cls in enumerate(self.classes_)}
        y_indices = np.array([label_to_idx[val] for val in y], dtype=np.int64)

        X_t = self._prepare_sequences(X)
        y_t = torch.tensor(y_indices, dtype=torch.long)

        dataset = TensorDataset(X_t, y_t)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(self.network.parameters(), lr=self.lr, weight_decay=1e-4)

        self.network.train()
        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                optimizer.zero_grad()
                outputs = self.network(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()

        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self.network.eval()
        X_t = self._prepare_sequences(X).to(self.device)
        with torch.no_grad():
            logits = self.network(X_t)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        return probs

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        pred_indices = np.argmax(probs, axis=1)
        return self.classes_[pred_indices]
