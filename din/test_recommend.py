"""Quick test of recommend_for_user"""
import os; os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import torch, pickle, numpy as np, sys
sys.path.insert(0, "D:/YueQian/din")
from din_model import load_model

DATA_DIR = "D:/YueQian/din/data"
MODEL_PATH = "D:/YueQian/din/din_model.pt"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TOP_K = 10

# Load data
print("Loading...")
model = load_model(MODEL_PATH, device=DEVICE); model.eval()
with open(os.path.join(DATA_DIR, 'encoder.pkl'), 'rb') as f: encoder = pickle.load(f)
with open(os.path.join(DATA_DIR, 'user_sequences.pkl'), 'rb') as f: user_sequences = pickle.load(f)
with open(os.path.join(DATA_DIR, 'p_items.pkl'), 'rb') as f: p_items = pickle.load(f)

item_to_idx = encoder['item_to_idx']; cat_to_idx = encoder['cat_to_idx']
idx_to_item = encoder['idx_to_item']; idx_to_cat = encoder['idx_to_cat']
max_seq_len = encoder['max_seq_len']

# Prepare P items
p_item_ids = list(p_items.keys())
p_item_indices = np.array([item_to_idx.get(iid, 0) for iid in p_item_ids], dtype=np.int64)
p_cat_indices = np.array([cat_to_idx.get(p_items[iid], 0) for iid in p_item_ids], dtype=np.int64)
valid = (p_item_indices > 0) & (p_item_indices < encoder['num_items'])
p_item_indices = p_item_indices[valid].astype(np.int32)
p_cat_indices = p_cat_indices[valid].astype(np.int32)
p_item_ids_filtered = [p_item_ids[i] for i in range(len(p_item_ids)) if valid[i]]
print(f"Valid P items: {len(p_item_ids_filtered):,}")

def recommend_for_user(uid_str, top_k=TOP_K):
    uid = int(uid_str)
    if uid not in user_sequences:
        return {"error": f"User {uid} not found"}

    seq_data = user_sequences[uid]
    items = seq_data['items'][-max_seq_len:]
    cats = seq_data['cats'][-max_seq_len:]

    seq_item_arr = np.zeros(max_seq_len, dtype=np.int32)
    seq_cat_arr = np.zeros(max_seq_len, dtype=np.int32)
    seq_mask_arr = np.zeros(max_seq_len, dtype=np.float32)
    for i, (iid, cid) in enumerate(zip(items, cats)):
        seq_item_arr[i] = item_to_idx.get(iid, 0)
        seq_cat_arr[i] = cat_to_idx.get(cid, 0)
        seq_mask_arr[i] = 1.0

    # Score all P items in batches
    batch_size = 8192
    all_scores = []
    for s in range(0, len(p_item_ids_filtered), batch_size):
        e = min(s + batch_size, len(p_item_ids_filtered))
        n = e - s
        seq_i = torch.LongTensor(np.tile(seq_item_arr, (n, 1))).to(DEVICE)
        seq_c = torch.LongTensor(np.tile(seq_cat_arr, (n, 1))).to(DEVICE)
        seq_m = torch.FloatTensor(np.tile(seq_mask_arr, (n, 1))).to(DEVICE)
        t_i = torch.LongTensor(p_item_indices[s:e]).to(DEVICE)
        t_c = torch.LongTensor(p_cat_indices[s:e]).to(DEVICE)
        scores = model.predict(seq_i, seq_c, seq_m, t_i, t_c)
        all_scores.extend(scores.cpu().numpy().tolist())

    top_indices = np.argsort(all_scores)[-top_k:][::-1]
    results = []
    for idx in top_indices:
        iid = p_item_ids_filtered[idx]
        cat = p_items.get(iid, 0)
        results.append({"item_id": iid, "category": cat, "score": round(all_scores[idx], 4)})

    return {"user_id": uid, "recommendations": results}

# Test
import time
for username, uid in [("admin", "98047837"), ("dafei", "97726136")]:
    print(f"\n{'='*50}")
    print(f"Testing: {username} (uid={uid})")
    start = time.time()
    result = recommend_for_user(uid, TOP_K)
    elapsed = time.time() - start
    print(f"Inference time: {elapsed:.1f}s")
    if 'error' in result:
        print(f"ERROR: {result['error']}")
    else:
        print(f"Top {TOP_K} recommendations:")
        for r in result['recommendations']:
            print(f"  item={r['item_id']}  cat={r['category']}  score={r['score']}")

print("\n[OK] Test passed!")
