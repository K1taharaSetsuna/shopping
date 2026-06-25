<template>
  <div class="container detail" v-if="p">
    <!-- 面包屑 -->
    <nav class="crumb">
      <a @click="$router.push('/')">首页</a>
      <span>›</span>
      <a @click="$router.push('/?cat=' + encodeURIComponent(p.category))">{{ p.category }}</a>
      <span>›</span>
      <span class="ellipsis">{{ p.name }}</span>
    </nav>

    <div class="layout">
      <!-- 左：主图 + 缩略图 -->
      <div class="gallery">
        <div class="main-img">
          <ProductImage :image="thumbs[mainIdx]" :category="p.category" :name="p.name" radius="8px" />
          <div class="ribbon">悦选自营</div>
        </div>
        <div class="thumbs">
          <div
            v-for="(t, i) in thumbs" :key="i"
            class="thumb"
            :class="{ on: mainIdx === i }"
            @click="mainIdx = i"
          >
            <ProductImage :image="t" :category="p.category" :name="p.name" radius="4px" />
          </div>
          <div class="thumb more" v-if="!p.image"><span>更多图<br>暂无</span></div>
        </div>
        <div class="share">
          <span>💬 收藏</span><span>📤 分享</span><span>🛡️ 正品保障</span>
        </div>
      </div>

      <!-- 右：信息 -->
      <div class="info">
        <h1 class="title">{{ p.name }}</h1>
        <p class="desc">{{ p.description || '精选好物，品质之选。悦选严选，每一件都经过严格筛选，让您买得放心、用得舒心。' }}</p>

        <!-- 价格区 -->
        <div class="price-box">
          <div class="price-row">
            <span class="lbl">悦选价</span>
            <span class="big-price">{{ p.price }}</span>
            <span class="market" v-if="marketPrice">¥{{ marketPrice }}</span>
            <span class="discount-tag">打折</span>
          </div>
          <div class="price-meta">
            <span>月销 {{ p.reviewCount || 0 }}+件</span>
            <span>累计评价 {{ p.reviewCount || 0 }}</span>
            <span class="rating" v-if="p.rating">评分 ⭐{{ p.rating }}</span>
          </div>
        </div>

        <!-- 参数 -->
        <div class="props">
          <div class="prop"><span class="k">分类</span><span class="v">{{ p.category }}</span></div>
          <div class="prop"><span class="k">库存</span><span class="v" :class="{ out: p.stock <= 0 }">{{ p.stock > 0 ? p.stock + ' 件（现货）' : '暂时缺货' }}</span></div>
          <div class="prop"><span class="k">发货地</span><span class="v">广东 · 广州</span></div>
          <div class="prop"><span class="k">运费</span><span class="v" style="color:#22c55e">免运费 · 211 限时达</span></div>
        </div>

        <!-- 数量 + 购买 -->
        <div class="buy-row">
          <span class="lbl">数量</span>
          <div class="qty">
            <button @click="dec">-</button>
            <input v-model.number="qty" type="number" min="1" :max="p.stock||999" />
            <button @click="inc">+</button>
          </div>
          <span class="stock-tip">库存 {{ p.stock }} 件</span>
        </div>

        <div class="actions">
          <button class="btn-cart" @click="addCart" :disabled="p.stock <= 0">🛒 加入购物车</button>
          <button class="btn-buy" @click="buyNow" :disabled="p.stock <= 0">立即购买</button>
        </div>

        <!-- 服务保障 -->
        <div class="guarantee">
          <span>✅ 正品保障</span>
          <span>🔄 七天无理由</span>
          <span>⚡ 极速发货</span>
          <span>💳 安全支付</span>
        </div>
      </div>
    </div>

    <!-- 详情说明 -->
    <section class="detail-tabs">
      <nav class="tabs">
        <span :class="{ on: tab==='desc' }" @click="tab='desc'">商品详情</span>
        <span :class="{ on: tab==='review' }" @click="tab='review'">累计评价 {{ p.reviewCount || 0 }}</span>
      </nav>
      <div class="tab-desc" v-if="tab==='desc'">
        <h3>商品介绍</h3>
        <p>{{ p.description || '本商品由悦选严选，采用优质材料，工艺精良，品质有保障。适合日常使用，是您生活品质的好帮手。' }}</p>
        <ul class="param-list">
          <li><span>商品名称</span><span>{{ p.name }}</span></li>
          <li><span>商品分类</span><span>{{ p.category }}</span></li>
          <li><span>商品库存</span><span>{{ p.stock }} 件</span></li>
          <li><span>商品评分</span><span>⭐ {{ p.rating || '暂无' }}</span></li>
          <li><span>累计评价</span><span>{{ p.reviewCount || 0 }} 条</span></li>
        </ul>
      </div>
      <div class="tab-review" v-else>
        <div class="review-summary">
          <div class="rs-score">
            <strong>{{ (p.rating || 5).toFixed(1) }}</strong>
            <span>商品评分</span>
          </div>
          <div class="rs-bars">
            <div><span>好评</span><div class="bar"><i style="width:92%"></i></div><em>92%</em></div>
            <div><span>中评</span><div class="bar"><i style="width:6%"></i></div><em>6%</em></div>
            <div><span>差评</span><div class="bar"><i style="width:2%"></i></div><em>2%</em></div>
          </div>
        </div>
        <div class="review-list">
          <div class="review" v-for="(r, i) in mockReviews" :key="i">
            <div class="r-head">
              <span class="r-user">{{ r.user }}</span>
              <span class="r-stars">⭐⭐⭐⭐⭐</span>
            </div>
            <p class="r-body">{{ r.text }}</p>
            <div class="r-meta">{{ r.time }} · {{ r.sku }}</div>
          </div>
        </div>
      </div>
    </section>

    <transition name="toast">
      <div class="toast" v-if="msg">{{ msg }}</div>
    </transition>
  </div>

  <div v-else class="container loading">加载中...</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProductById, type Product } from '../api'
