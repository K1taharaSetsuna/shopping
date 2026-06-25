"""
天池移动推荐数据集 EDA（探索性数据分析）
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

DATA_PATH = "D:/data/tianchi_mobile_recommend_train_user/tianchi_mobile_recommend_train_user.csv"
ITEM_PATH = "D:/data/tianchi_mobile_recommend_train_user/tianchi_mobile_recommend_train_item.csv"
OUTPUT_DIR = "D:/YueQian/din"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 1. 数据集基本信息
# ============================================================
print("=" * 60)
print("1. 数据集基本信息")
print("=" * 60)

# 商品子集 P
df_item = pd.read_csv(ITEM_PATH)
print(f"\n[商品子集 P] tianchi_mobile_recommend_train_item.csv")
print(f"  行数: {len(df_item):,}")
print(f"  列: {list(df_item.columns)}")
print(f"  唯一 item_id: {df_item['item_id'].nunique():,}")
print(f"  唯一 item_category: {df_item['item_category'].nunique():,}")
print(f"  item_geohash 缺失率: {df_item['item_geohash'].isna().mean()*100:.1f}%")

# 用户行为数据 D — 分块统计
print(f"\n[用户行为 D] tianchi_mobile_recommend_train_user.csv")
print(f"  列: ['user_id', 'item_id', 'behavior_type', 'user_geohash', 'item_category', 'time']")

# 分块读取统计
chunk_size = 500_000
total_rows = 0
all_behavior_counts = Counter()
unique_users = set()
unique_items = set()
unique_categories = set()
geohash_na_count = 0

for chunk in pd.read_csv(DATA_PATH, chunksize=chunk_size):
    total_rows += len(chunk)
    all_behavior_counts.update(chunk['behavior_type'].value_counts().to_dict())
    unique_users.update(chunk['user_id'].unique())
    unique_items.update(chunk['item_id'].unique())
    unique_categories.update(chunk['item_category'].unique())
    geohash_na_count += chunk['user_geohash'].isna().sum()
    if total_rows % 2_000_000 == 0:
        print(f"  已处理 {total_rows:,} 行...")

print(f"\n  总行数: {total_rows:,}")
print(f"  唯一 user_id: {len(unique_users):,}")
print(f"  唯一 item_id: {len(unique_items):,}")
print(f"  唯一 item_category: {len(unique_categories):,}")
print(f"  user_geohash 缺失率: {geohash_na_count/total_rows*100:.1f}%")

# ============================================================
# 2. 行为类型分布
# ============================================================
print("\n" + "=" * 60)
print("2. 行为类型分布 (1=浏览 2=收藏 3=加购 4=购买)")
print("=" * 60)

behavior_names = {1: '浏览', 2: '收藏', 3: '加购物车', 4: '购买'}
for bt in sorted(all_behavior_counts.keys()):
    count = all_behavior_counts[bt]
    print(f"  {behavior_names[bt]}({bt}): {count:>12,} ({count/total_rows*100:5.2f}%)")

# ============================================================
# 3. 时间分布分析
# ============================================================
print("\n" + "=" * 60)
print("3. 时间分布分析")
print("=" * 60)

# 分块统计每日行为
daily_counts = Counter()
hourly_counts = Counter()

for chunk in pd.read_csv(DATA_PATH, chunksize=chunk_size):
    chunk['date'] = chunk['time'].str[:10]  # "2014-12-06"
    chunk['hour'] = chunk['time'].str[-2:].astype(int)
    daily_counts.update(chunk['date'].value_counts().to_dict())
    hourly_counts.update(chunk['hour'].value_counts().to_dict())

print(f"\n  时间范围: {min(daily_counts.keys())} ~ {max(daily_counts.keys())}")
print(f"  总天数: {len(daily_counts)}")
print(f"\n  每日行为分布（前10天和后10天）:")
dates_sorted = sorted(daily_counts.items())
print(f"  {'日期':<14} {'行为数':>10} {'累计占比':>10}")
cum = 0
for date, count in dates_sorted[:10]:
    cum += count
    print(f"  {date:<14} {count:>10,} {cum/total_rows*100:>9.2f}%")
print(f"  ...")
for date, count in dates_sorted[-10:]:
    cum += count
    print(f"  {date:<14} {count:>10,} {cum/total_rows*100:>9.2f}%")

print(f"\n  每日购买行为分布:")
daily_buy = Counter()
for chunk in pd.read_csv(DATA_PATH, chunksize=chunk_size):
    chunk['date'] = chunk['time'].str[:10]
    buy_chunk = chunk[chunk['behavior_type'] == 4]
    daily_buy.update(buy_chunk['date'].value_counts().to_dict())
for date, _ in dates_sorted[:5]:
    buys = daily_buy.get(date, 0)
    print(f"  {date}: 购买 {buys:,}")

# ============================================================
# 4. 用户行为统计
# ============================================================
print("\n" + "=" * 60)
print("4. 用户行为统计（基于前200W行采样）")
print("=" * 60)

# 取前200W行做用户级别分析（避免内存溢出）
sample_chunks = []
sample_rows = 0
for chunk in pd.read_csv(DATA_PATH, chunksize=chunk_size):
    sample_chunks.append(chunk)
    sample_rows += len(chunk)
    if sample_rows >= 2_000_000:
        break

df_sample = pd.concat(sample_chunks, ignore_index=True)
print(f"  采样行数: {len(df_sample):,}")

# 用户行为统计
user_stats = df_sample.groupby('user_id').agg(
    行为总数=('behavior_type', 'count'),
    浏览数=('behavior_type', lambda x: (x == 1).sum()),
    收藏数=('behavior_type', lambda x: (x == 2).sum()),
    加购数=('behavior_type', lambda x: (x == 3).sum()),
    购买数=('behavior_type', lambda x: (x == 4).sum()),
    唯一商品数=('item_id', 'nunique'),
    唯一类目数=('item_category', 'nunique'),
)

print(f"\n  采样用户数: {len(user_stats):,}")
print(f"\n  用户行为分布:")
print(user_stats.describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).to_string())

# 转化率
buy_users = (user_stats['购买数'] > 0).sum()
print(f"\n  有购买行为的用户: {buy_users} / {len(user_stats)} ({buy_users/len(user_stats)*100:.1f}%)")

# ============================================================
# 5. 商品热度分布
# ============================================================
print("\n" + "=" * 60)
print("5. 商品热度分布（采样）")
print("=" * 60)

item_popularity = df_sample['item_id'].value_counts()
print(f"\n  商品被交互次数分布:")
print(f"  mean:  {item_popularity.mean():.1f}")
print(f"  median: {item_popularity.median():.1f}")
print(f"  max:    {item_popularity.max()}")
print(f"  99%分位: {item_popularity.quantile(0.99):.1f}")
print(f"  被交互1次的商品: {(item_popularity == 1).sum()} / {len(item_popularity)} ({(item_popularity == 1).sum()/len(item_popularity)*100:.1f}%)")
print(f"  被交互>=100次的商品: {(item_popularity >= 100).sum()}")

# 商品购买热度
buy_item_pop = df_sample[df_sample['behavior_type'] == 4]['item_id'].value_counts()
print(f"\n  商品被购买次数分布:")
print(f"  有购买记录的商品数: {len(buy_item_pop)}")
print(f"  mean:  {buy_item_pop.mean():.1f}")
print(f"  max:   {buy_item_pop.max()}")
print(f"  被买>=10次的商品: {(buy_item_pop >= 10).sum()}")

# ============================================================
# 6. 类目分析
# ============================================================
print("\n" + "=" * 60)
print("6. 类目分析（采样）")
print("=" * 60)

cat_pop = df_sample['item_category'].value_counts()
print(f"\n  类目数: {len(cat_pop)}")
print(f"  Top 10 热门类目:")
for cat, count in cat_pop.head(10).items():
    print(f"    类目 {cat}: {count:>8,} 次交互")

# 类目与购买的关系
cat_buy = df_sample[df_sample['behavior_type'] == 4]['item_category'].value_counts()
print(f"\n  Top 10 购买类目:")
for cat, count in cat_buy.head(10).items():
    print(f"    类目 {cat}: {count:>8,} 次购买")

# ============================================================
# 7. 购买转化路径分析
# ============================================================
print("\n" + "=" * 60)
print("7. 购买转化分析（采样）")
print("=" * 60)

# 统计 behavior_type 转移
# 每个用户按时间排序，看购买前的行为
total_buys = 0
buys_with_prior = 0
prior_behavior_dist = Counter()

for uid, group in df_sample.groupby('user_id'):
    group = group.sort_values('time')
    for i, row in group.iterrows():
        if row['behavior_type'] == 4:
            total_buys += 1
            # 找之前对同一商品的行为
            prior = group[(group.index < i) & (group['item_id'] == row['item_id'])]
            if len(prior) > 0:
                buys_with_prior += 1
                for bt in prior['behavior_type']:
                    prior_behavior_dist[bt] += 1

print(f"  总购买次数: {total_buys}")
print(f"  购买前有交互的: {buys_with_prior} ({buys_with_prior/total_buys*100:.1f}%)")
print(f"  购买前行为分布:")
for bt in [1, 2, 3]:
    print(f"    {behavior_names[bt]}: {prior_behavior_dist.get(bt, 0)}")

# ============================================================
# 8. 商品子集 P 与 行为数据 D 的交集
# ============================================================
print("\n" + "=" * 60)
print("8. 商品子集 P 与行为数据 D 的交集")
print("=" * 60)

p_items = set(df_item['item_id'].unique())

# 分块统计 P 中商品在 D 中的行为
p_in_d_total = 0
p_buy_total = 0
for chunk in pd.read_csv(DATA_PATH, chunksize=chunk_size):
    in_p = chunk['item_id'].isin(p_items)
    p_in_d_total += in_p.sum()
    p_buy_total += ((chunk['behavior_type'] == 4) & in_p).sum()

print(f"  P 中商品数: {len(p_items):,}")
print(f"  P 中商品在 D 中被交互的总次数: {p_in_d_total:,} ({p_in_d_total/total_rows*100:.1f}%)")
print(f"  P 中商品在 D 中被购买次数: {p_buy_total:,}")

# 有多少P中商品实际有行为数据
p_items_with_behavior = set()
p_items_bought = set()
for chunk in pd.read_csv(DATA_PATH, chunksize=chunk_size):
    p_mask = chunk['item_id'].isin(p_items)
    if p_mask.any():
        p_items_with_behavior.update(chunk.loc[p_mask, 'item_id'].unique())
        p_items_bought.update(chunk.loc[p_mask & (chunk['behavior_type'] == 4), 'item_id'].unique())

print(f"  P 中有被交互的商品: {len(p_items_with_behavior):,} / {len(p_items):,} ({len(p_items_with_behavior)/len(p_items)*100:.1f}%)")
print(f"  P 中有被购买的商品: {len(p_items_bought):,} / {len(p_items):,} ({len(p_items_bought)/len(p_items)*100:.1f}%)")

# ============================================================
# 9. 用户序列长度分布
# ============================================================
print("\n" + "=" * 60)
print("9. 用户行为序列长度分布（采样）")
print("=" * 60)

seq_lengths = df_sample.groupby('user_id').size()
print(f"  序列长度分布:")
print(f"  mean:   {seq_lengths.mean():.1f}")
print(f"  median: {seq_lengths.median():.1f}")
print(f"  分位数:")
for p in [0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]:
    print(f"    {p*100:>5.0f}%: {seq_lengths.quantile(p):.0f}")

# 序列长度分桶
bins = [0, 5, 10, 20, 50, 100, 200, 500, 100000]
labels = ['1-5', '6-10', '11-20', '21-50', '51-100', '101-200', '201-500', '500+']
seq_bins = pd.cut(seq_lengths, bins=bins, labels=labels)
print(f"\n  序列长度分布:")
for label, count in seq_bins.value_counts().sort_index().items():
    print(f"    {label}: {count:>6,} ({count/len(seq_lengths)*100:5.2f}%)")

# ============================================================
# 10. 购买用户 vs 非购买用户
# ============================================================
print("\n" + "=" * 60)
print("10. 购买用户 vs 非购买用户对比")
print("=" * 60)

buy_user_set = set(df_sample[df_sample['behavior_type'] == 4]['user_id'].unique())
user_type_stats = []
for uid, row in user_stats.iterrows():
    user_type_stats.append({
        'user_id': uid,
        'is_buyer': uid in buy_user_set,
        '行为总数': row['行为总数'],
        '唯一商品数': row['唯一商品数'],
        '唯一类目数': row['唯一类目数'],
    })

df_ut = pd.DataFrame(user_type_stats)
buyers = df_ut[df_ut['is_buyer']]
non_buyers = df_ut[~df_ut['is_buyer']]

print(f"\n  购买用户 (n={len(buyers):,}):")
print(f"    平均行为数: {buyers['行为总数'].mean():.1f}")
print(f"    平均唯一商品数: {buyers['唯一商品数'].mean():.1f}")
print(f"    平均唯一类目数: {buyers['唯一类目数'].mean():.1f}")

print(f"\n  非购买用户 (n={len(non_buyers):,}):")
print(f"    平均行为数: {non_buyers['行为总数'].mean():.1f}")
print(f"    平均唯一商品数: {non_buyers['唯一商品数'].mean():.1f}")
print(f"    平均唯一类目数: {non_buyers['唯一类目数'].mean():.1f}")

# ============================================================
# 11. 时间窗口建议
# ============================================================
print("\n" + "=" * 60)
print("11. 训练/验证/测试划分建议")
print("=" * 60)

print(f"""
  数据时间范围: 2014.11.18 ~ 2014.12.18 (31天)
  预测目标日:   2014.12.19
  评测指标:     Precision, Recall, F1

  建议划分:
  ┌─────────────────────────────────────────────────────────────┐
  │ 训练集: 11.18 ~ 12.16 (29天)                                 │
  │   输入特征: 用户序列 + 候选商品                               │
  │   标签: 12.17 是否购买 P 中商品                               │
  │                                                              │
  │ 验证集: 11.19 ~ 12.17 (29天)                                 │
  │   标签: 12.18 是否购买 P 中商品                               │
  │                                                              │
  │ 测试目标: 预测 12.19 对 P 中商品的购买                        │
  │   (无标签，提交到天池平台评测)                                │
  └─────────────────────────────────────────────────────────────┘

  关键指标回顾:
  - 总用户数: {len(unique_users):,}
  - 总商品数: {len(unique_items):,}
  - P 中商品数: {len(p_items):,}
  - 购买行为占比: {all_behavior_counts.get(4,0)/total_rows*100:.2f}%
  - P 中商品被购买次数: {p_buy_total:,}
""")

print("\n✅ EDA 完成!")
print(f"图片将保存在: {OUTPUT_DIR}/")
