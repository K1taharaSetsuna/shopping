"""
DIN 数据预处理 — 天池移动推荐数据集
输出: 训练集/验证集 pickle、用户序列映射、特征编码器
简化版: 只用后7天数据(12.12~12.18)，序列长度50，负采样1:4
"""
import pandas as pd
import numpy as np
import pickle
import os
from collections import defaultdict
from tqdm import tqdm

DATA_PATH = "D:/data/tianchi_mobile_recommend_train_user/tianchi_mobile_recommend_train_user.csv"
ITEM_PATH = "D:/data/tianchi_mobile_recommend_train_user/tianchi_mobile_recommend_train_item.csv"
OUTPUT_DIR = "D:/YueQian/din/data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 配置
# ============================================================
MAX_SEQ_LEN = 50       # 序列长度
NEG_RATIO = 4           # 正负比 1:4
TOP_K = 10              # 推荐 Top-K

# 简化时间窗口: 只取后7天
DATE_RANGE = ["2014-12-12", "2014-12-13", "2014-12-14", "2014-12-15",
              "2014-12-16", "2014-12-17", "2014-12-18"]

print("=" * 60)
print("DIN 数据预处理")
print(f"序列长度: {MAX_SEQ_LEN} | 正负比: 1:{NEG_RATIO} | 时间: {DATE_RANGE[0]}~{DATE_RANGE[-1]}")
print("=" * 60)

# ============================================================
# Step 1: 加载 P 子集
# ============================================================
print("\n[1/5] 加载 P 子集...")
df_item = pd.read_csv(ITEM_PATH)
p_items_set = set(df_item['item_id'].unique())
# item_id → category 映射
item_to_category = dict(zip(df_item['item_id'], df_item['item_category']))
print(f"  P 子集商品数: {len(p_items_set):,}")
print(f"  P 子集类目数: {df_item['item_category'].nunique()}")

# ============================================================
# Step 2: 加载 D 数据（只取后7天）
# ============================================================
print("\n[2/5] 加载用户行为数据（后7天）...")

# 存储每个用户的行为序列（按时间排序）
user_sequences = defaultdict(list)  # uid → [(item_id, category, behavior_type, hour, date), ...]
# 存储每天的用户行为
daily_user_actions = defaultdict(lambda: defaultdict(set))  # date → uid → {item_ids interacted}

chunk_size = 500_000
total_loaded = 0
for chunk in pd.read_csv(DATA_PATH, chunksize=chunk_size):
    # 过滤时间范围
    chunk['date'] = chunk['time'].str[:10]
    chunk = chunk[chunk['date'].isin(DATE_RANGE)]
    if len(chunk) == 0:
        continue

    chunk['hour'] = chunk['time'].str[-2:].astype(int)
    for _, row in chunk.iterrows():
        uid = row['user_id']
        iid = row['item_id']
        bt = row['behavior_type']
        cat = row['item_category']
        hour = row['hour']
        date = row['date']
        user_sequences[uid].append((iid, cat, bt, hour, date))
        daily_user_actions[date][uid].add(iid)

    total_loaded += len(chunk)

print(f"  加载行为数: {total_loaded:,}")
print(f"  用户数: {len(user_sequences):,}")

# 按时间排序每个用户的行为序列
for uid in user_sequences:
    user_sequences[uid].sort(key=lambda x: x[4])  # 按 date 排序

# ============================================================
# Step 3: 构建特征编码器
# ============================================================
print("\n[3/5] 构建特征编码器...")

# 收集所有 item_id 和 category
all_items = set()
all_cats = set()
for uid, seq in user_sequences.items():
    for iid, cat, bt, hour, date in seq:
        all_items.add(iid)
        all_cats.add(cat)
all_items.update(p_items_set)  # 确保 P 中商品都在

item_to_idx = {item: idx + 1 for idx, item in enumerate(sorted(all_items))}  # 0 留给 padding
cat_to_idx = {cat: idx + 1 for idx, cat in enumerate(sorted(all_cats))}
idx_to_item = {v: k for k, v in item_to_idx.items()}
idx_to_cat = {v: k for k, v in cat_to_idx.items()}

print(f"  item_id 词表大小: {len(item_to_idx):,} (含 padding 0)")
print(f"  category 词表大小: {len(cat_to_idx):,} (含 padding 0)")

