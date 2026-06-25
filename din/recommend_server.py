"""
DIN Recommendation Server - Flask API
Usage: python recommend_server.py
Port: 5001
"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
import numpy as np
import pickle
import traceback
from flask import Flask, request, jsonify
from din_model import load_model

app = Flask(__name__)

MODEL_PATH = "D:/YueQian/din/din_model.pt"
DATA_DIR = "D:/YueQian/din/data"
TOP_K = 10
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Demo account -> Tianchi user_id mapping
ACCOUNT_MAP = {
    "admin": "98047837",
    "dafei": "97726136",
    "shoe_shop": "98607707",
    "cloth_shop": "98662432",
}

print("=" * 50)
print("DIN Recommendation Server")
print(f"Device: {DEVICE}")

# Load model
print(f"\n[1/3] Loading model: {MODEL_PATH}")
model = load_model(MODEL_PATH, device=DEVICE)
model.eval()
print(f"  Parameters: {sum(p.numel() for p in model.parameters()):,}")

# Load data
print("\n[2/3] Loading data...")
with open(os.path.join(DATA_DIR, 'encoder.pkl'), 'rb') as f:
    encoder = pickle.load(f)
with open(os.path.join(DATA_DIR, 'user_sequences.pkl'), 'rb') as f:
    user_sequences = pickle.load(f)
with open(os.path.join(DATA_DIR, 'p_items.pkl'), 'rb') as f:
    p_items = pickle.load(f)

item_to_idx = encoder['item_to_idx']
cat_to_idx = encoder['cat_to_idx']
max_seq_len = encoder['max_seq_len']

print(f"  Users: {len(user_sequences):,}")
print(f"  P items: {len(p_items):,}")
print(f"  max_seq_len: {max_seq_len}")

# Pre-compute P item indices (filter invalid)
p_item_ids = list(p_items.keys())
p_item_indices = np.array([item_to_idx.get(iid, 0) for iid in p_item_ids], dtype=np.int64)
p_cat_indices = np.array([cat_to_idx.get(p_items[iid], 0) for iid in p_item_ids], dtype=np.int64)
valid = (p_item_indices > 0) & (p_item_indices < encoder['num_items'])
p_item_indices = p_item_indices[valid].astype(np.int32)
p_cat_indices = p_cat_indices[valid].astype(np.int32)
p_item_ids_filtered = [p_item_ids[i] for i in range(len(p_item_ids)) if valid[i]]
print(f"  Valid P items: {len(p_item_ids_filtered):,} (filtered {int((~valid).sum())})")


def recommend_for_user(uid_str, top_k=TOP_K):
    """Recommend Top-K P items for a Tianchi user"""
    uid = int(uid_str)

    if uid not in user_sequences:
        return {"error": f"User {uid} not found in behavior data"}

    seq_data = user_sequences[uid]
    items = seq_data['items'][-max_seq_len:]
    cats = seq_data['cats'][-max_seq_len:]

    # Build sequence input
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

    for start in range(0, len(p_item_ids_filtered), batch_size):
        end = min(start + batch_size, len(p_item_ids_filtered))
        n = end - start

        seq_i = torch.LongTensor(np.tile(seq_item_arr, (n, 1))).to(DEVICE)
        seq_c = torch.LongTensor(np.tile(seq_cat_arr, (n, 1))).to(DEVICE)
        seq_m = torch.FloatTensor(np.tile(seq_mask_arr, (n, 1))).to(DEVICE)
        t_i = torch.LongTensor(p_item_indices[start:end]).to(DEVICE)
        t_c = torch.LongTensor(p_cat_indices[start:end]).to(DEVICE)

        scores = model.predict(seq_i, seq_c, seq_m, t_i, t_c)
        all_scores.extend(scores.cpu().numpy().tolist())

    # Top-K
    top_indices = np.argsort(all_scores)[-top_k:][::-1]
    results = []
    for idx in top_indices:
        iid = p_item_ids_filtered[idx]
        cat = int(p_items.get(iid, 0))
        results.append({
            "item_id": int(iid),
            "category": cat,
            "score": round(float(all_scores[idx]), 4),
        })

    return {"user_id": uid, "recommendations": results}


# ============================================================
# API Endpoints
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model": "DIN",
        "device": str(DEVICE),
        "users_loaded": len(user_sequences),
        "p_items": len(p_items),
    })


@app.route("/recommend", methods=["POST", "OPTIONS"])
def recommend():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return resp

    try:
        # Try multiple ways to parse the body
        data = request.get_json(silent=True)

        # If JSON parsing failed, try form data or raw body
        if not data:
            raw_body = request.get_data(as_text=True).strip()
            if raw_body:
                import json
                try:
                    data = json.loads(raw_body)
                except:
                    pass

        # If still no data, try request.form
        if not data and request.form:
            data = dict(request.form)

        # If still no data, try request.args (for GET-like POST)
        if not data and request.args:
            data = dict(request.args)

        if not data:
            raw_body = request.get_data(as_text=True)
            content_type = request.headers.get('Content-Type', '')
            print(f"[DEBUG 400] ct={content_type}, body={raw_body[:300]}")
            return jsonify({"error": "Empty request body"}), 400

        if "username" in data:
            username = data["username"]
            if username not in ACCOUNT_MAP:
                return jsonify({"error": f"Unknown user: {username}, available: {list(ACCOUNT_MAP.keys())}"}), 400
            uid = ACCOUNT_MAP[username]
        elif "user_id" in data:
            uid = str(data["user_id"])
        else:
            return jsonify({"error": "Missing user_id or username"}), 400

        top_k = data.get("top_k", TOP_K)
        result = recommend_for_user(uid, top_k)

        if "username" in data:
            result["username"] = data["username"]

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/users", methods=["GET"])
def list_users():
    return jsonify({
        "mapped_accounts": ACCOUNT_MAP,
        "total_tianchi_users": len(user_sequences),
    })


print("\n[3/3] Server ready!")
print("=" * 50)
print("Endpoints:")
print("  GET  /health    - Health check")
print("  POST /recommend - Recommend (body: {user_id: '...'} or {username: '...'})")
print("  GET  /users     - List demo users")
print(f"\nDemo accounts: {ACCOUNT_MAP}")
print("=" * 50)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