import { addToCart } from '../store/cart'
import ProductImage from '../components/ProductImage.vue'

const route = useRoute()
const router = useRouter()
const p = ref<Product | null>(null)
const qty = ref(1)
const mainIdx = ref(0)
const msg = ref('')
const tab = ref<'desc' | 'review'>('desc')

const thumbs = computed(() => {
  // 根据主图名生成 4 张缩略图（如 xiaomi-1.png → xiaomi-2/3/4.png）
  const base = p.value?.image || ''
  if (!base) return ['', '', '', '']
  const m = base.match(/^(.+?-)(\d+)(\.[^.]+)$/)
  if (!m) return [base, '', '', '']
  return [1,2,3,4].map(n => m[1] + n + m[3])
})

const marketPrice = computed(() => p.value ? Math.round(p.value.price * 1.18) : 0)

const _user = computed(() => {
  try { return JSON.parse(sessionStorage.getItem('yuexuan_user') || '')?.username } catch { return '' }
})

const mockReviews = [
  { user: '悦***选', text: '收到货了,质量非常好,包装精致,物流速度快,客服态度也很好,非常满意的一次购物体验!', time: '2026-06-15', sku: '默认规格' },
  { user: 'user***88', text: '性价比超高,比想象中要好,做工扎实,细节到位,会回购的。', time: '2026-06-10', sku: '默认规格' },
  { user: '匿名***客', text: '一直在悦选买,品质有保障,物流也快,好评!', time: '2026-06-02', sku: '默认规格' },
]

onMounted(async () => {
  try {
    const res: any = await getProductById(Number(route.params.id))
    p.value = res
  } catch (e) {}
})

function inc() { if (p.value && qty.value < (p.value.stock || 999)) qty.value++ }
function dec() { if (qty.value > 1) qty.value-- }

function addCart() {
  if (!p.value || p.value.stock <= 0) return
  addToCart(p.value.pid, p.value.name, p.value.price, p.value.category, p.value.image || '', qty.value)
  msg.value = '✅ 已加入购物车'
  setTimeout(() => msg.value = '', 1500)
}
function buyNow() {
  if (!p.value || p.value.stock <= 0) return
  addToCart(p.value.pid, p.value.name, p.value.price, p.value.category, p.value.image || '', qty.value)
  router.push('/cart')
}
</script>

