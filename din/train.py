"""
DIN 模型训练脚本
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
import pickle
import os
from din_model import DINModel, save_model

DATA_DIR = "D:/YueQian/din/data"
MODEL_DIR = "D:/YueQian/din"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 超参数
BATCH_SIZE = 256
EPOCHS = 5
LR = 0.001
WEIGHT_DECAY = 1e-5

print(f"设备: {DEVICE}")
print("=" * 60)

# ============================================================
# 1. 加载数据
# ============================================================
print("\n[1/4] 加载预处理数据...")
with open(os.path.join(DATA_DIR, 'train.pkl'), 'rb') as f:
    train_data = pickle.load(f)
with open(os.path.join(DATA_DIR, 'val.pkl'), 'rb') as f:
    val_data = pickle.load(f)
with open(os.path.join(DATA_DIR, 'encoder.pkl'), 'rb') as f:
    encoder = pickle.load(f)

print(f"  训练集: {len(train_data['labels']):,} 样本 (正: {int(train_data['labels'].sum())})")
print(f"  验证集: {len(val_data['labels']):,} 样本 (正: {int(val_data['labels'].sum())})")
print(f"  Item词表: {encoder['num_items']:,}, Cat词表: {encoder['num_cats']:,}")

# ============================================================
# 2. Dataset
# ============================================================
class RecDataset(Dataset):
    def __init__(self, data):
        self.seq_items = torch.LongTensor(data['seq_items'])
        self.seq_cats = torch.LongTensor(data['seq_cats'])
        self.seq_mask = torch.FloatTensor(data['seq_mask'])
        self.target_item = torch.LongTensor(data['target_item'])
        self.target_cat = torch.LongTensor(data['target_cat'])
        self.labels = torch.FloatTensor(data['labels'])

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return (self.seq_items[idx], self.seq_cats[idx], self.seq_mask[idx],
                self.target_item[idx], self.target_cat[idx], self.labels[idx])

train_dataset = RecDataset(train_data)
val_dataset = RecDataset(val_data)
# 调整 batch_size 如果数据量很少
actual_batch = min(BATCH_SIZE, len(train_dataset) // 4)
train_loader = DataLoader(train_dataset, batch_size=actual_batch, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=actual_batch * 2, shuffle=False)
print(f"\n[2/4] DataLoader 就绪: batch_size={actual_batch}")

# ============================================================
# 3. 模型
# ============================================================
print("\n[3/4] 构建 DIN 模型...")
model = DINModel(
    num_items=encoder['num_items'],
    num_cats=encoder['num_cats'],
    item_emb_dim=128,
    cat_emb_dim=32,
    max_seq_len=encoder['max_seq_len'],
    dropout=0.2,
).to(DEVICE)

print(f"  参数量: {sum(p.numel() for p in model.parameters()):,}")

# 损失函数 & 优化器
# 用加权 BCE 处理正负样本不均衡
pos_weight = torch.tensor([(len(train_dataset) - train_data['labels'].sum()) / max(1, train_data['labels'].sum())]).to(DEVICE)
criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=2, gamma=0.5)

# ============================================================
# 4. 训练循环
# ============================================================
print("\n[4/4] 开始训练...")
print("=" * 60)

for epoch in range(EPOCHS):
    # ---- Train ----
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for batch in train_loader:
        seq_i, seq_c, seq_m, t_i, t_c, labels = [b.to(DEVICE) for b in batch]

        optimizer.zero_grad()
        logits = model(seq_i, seq_c, seq_m, t_i, t_c)  # raw logits
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * len(labels)
        preds = (torch.sigmoid(logits) > 0.5).float()
        correct += (preds == labels).sum().item()
        total += len(labels)

    scheduler.step()
    train_acc = correct / max(1, total)
    avg_loss = total_loss / max(1, total)

    # ---- Validation ----
    model.eval()
    val_loss = 0
    val_correct = 0
    val_total = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in val_loader:
            seq_i, seq_c, seq_m, t_i, t_c, labels = [b.to(DEVICE) for b in batch]
            logits = model(seq_i, seq_c, seq_m, t_i, t_c)  # raw logits
            loss = criterion(logits, labels)
            val_loss += loss.item() * len(labels)
            preds = (torch.sigmoid(logits) > 0.5).float()
            val_correct += (preds == labels).sum().item()
            val_total += len(labels)
            all_preds.extend(preds.cpu().numpy().tolist())
            all_labels.extend(labels.cpu().numpy().tolist())

    val_acc = val_correct / max(1, val_total)

    # 计算 Precision/Recall/F1
    tp = sum(1 for p, l in zip(all_preds, all_labels) if p == 1 and l == 1)
    fp = sum(1 for p, l in zip(all_preds, all_labels) if p == 1 and l == 0)
    fn = sum(1 for p, l in zip(all_preds, all_labels) if p == 0 and l == 1)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-8, precision + recall)

    print(f"Epoch {epoch+1}/{EPOCHS} | "
          f"Loss: {avg_loss:.4f} | Acc: {train_acc:.4f} | "
          f"Val Acc: {val_acc:.4f} | P: {precision:.4f} R: {recall:.4f} F1: {f1:.4f}")

# ============================================================
# 5. 保存模型
# ============================================================
print("\n" + "=" * 60)
model_path = os.path.join(MODEL_DIR, "din_model.pt")
save_model(model, model_path)
print(f"\n训练完成! 模型: {model_path}")
