<template>
  <div class="container reco-page">
    <nav class="crumb">
      <a @click="$router.push('/')">首页</a>
      <span>›</span>
      <span>AI 识物</span>
    </nav>

    <header class="reco-head">
      <h1>🤖 AI 智能识物</h1>
      <p>上传商品图片，AI 自动识别商品类别 — 基于 YOLOv8 深度学习模型</p>
    </header>

    <div class="reco-body">
      <!-- 上传区 -->
      <section class="upload-zone" v-if="!preview">
        <label class="drop-area" @dragover.prevent @drop.prevent="onDrop">
          <input type="file" accept="image/*" @change="onFile" hidden ref="fileInput" />
          <div class="drop-inner">
            <div class="drop-ico">📸</div>
            <h3>点击或拖拽上传商品图片</h3>
            <p>支持 JPG / PNG / WebP，单张不超过 10MB</p>
            <button type="button" class="drop-btn" @click="($refs.fileInput as any).click()">选择图片</button>
          </div>
        </label>
      </section>

      <!-- 预览 + 结果 -->
      <div class="result-layout" v-else>
        <!-- 左侧预览 -->
        <section class="preview-side">
          <div class="preview-box">
            <img :src="preview" alt="预览" />
            <button class="btn-reset" @click="reset">✕ 重新上传</button>
          </div>
        </section>

        <!-- 右侧结果 -->
        <section class="result-side">
          <!-- 模型选择 -->
          <div class="model-switch">
            <span
              v-for="m in models" :key="m.value"
              :class="{ on: model === m.value }"
              @click="model = m.value"
            >{{ m.label }}</span>
          </div>

          <button class="btn-detect" @click="detect" :disabled="detecting">
            <span v-if="!detecting">🔍 开始识别</span>
            <span v-else>⏳ 识别中...</span>
          </button>

          <!-- 结果列表 -->
          <div class="detections" v-if="results.length">
            <h3>识别结果（共 {{ results.length }} 件）</h3>
            <div class="det-card" v-for="d in results" :key="d.class_id">
              <div class="det-rank">
                <span class="det-conf">{{ (d.confidence * 100).toFixed(1) }}%</span>
                <div class="conf-bar"><i :style="{ width: (d.confidence * 100) + '%' }"></i></div>
              </div>
              <div class="det-info">
                <strong class="det-name">{{ d.class_name }}</strong>
                <span class="det-class-id">{{ d.source === 'snacks' ? '🍿 零食模型' : '🌐 通用模型' }} · class_id: {{ d.class_id }}</span>
              </div>
              <div class="det-actions">
                <button class="btn-search" @click="searchProduct(d.class_name)">🔍 搜同款</button>
              </div>
            </div>
          </div>

          <!-- 空结果 -->
          <div class="no-result" v-if="done && !results.length">
            <div class="no-ico">🤷</div>
            <p>AI 未能识别出商品</p>
            <span>请尝试更换更清晰的商品图片</span>
          </div>

          <!-- 错误 -->
          <div class="err-msg" v-if="errMsg">
            <span>⚠ {{ errMsg }}</span>
          </div>
        </section>
      </div>
    </div>

    <!-- 模型说明 -->
    <footer class="reco-footer">
      <div class="model-badge">
        <span class="mb-dot"></span> YOLOv8n · 伊朗零食数据集 19 类 · mAP50 = 0.992
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const fileInput = ref<HTMLInputElement | null>(null)
const preview = ref('')
const detecting = ref(false)
const done = ref(false)
const errMsg = ref('')
const results = ref<any[]>([])
const model = ref('coco')
const models = [
  { label: '🌐 通用', value: 'coco' },
  { label: '🍿 零食', value: 'snacks' },
  { label: '🔀 全部', value: 'both' },
]

function onFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) readFile(file)
}
function onDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (file) readFile(file)
}
function readFile(file: File) {
  if (file.size > 10 * 1024 * 1024) { errMsg.value = '图片不能超过 10MB'; return }
  const reader = new FileReader()
  reader.onload = () => {
    preview.value = reader.result as string
    errMsg.value = ''; results.value = []; done.value = false
  }
  reader.readAsDataURL(file)
}
function reset() {
  preview.value = ''
  results.value = []
  errMsg.value = ''
  done.value = false
}