# ============================================================
# Step 4: 构造训练样本
# ============================================================
print("\n[4/5] 构造训练样本...")

# 训练集: 12.12~12.16 行为 → 预测 12.17 购买 P 商品
# 验证集: 12.13~12.17 行为 → 预测 12.18 购买 P 商品

TRAIN_DAYS = ["2014-12-12", "2014-12-13", "2014-12-14", "2014-12-15", "2014-12-16"]
TRAIN_TARGET = "2014-12-17"
VAL_DAYS = ["2014-12-13", "2014-12-14", "2014-12-15", "2014-12-16", "2014-12-17"]
VAL_TARGET = "2014-12-18"

def build_samples(target_date, history_days, desc="train"):
    """为指定目标日构造训练样本"""
    samples = []  # [(seq_items, seq_cats, seq_mask, target_item, target_cat, label), ...]

    # 当天在 P 中的交互
    target_day_actions = daily_user_actions.get(target_date, {})
    # 历史所有天的行为
    history_actions = defaultdict(set)
    for d in history_days:
        for uid, items in daily_user_actions.get(d, {}).items():
            history_actions[uid].update(items)

    users_with_target = set(target_day_actions.keys())
    print(f"  [{desc}] {target_date}: 有行为的用户 {len(users_with_target):,}")

    pos_count = 0
    neg_count = 0
    skipped_no_seq = 0
    skipped_no_pos = 0

    for uid in tqdm(users_with_target, desc=f"  [{desc}] 构造样本"):
        # 获取用户全部行为序列
        full_seq = user_sequences.get(uid, [])
        if len(full_seq) == 0:
            skipped_no_seq += 1
            continue

        # 只保留目标日之前的行为，取最近 MAX_SEQ_LEN 条
        seq_before_target = [s for s in full_seq if s[4] < target_date]
        recent_seq = seq_before_target[-MAX_SEQ_LEN:]

        if len(recent_seq) == 0:
            skipped_no_seq += 1
            continue

        # 构造序列特征
        seq_items = [item_to_idx[s[0]] for s in recent_seq]
        seq_cats = [cat_to_idx[s[1]] for s in recent_seq]

        # 当天购买的 P 商品（正样本）
        bought_p = set()
        for s in full_seq:
            if s[4] == target_date and s[0] in p_items_set and s[2] == 4:
                bought_p.add(s[0])

        if len(bought_p) == 0:
            skipped_no_pos += 1
            continue

        # 负样本: 从用户历史所有天浏览过但从未买过的 P 商品中采样
        # 收集用户所有历史交互过的 P 商品
        history_p_items = set()
        history_p_bought = set()
        for s in full_seq:
            if s[4] <= target_date and s[0] in p_items_set:
                history_p_items.add(s[0])
                if s[2] == 4:
                    history_p_bought.add(s[0])

        neg_candidates = list(history_p_items - history_p_bought)
        # 如果历史负样本不够，补充P中热门商品（用户未交互过的）
        if len(neg_candidates) < len(bought_p) * NEG_RATIO:
            # 从P中随机采样补充
            extra_needed = len(bought_p) * NEG_RATIO - len(neg_candidates)
            extra_pool = list(p_items_set - history_p_items - history_p_bought)
            if len(extra_pool) > extra_needed:
                extra = list(np.random.choice(list(extra_pool), extra_needed, replace=False))
            elif len(extra_pool) > 0:
                extra = list(np.random.choice(list(extra_pool), extra_needed, replace=True))
            else:
                extra = []
            neg_candidates.extend(extra)

        # 正样本
        for pos_item in bought_p:
            if pos_item not in item_to_idx:
                continue
            pos_count += 1
            samples.append((
                seq_items, seq_cats,
                item_to_idx[pos_item], cat_to_idx.get(item_to_category.get(pos_item, 0), 0),
                1
            ))

        # 负样本
        n_neg_needed = len(bought_p) * NEG_RATIO
        if len(neg_candidates) >= n_neg_needed:
            neg_sampled = np.random.choice(neg_candidates, n_neg_needed, replace=False)
        else:
            neg_sampled = np.random.choice(neg_candidates, n_neg_needed, replace=True)

        for neg_item in neg_sampled:
            neg_count += 1
            samples.append((
                seq_items, seq_cats,
                item_to_idx[neg_item], cat_to_idx.get(item_to_category.get(neg_item, 0), 0),
                0
            ))

    print(f"  [{desc}] 正样本: {pos_count}, 负样本: {neg_count}")
    print(f"  [{desc}] 跳过(无序列): {skipped_no_seq}, 跳过(无正样本): {skipped_no_pos}")
    return samples