<style scoped>
.detail { padding: 16px 20px 40px; }

.crumb {
  font-size: 13px; color: var(--text-muted);
  padding: 8px 0 14px;
  display: flex; align-items: center; gap: 8px;
}
.crumb a { color: var(--text-secondary); cursor: pointer; }
.crumb a:hover { color: var(--primary); }
.crumb span { color: var(--text-muted); }
.crumb .ellipsis { max-width: 320px; }

.layout {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 32px;
  background: #fff;
  padding: 24px;
  border-radius: var(--r-md);
  box-shadow: var(--shadow-card);
}

/* 左图 */
.gallery { position: sticky; top: 80px; }
.main-img { position: relative; width: 100%; }
.ribbon {
  position: absolute; left: -1px; top: 10px;
  background: var(--primary); color: #fff;
  padding: 3px 10px; font-size: 12px;
  border-radius: 0 999px 999px 0;
}
.thumbs {
  display: flex; gap: 10px; margin-top: 14px;
}
.thumb {
  width: 64px; height: 64px;
  border: 2px solid var(--border);
  border-radius: var(--r-sm);
  cursor: pointer; overflow: hidden;
  transition: border-color 0.2s;
}
.thumb.on { border-color: var(--primary); }
.thumb.more {
  display: grid; place-items: center;
  font-size: 12px; color: var(--text-muted);
  background: var(--bg-gray);
  text-align: center;
}
.share {
  display: flex; gap: 22px; margin-top: 18px;
  font-size: 13px; color: var(--text-secondary);
}
.share span { cursor: pointer; }
.share span:hover { color: var(--primary); }

/* 右信息 */
.info { display: flex; flex-direction: column; }
.title { font-size: 22px; font-weight: 700; color: var(--text-primary); line-height: 1.4; margin-bottom: 10px; }
.desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 18px; }