async function detect() {
  if (!preview.value) return
  detecting.value = true; errMsg.value = ''; results.value = []; done.value = false

  try {
    // dataURL → Blob → FormData
    const blob = await fetch(preview.value).then(r => r.blob())
    const form = new FormData()
    form.append('image', blob, 'product.jpg')

    const res = await axios.post(`/yolo/detect?model=${model.value}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    })

    const data = res.data
    results.value = (data.detections || []).sort((a: any, b: any) => b.confidence - a.confidence)
  } catch (e: any) {
    errMsg.value = '识别失败：' + (e.message || '请确认 YOLO 服务已启动')
  } finally {
    detecting.value = false
    done.value = true
  }
}

function searchProduct(name: string) {
  // 跳转首页搜索该商品名
  router.push({ path: '/', query: { kw: encodeURIComponent(name) } })
}
</script>

<style scoped>
.reco-page { padding: 16px 20px 40px; }

.crumb {
  font-size: 13px; color: var(--text-muted);
  padding: 8px 0 14px;
  display: flex; align-items: center; gap: 8px;
}
.crumb a { color: var(--text-secondary); cursor: pointer; }
.crumb a:hover { color: var(--primary); }

.reco-head {
  text-align: center;
  padding: 24px 0 32px;
}
.reco-head h1 { font-size: 28px; font-weight: 800; color: var(--text-primary); }
.reco-head p { font-size: 14px; color: var(--text-muted); margin-top: 8px; }

/* 上传区 */
.upload-zone { max-width: 560px; margin: 0 auto; }
.drop-area {
  display: block;
  cursor: pointer;
}
.drop-inner {
  border: 2px dashed var(--border-strong);
  border-radius: var(--r-lg);
  padding: 56px 32px;
  text-align: center;
  transition: all 0.2s;
  background: var(--bg-soft);
}
.drop-inner:hover {
  border-color: var(--primary);
  background: var(--primary-bg);
}
.drop-ico { font-size: 56px; margin-bottom: 16px; }
.drop-inner h3 { font-size: 17px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.drop-inner p { font-size: 13px; color: var(--text-muted); margin-bottom: 20px; }
.drop-btn {
  padding: 10px 32px;
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  color: #fff;
  font-size: 14px; font-weight: 600;
  border-radius: var(--r-round);
  box-shadow: 0 4px 12px rgba(255,68,0,0.3);
  transition: all 0.2s;
}
.drop-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(255,68,0,0.4); }

/* 结果布局 */
.result-layout {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 32px;
  max-width: 960px;
  margin: 0 auto;
}
@media (max-width: 860px) { .result-layout { grid-template-columns: 1fr; } }

/* 预览 */
.preview-side { }
.preview-box {
  position: relative;
  border-radius: var(--r-md);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  background: #fff;
}
.preview-box img {
  width: 100%;
  max-height: 420px;
  object-fit: contain;
  background: #fafafa;
}
.btn-reset {
  position: absolute; top: 12px; right: 12px;
  padding: 6px 14px;
  background: rgba(0,0,0,0.55);
  color: #fff;
  font-size: 12px;
  border-radius: var(--r-round);
  backdrop-filter: blur(4px);
  transition: background 0.2s;
}
.btn-reset:hover { background: rgba(0,0,0,0.75); }

/* 模型切换 */
.model-switch {
  display: flex; gap: 6px;
  margin-bottom: 14px;
  padding: 4px;
  background: var(--bg-soft);
  border-radius: var(--r-md);
}
.model-switch span {
  flex: 1;
  padding: 8px 0;
  text-align: center;
  font-size: 13px; font-weight: 600;
  color: var(--text-muted);
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: all 0.2s;
}
.model-switch span:hover { color: var(--text-primary); }
.model-switch span.on {
  background: #fff;
  color: var(--primary);
  box-shadow: var(--shadow-sm);
}

/* 识别按钮 */
.btn-detect {
  width: 100%;
  height: 52px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 18px; font-weight: 700;
  border-radius: var(--r-md);
  box-shadow: 0 6px 16px rgba(102,126,234,0.35);
  transition: all 0.2s;
  margin-bottom: 24px;
}
.btn-detect:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(102,126,234,0.5); }
.btn-detect:disabled { opacity: 0.6; cursor: wait; }

/* 结果卡片 */
.detections h3 {
  font-size: 15px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 14px; padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}
.det-card {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 16px;
  background: #fff;
  border-radius: var(--r-md);
  box-shadow: var(--shadow-sm);
  margin-bottom: 10px;
  transition: all 0.2s;
}
.det-card:hover { box-shadow: var(--shadow-card); }

.det-rank { flex-shrink: 0; width: 72px; }
.det-conf { font-size: 16px; font-weight: 800; color: var(--primary); }
.conf-bar { height: 5px; background: var(--border-light); border-radius: 3px; margin-top: 4px; overflow: hidden; }
.conf-bar i { display: block; height: 100%; background: linear-gradient(90deg, var(--primary), var(--yellow)); border-radius: 3px; transition: width 0.4s; }

.det-info { flex: 1; min-width: 0; }
.det-name { font-size: 15px; font-weight: 600; color: var(--text-primary); display: block; }
.det-class-id { font-size: 11px; color: var(--text-muted); margin-top: 2px; display: block; }

.btn-search {
  padding: 7px 16px;
  background: var(--primary-bg);
  color: var(--primary);
  font-size: 12px; font-weight: 600;
  border-radius: var(--r-round);
  border: 1px solid var(--primary-light);
  white-space: nowrap;
  transition: all 0.2s;
}
.btn-search:hover { background: var(--primary); color: #fff; }

/* 空 / 错误 */
.no-result, .err-msg {
  text-align: center;
  padding: 40px 20px;
}
.no-ico { font-size: 48px; margin-bottom: 12px; }
.no-result p { font-size: 15px; color: var(--text-regular); }
.no-result span { font-size: 13px; color: var(--text-muted); }
.err-msg {
  padding: 16px;
  background: #FEF2F2;
  color: #DC2626;
  border-radius: var(--r-md);
  font-size: 13px;
}

/* 底部模型信息 */
.reco-footer {
  margin-top: 48px;
  text-align: center;
}
.model-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px;
  background: var(--bg-soft);
  border-radius: var(--r-round);
  font-size: 12px; color: var(--text-muted);
}
.mb-dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 6px #4ade80; }
</style>
