"""
DIN (Deep Interest Network) 模型 — PyTorch 实现
核心: Attention Pooling 对用户历史行为序列做局部激活
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class DiceActivation(nn.Module):
    """Dice 激活函数 (DIN 论文提出的自适应激活)"""
    def __init__(self):
        super().__init__()
        self.alpha = nn.Parameter(torch.zeros(1))

    def forward(self, x):
        mean = x.mean(dim=-1, keepdim=True)
        var = x.var(dim=-1, keepdim=True) + 1e-8
        x_norm = (x - mean) / var.sqrt()
        p = torch.sigmoid(x_norm)
        return self.alpha * (1 - p) * x + p * x


class AttentionPooling(nn.Module):
    """
    DIN 的核心 Attention 机制:
    对用户历史行为序列，根据候选商品计算注意力权重，加权求和得到用户兴趣向量
    """
    def __init__(self, embed_dim):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(embed_dim * 4, 64),
            DiceActivation(),
            nn.Linear(64, 32),
            DiceActivation(),
            nn.Linear(32, 1),
        )

    def forward(self, query, keys, mask):
        """
        query: [batch, embed_dim] — 候选商品的 embedding
        keys:  [batch, seq_len, embed_dim] — 历史序列中每个商品的 embedding
        mask:  [batch, seq_len] — padding mask (1=有效, 0=padding)
        返回:  [batch, embed_dim] — 用户兴趣向量
        """
        batch_size, seq_len, embed_dim = keys.shape

        # query 扩展到序列长度: [batch, seq_len, embed_dim]
        query_expand = query.unsqueeze(1).expand(-1, seq_len, -1)

        # DIN attention: 拼接 query, keys, query*keys, query-keys
        outer = query_expand * keys  # element-wise product
        diff = query_expand - keys   # difference
        concat = torch.cat([query_expand, keys, outer, diff], dim=-1)  # [B, L, 4E]

        # 计算 attention score: [B, L, 1]
        attn_score = self.fc(concat)

        # mask 掉 padding 位置
        attn_score = attn_score.squeeze(-1)  # [B, L]
        attn_score = attn_score.masked_fill(mask == 0, -1e9)
        attn_weight = F.softmax(attn_score, dim=-1).unsqueeze(-1)  # [B, L, 1]

        # 加权求和
        output = (keys * attn_weight).sum(dim=1)  # [B, E]

        return output


class DINModel(nn.Module):
    """
    DIN 模型
    输入:
      - seq_items:     [batch, max_seq_len] — 用户历史行为序列(item_id)
      - seq_cats:      [batch, max_seq_len] — 历史序列的 category
      - seq_mask:      [batch, max_seq_len]
      - target_item:   [batch] — 候选商品 item_id
      - target_cat:    [batch] — 候选商品 category
    输出:
      - logits: [batch] — 购买概率(0~1)
    """
    def __init__(self,
                 num_items,        # item_id 词表大小
                 num_cats,         # category 词表大小
                 item_emb_dim=128,
                 cat_emb_dim=32,
                 max_seq_len=50,
                 dnn_hidden=[256, 128, 64],
                 dropout=0.2):
        super().__init__()

        self.max_seq_len = max_seq_len
        self.total_emb_dim = item_emb_dim + cat_emb_dim

        # Embedding 层
        self.item_embedding = nn.Embedding(num_items, item_emb_dim, padding_idx=0)
        self.cat_embedding = nn.Embedding(num_cats, cat_emb_dim, padding_idx=0)

        # Attention Pooling (DIN 核心)
        self.attention = AttentionPooling(self.total_emb_dim)

        # DNN 预测层
        # 输入: 用户兴趣向量 + 候选商品 embedding + 候选类别 embedding
        dnn_input_dim = self.total_emb_dim * 2  # 用户兴趣 + 候选商品

        layers = []
        prev_dim = dnn_input_dim
        for h in dnn_hidden:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.BatchNorm1d(h))
            layers.append(DiceActivation())
            layers.append(nn.Dropout(dropout))
            prev_dim = h

        layers.append(nn.Linear(prev_dim, 1))
        self.dnn = nn.Sequential(*layers)

        # 初始化
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, mean=0, std=0.01)

    def get_item_embedding(self, item_ids):
        """获取商品的完整 embedding (item + category)"""
        return self.item_embedding(item_ids)

    def get_item_full_embedding(self, item_ids, cat_ids):
        """获取商品完整 embedding: item_emb + cat_emb"""
        item_emb = self.item_embedding(item_ids)
        cat_emb = self.cat_embedding(cat_ids)
        return torch.cat([item_emb, cat_emb], dim=-1)

    def forward(self, seq_items, seq_cats, seq_mask, target_item, target_cat):
        """
        前向传播，返回原始 logits（未经 sigmoid）
        """
        batch_size = seq_items.shape[0]

        # 1. 历史序列 embedding: [B, L, E]
        seq_item_emb = self.item_embedding(seq_items)    # [B, L, item_dim]
        seq_cat_emb = self.cat_embedding(seq_cats)       # [B, L, cat_dim]
        seq_emb = torch.cat([seq_item_emb, seq_cat_emb], dim=-1)  # [B, L, E_total]

        # 2. 候选商品 embedding: [B, E_total]
        target_item_emb = self.item_embedding(target_item)
        target_cat_emb = self.cat_embedding(target_cat)
        target_emb = torch.cat([target_item_emb, target_cat_emb], dim=-1)

        # 3. Attention Pooling → 用户兴趣向量: [B, E_total]
        user_interest = self.attention(target_emb, seq_emb, seq_mask)

        # 4. 拼接 → DNN 预测
        concat = torch.cat([user_interest, target_emb], dim=-1)
        logits = self.dnn(concat).squeeze(-1)

        return logits  # 返回原始 logits

    def predict(self, seq_items, seq_cats, seq_mask, target_item, target_cat):
        """推理模式，返回概率"""
        self.eval()
        with torch.no_grad():
            logits = self.forward(seq_items, seq_cats, seq_mask, target_item, target_cat)
            return torch.sigmoid(logits)


# ============================================================
# 模型加载/保存工具
# ============================================================
def save_model(model, path):
    torch.save({
        'model_state_dict': model.state_dict(),
        'num_items': model.item_embedding.num_embeddings,
        'num_cats': model.cat_embedding.num_embeddings,
        'max_seq_len': model.max_seq_len,
    }, path)
    print(f"[OK] 模型已保存: {path}")


def load_model(path, device='cpu'):
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    model = DINModel(
        num_items=checkpoint['num_items'],
        num_cats=checkpoint['num_cats'],
        max_seq_len=checkpoint['max_seq_len'],
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    print(f"[OK] 模型已加载: {path}")
    return model


if __name__ == "__main__":
    # 快速测试：前向传播
    print("测试 DIN 模型前向传播...")
    model = DINModel(
        num_items=10000,
        num_cats=1000,
        item_emb_dim=128,
        cat_emb_dim=32,
        max_seq_len=50,
    )

    batch = 32
    seq_len = 50
    seq_items = torch.randint(1, 10000, (batch, seq_len))
    seq_cats = torch.randint(1, 1000, (batch, seq_len))
    seq_mask = torch.ones(batch, seq_len)
    seq_mask[:, 40:] = 0  # 模拟 padding
    target_item = torch.randint(1, 10000, (batch,))
    target_cat = torch.randint(1, 1000, (batch,))

    out = model(seq_items, seq_cats, seq_mask, target_item, target_cat)
    print(f"  输入: seq={seq_items.shape}, target={target_item.shape}")
    print(f"  输出: {out.shape}, range=[{out.min().item():.4f}, {out.max().item():.4f}]")
    print(f"  参数量: {sum(p.numel() for p in model.parameters()):,}")
    print("[OK] DIN 模型测试通过!")
