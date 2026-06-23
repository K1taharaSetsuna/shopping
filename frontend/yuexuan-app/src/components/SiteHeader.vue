<template>
  <header class="site-header">
    <!-- 顶部窄条 -->
    <div class="top-bar">
      <div class="container top-bar-inner">
        <span>欢迎来到悦选 · 你的智能购物伙伴</span>
        <nav class="top-links">
          <a v-if="isAdmin" @click="$router.push('/admin/dashboard')" class="admin-link">⚙ 管理后台</a>
          <router-link to="/recognize" class="ai-link">🤖 AI 识物</router-link>
          <router-link to="/orders">我的订单</router-link>
          <router-link to="/cart">购物车</router-link>
          <a v-if="user" @click="logout" class="user">👤 {{ user }} · 退出</a>
          <router-link v-else to="/login">请登录</router-link>
        </nav>
      </div>
    </div>

    <!-- 主体：logo + 搜索 + 头部按钮 -->
    <div class="container header-main">
      <router-link to="/" class="logo">
        <span class="logo-mark">悦</span>
        <span class="logo-text">
          <strong>悦选</strong>
          <small>YUE SELECT</small>
        </span>
      </router-link>

      <div class="search">
        <div class="search-box">
          <input
            v-model="kw"
            placeholder="搜索你想要的商品"
            @keyup.enter="onSearch"
            @focus="showHist = true"
            @blur="showHist = false"
          />
          <button class="search-btn" @click="onSearch">搜 — 索</button>
        </div>
        <div class="hot-words">
          <span v-for="(h, i) in hotWords" :key="i" @click="$router.push('/?kw=' + encodeURIComponent(h))">{{ h }}</span>
        </div>
        <transition name="fade">
          <ul v-if="showHist && histories.length" class="search-hist">
            <li v-for="(h, i) in histories" :key="i" @click="$router.push('/?kw=' + encodeURIComponent(h))">
              <span>{{ h }}</span><em @click.stop="delHist(i)">×</em>
            </li>
          </ul>
        </transition>
      </div>

      <div class="header-actions">
        <router-link to="/cart" class="cart-btn">
          🛒 购物车
          <span class="cart-badge" v-if="count">{{ count }}</span>
        </router-link>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { cartCount } from '../store/cart'

const router = useRouter()
const route = useRoute()
const kw = ref('')
const showHist = ref(false)
const hotWords = ref(['跑鞋', 'T恤', '蓝牙耳机', '智能手表', '坚果零食', '台灯'])

const user = computed(() => {
  try { return JSON.parse(sessionStorage.getItem('yuexuan_user') || '')?.username } catch { return '' }
})
const isAdmin = computed(() => {
  try {
    const role = JSON.parse(sessionStorage.getItem('yuexuan_user') || '{}')?.role || ''
    return ['shop', 'admin', 'platform'].includes(role)
  } catch { return false }
})

function logout() {
  sessionStorage.removeItem('yuexuan_token')
  sessionStorage.removeItem('yuexuan_user')
  router.push('/login')
}

// 购物车实时角标
function get() { return cartCount() }
const count = ref(get())
let stop: any = null
onMounted(async () => {
  const { watchEffect } = await import('vue')
  stop = watchEffect(() => { count.value = get() })
})
onUnmounted(() => { stop?.() })

// 搜索历史（localStorage）
const HIST_KEY = 'yuexuan_search_hist'
const histories = ref<string[]>(loadHist())
function loadHist(): string[] { try { return JSON.parse(localStorage.getItem(HIST_KEY) || '[]') } catch { return [] } }
function saveHist(h: string[]) { localStorage.setItem(HIST_KEY, JSON.stringify(h)) }
function pushHist(w: string) {
  if (!w) return
  let h = loadHist().filter(x => x !== w)
  h.unshift(w)
  if (h.length > 8) h = h.slice(0, 8)
  saveHist(h); histories.value = h
}
function delHist(i: number) {
  const h = histories.value.slice()
  h.splice(i, 1); saveHist(h); histories.value = h
}

function onSearch() {
  const w = kw.value.trim()
  pushHist(w)
  // Home 通过 query 读取关键词并自动 load
  router.push('/?kw=' + encodeURIComponent(w))
}

// 外部跳转带 kw 时回填输入框
watch(() => route.query.kw, (v) => {
  if (typeof v === 'string') kw.value = decodeURIComponent(v)
}, { immediate: true })
</script>

<style scoped>
.site-header {
  background: #fff;
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 100;
}

/* 顶部条 */
.top-bar {
  background: #3c3c3c;
  color: #d0d0d0;
  font-size: 12px;
  height: 32px;
  line-height: 32px;
}
.top-bar-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.top-links { display: flex; gap: 18px; align-items: center; }
.top-links a { cursor: pointer; }
.top-links a:hover { color: #fff; }
.top-links .user { color: var(--yellow); }
.top-links .admin-link { color: #FFD500; font-weight: 600; }
.top-links .ai-link { color: #4ade80; font-weight: 600; }
.top-links .ai-link:hover { color: #86efac; }

/* 主区 */
.header-main {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 18px 20px;
}

/* logo */
.logo { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.logo-mark {
  width: 44px; height: 44px;
  background: linear-gradient(135deg, var(--primary), var(--yellow));
  color: #fff;
  font-size: 26px; font-weight: 800;
  display: grid; place-items: center;
  border-radius: var(--r-md);
  box-shadow: 0 4px 10px rgba(255,68,0,0.3);
}
.logo-text { display: flex; flex-direction: column; line-height: 1.1; }
.logo-text strong { font-size: 22px; font-weight: 800; color: #1a1a1a; }
.logo-text small { font-size: 10px; color: var(--primary); letter-spacing: 2px; }

/* 搜索 */
.search { flex: 1; max-width: 560px; position: relative; }
.search-box {
  display: flex;
  border: 2px solid var(--primary);
  border-radius: var(--r-round);
  overflow: hidden;
  background: #fff;
}
.search-box input {
  flex: 1;
  padding: 9px 18px;
  border: none;
  font-size: 14px;
  background: transparent;
}
.search-btn {
  padding: 0 28px;
  background: linear-gradient(135deg, var(--primary), var(--yellow));
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 4px;
}
.hot-words {
  display: flex; gap: 14px;
  margin-top: 6px; padding: 0 18px;
  font-size: 12px; color: var(--text-muted);
}
.hot-words span { cursor: pointer; }
.hot-words span:hover { color: var(--primary); }

.search-hist {
  position: absolute;
  top: calc(100% + 4px);
  left: 0; right: 0;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-md);
  padding: 6px 0;
  z-index: 20;
}
.search-hist li {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 18px;
  font-size: 13px; color: var(--text-regular);
  cursor: pointer;
}
.search-hist li:hover { background: var(--bg-gray); }
.search-hist em {
  width: 18px; height: 18px;
  text-align: center; line-height: 18px;
  color: var(--text-muted);
  border-radius: 50%;
  font-style: normal;
  font-size: 14px;
}
.search-hist em:hover { background: #eee; color: #333; }

/* 购物车按钮 */
.header-actions { margin-left: auto; }
.cart-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 9px 22px;
  border: 1px solid var(--border-strong);
  border-radius: var(--r-round);
  font-size: 14px;
  color: var(--text-regular);
  transition: all 0.2s;
}
.cart-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.cart-badge {
  background: var(--primary);
  color: #fff;
  font-size: 11px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: var(--r-round);
  display: inline-flex; align-items: center; justify-content: center;
  font-weight: 700;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>