.price-box {
  background: linear-gradient(180deg, var(--primary-bg), #fff);
  padding: 18px 20px;
  border-radius: var(--r-md);
  margin-bottom: 20px;
}
.price-row { display: flex; align-items: baseline; gap: 12px; }
.lbl { color: var(--text-muted); font-size: 13px; }
.big-price {
  font-size: 34px; font-weight: 800; color: var(--primary);
  line-height: 1;
}
.big-price::before { content: '¥'; font-size: 18px; margin-right: 2px; }
.market { font-size: 14px; color: var(--text-muted); text-decoration: line-through; }
.discount-tag {
  background: var(--primary); color: #fff;
  font-size: 11px; padding: 2px 8px; border-radius: var(--r-sm);
}
.price-meta {
  display: flex; gap: 24px;
  margin-top: 12px;
  font-size: 13px; color: var(--text-secondary);
}
.price-meta .rating { color: var(--primary); }

/* 参数 */
.props {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 12px 24px;
  padding: 16px 0;
  border-top: 1px dashed var(--border);
  border-bottom: 1px dashed var(--border);
  margin-bottom: 18px;
}
.prop { display: flex; gap: 10px; font-size: 13px; }
.prop .k { color: var(--text-muted); width: 48px; }
.prop .v { color: var(--text-primary); }
.prop .v.out { color: #ccc; }

/* 数量 */
.buy-row {
  display: flex; align-items: center; gap: 14px;
  margin-bottom: 22px;
}
.buy-row .lbl { color: var(--text-muted); font-size: 13px; }
.qty { display: flex; border: 1px solid var(--border-strong); border-radius: var(--r-sm); overflow: hidden; }
.qty button {
  width: 32px; height: 32px;
  background: var(--bg-gray);
  font-size: 16px; color: var(--text-regular);
}
.qty button:hover { background: var(--border-light); }
.qty input {
  width: 50px; height: 32px;
  text-align: center;
  border: none; border-left: 1px solid var(--border-light);
  border-right: 1px solid var(--border-light);
  font-size: 14px;
}
.stock-tip { font-size: 12px; color: var(--text-muted); }

/* 购买按钮 */
.actions { display: flex; gap: 14px; margin-bottom: 20px; }
.btn-cart, .btn-buy {
  flex: 0 0 180px;
  height: 46px;
  border-radius: var(--r-md);
  font-size: 16px; font-weight: 700;
  border: 2px solid;
}
.btn-cart {
  background: #FFF6EE;
  border-color: var(--primary);
  color: var(--primary);
}
.btn-cart:hover { background: var(--primary-bg); }
.btn-buy {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}
.btn-buy:hover { background: var(--primary-hover); }
.btn-cart:disabled, .btn-buy:disabled { opacity: 0.5; cursor: not-allowed; }

.guarantee {
  display: flex; gap: 18px;
  font-size: 12px; color: var(--text-muted);
  flex-wrap: wrap;
}
.guarantee span { display: inline-flex; align-items: center; }

/* 详情 tabs */
.detail-tabs {
  margin-top: 24px;
  background: #fff;
  border-radius: var(--r-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
.tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  background: var(--bg-soft);
}
.tabs span {
  padding: 14px 28px;
  font-size: 15px; color: var(--text-regular);
  cursor: pointer; position: relative;
}
.tabs span.on { color: var(--primary); font-weight: 600; background: #fff; }
.tabs span.on::after {
  content: ''; position: absolute; left: 0; right: 0; bottom: -1px;
  height: 2px; background: var(--primary);
}
.tab-desc, .tab-review { padding: 24px 28px; }
.tab-desc h3 { font-size: 16px; margin-bottom: 14px; }
.tab-desc p { font-size: 14px; color: var(--text-regular); line-height: 1.8; margin-bottom: 20px; }
.param-list {
  border: 1px solid var(--border);
  border-radius: var(--r-md);
}
.param-list li {
  display: grid; grid-template-columns: 140px 1fr;
  padding: 12px 18px;
  font-size: 13px;
  border-bottom: 1px solid var(--border-light);
}
.param-list li:last-child { border-bottom: none; }
.param-list li span:first-child { color: var(--text-muted); }
.param-list li span:last-child { color: var(--text-primary); }

/* 评价 */
.review-summary {
  display: flex; gap: 40px;
  padding: 20px 24px;
  background: var(--bg-soft);
  border-radius: var(--r-md);
  margin-bottom: 20px;
}
.rs-score { text-align: center; }
.rs-score strong { display: block; font-size: 40px; color: var(--primary); font-weight: 800; }
.rs-score span { font-size: 13px; color: var(--text-muted); }
.rs-bars { flex: 1; display: flex; flex-direction: column; gap: 10px; justify-content: center; }
.rs-bars > div { display: flex; align-items: center; gap: 12px; font-size: 13px; }
.rs-bars > div span { width: 36px; color: var(--text-secondary); }
.rs-bars .bar { flex: 1; height: 8px; background: #eee; border-radius: 4px; overflow: hidden; }
.rs-bars .bar i { display: block; height: 100%; background: var(--primary); }
.rs-bars em { font-style: normal; color: var(--text-muted); width: 40px; }

.review-list { display: flex; flex-direction: column; gap: 18px; }
.review { padding-bottom: 18px; border-bottom: 1px dashed var(--border); }
.review:last-child { border-bottom: none; }
.r-head { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; }
.r-user { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.r-stars { font-size: 12px; }
.r-body { font-size: 14px; color: var(--text-regular); line-height: 1.7; }
.r-meta { font-size: 12px; color: var(--text-muted); margin-top: 6px; }

/* toast */
.toast {
  position: fixed; top: 90px; left: 50%; transform: translateX(-50%);
  background: rgba(0,0,0,0.85); color: #fff;
  padding: 12px 28px; border-radius: var(--r-md);
  font-size: 14px; z-index: 9999;
}
.toast-enter-active, .toast-leave-active { transition: all 0.25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, -10px); }

.loading { padding: 80px; text-align: center; color: var(--text-muted); }
</style>