train_samples = build_samples(TRAIN_TARGET, TRAIN_DAYS, "train")
val_samples = build_samples(VAL_TARGET, VAL_DAYS, "val")

# ============================================================
# Step 5: 转换为训练格式 & 保存
# ============================================================
print("\n[5/5] 格式转换 & 保存...")

def samples_to_arrays(samples, max_seq_len=MAX_SEQ_LEN):
    """将样本列表转为 padded numpy arrays"""
    n = len(samples)
    seq_items_arr = np.zeros((n, max_seq_len), dtype=np.int32)
    seq_cats_arr = np.zeros((n, max_seq_len), dtype=np.int32)
    seq_mask_arr = np.zeros((n, max_seq_len), dtype=np.float32)
    target_item_arr = np.zeros(n, dtype=np.int32)
    target_cat_arr = np.zeros(n, dtype=np.int32)
    labels_arr = np.zeros(n, dtype=np.float32)

    for i, (seq_items, seq_cats, target_item, target_cat, label) in enumerate(samples):
        seq_len = min(len(seq_items), max_seq_len)
        seq_items_arr[i, :seq_len] = seq_items[-seq_len:]  # 取最后 max_seq_len 个
        seq_cats_arr[i, :seq_len] = seq_cats[-seq_len:]
        seq_mask_arr[i, :seq_len] = 1.0
        target_item_arr[i] = target_item
        target_cat_arr[i] = target_cat
        labels_arr[i] = label

    return {
        'seq_items': seq_items_arr,
        'seq_cats': seq_cats_arr,
        'seq_mask': seq_mask_arr,
        'target_item': target_item_arr,
        'target_cat': target_cat_arr,
        'labels': labels_arr,
    }

train_data = samples_to_arrays(train_samples)
val_data = samples_to_arrays(val_samples)

print(f"  训练集样本: {len(train_samples):,} (正: {int(train_data['labels'].sum())})")
print(f"  验证集样本: {len(val_samples):,} (正: {int(val_data['labels'].sum())})")

# 保存
with open(os.path.join(OUTPUT_DIR, 'train.pkl'), 'wb') as f:
    pickle.dump(train_data, f)
with open(os.path.join(OUTPUT_DIR, 'val.pkl'), 'wb') as f:
    pickle.dump(val_data, f)

# 保存编码器 & 用户序列
encoder = {
    'item_to_idx': item_to_idx,
    'cat_to_idx': cat_to_idx,
    'idx_to_item': idx_to_item,
    'idx_to_cat': idx_to_cat,
    'item_to_category': item_to_category,
    'num_items': len(item_to_idx),
    'num_cats': len(cat_to_idx),
    'max_seq_len': MAX_SEQ_LEN,
}
with open(os.path.join(OUTPUT_DIR, 'encoder.pkl'), 'wb') as f:
    pickle.dump(encoder, f)

# 保存用户序列（推理用）
# 转为可序列化格式
user_sequences_export = {}
for uid, seq in user_sequences.items():
    user_sequences_export[uid] = {
        'items': [s[0] for s in seq],
        'cats': [s[1] for s in seq],
        'behaviors': [s[2] for s in seq],
        'hours': [s[3] for s in seq],
        'dates': [s[4] for s in seq],
    }
with open(os.path.join(OUTPUT_DIR, 'user_sequences.pkl'), 'wb') as f:
    pickle.dump(user_sequences_export, f)

# 保存 P 子集的 item_id → category 映射
p_items_with_cat = {iid: item_to_category.get(iid, 0) for iid in p_items_set}
with open(os.path.join(OUTPUT_DIR, 'p_items.pkl'), 'wb') as f:
    pickle.dump(p_items_with_cat, f)

print(f"\n[OK] 预处理完成! 输出文件:")
for fname in ['train.pkl', 'val.pkl', 'encoder.pkl', 'user_sequences.pkl', 'p_items.pkl']:
    fpath = os.path.join(OUTPUT_DIR, fname)
    size_mb = os.path.getsize(fpath) / 1024 / 1024
    print(f"  {fname}: {size_mb:.1f} MB")
