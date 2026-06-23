"""
悦选AI — YOLO 商品识别推理服务
启动: uvicorn app:app --host 0.0.0.0 --port 5000
对外暴露: ngrok http 5000
"""
import io
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

# ── 全局模型引用 ──
model_store: dict[str, YOLO] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时预加载模型"""
    model_store["yolov8n"] = YOLO("models/yolov8n.pt")
    try:
        model_store["snack"] = YOLO("models/best.pt")  # 零食定制模型
    except Exception:
        print("[WARN] best.pt 未找到, 仅使用 yolov8n")
    print("[INFO] 模型加载完成:", list(model_store.keys()))
    yield


app = FastAPI(title="悦选 YOLO 推理服务", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "models": list(model_store.keys())}


@app.post("/detect")
async def detect(
    file: UploadFile = File(...),
    model: str = Query("yolov8n"),
    conf: float = Query(0.25, ge=0.01, le=1.0),
):
    """单张图片检测"""
    yolo = model_store.get(model)
    if yolo is None:
        return {"error": f"模型 {model} 不可用，可选: {list(model_store.keys())}"}

    # 读取上传的图片
    contents = await file.read()
    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)

    # 推理
    results = yolo(img, conf=conf)

    detections = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            detections.append({
                "class": r.names.get(cls_id, f"cls_{cls_id}"),
                "confidence": round(float(box.conf[0]), 4),
                "bbox": [round(float(x), 1) for x in box.xyxy[0].tolist()],
            })

    return {
        "model": model,
        "filename": file.filename,
        "detections": sorted(detections, key=lambda d: d["confidence"], reverse=True),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
