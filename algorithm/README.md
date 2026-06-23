# 🧠 算法推理层 — YOLO 商品识别

## 快速启动

```bash
cd algorithm
pip install -r requirements.txt

# 放置模型文件到 models/ 目录
mkdir models
# 将 yolov8n.pt / best.pt 放入 models/

# 启动推理服务
python app.py
# 或: uvicorn app:app --host 0.0.0.0 --port 5000
```

## ngrok 暴露公网

```bash
# 安装 ngrok (https://ngrok.com/download)
ngrok http 5000

# 复制生成的公网 URL，例如:
# https://abc123.ngrok-free.app
```

把 ngrok URL 告诉应用层，应用层会在 Gateway 配置中填入这个地址。

## API

### `GET /health`
健康检查，返回已加载的模型列表。

### `POST /detect`
单张图片目标检测。

| 参数 | 类型 | 说明 |
|------|------|------|
| `file` | multipart | 上传的图片文件 |
| `model` | query | 模型名，默认 `yolov8n`，可选 `snack` |
| `conf` | query | 置信度阈值，默认 0.25 |

**返回示例：**
```json
{
  "model": "yolov8n",
  "filename": "image.jpg",
  "detections": [
    {
      "class": "bottle",
      "confidence": 0.92,
      "bbox": [100.5, 200.3, 300.7, 450.1]
    }
  ]
}
```

## 模型

| 模型 | 文件 | 说明 |
|------|------|------|
| yolov8n | models/yolov8n.pt | YOLOv8 nano 通用检测 |
| snack | models/best.pt | 零食/商品定制模型 |
