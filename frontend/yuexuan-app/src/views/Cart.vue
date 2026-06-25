<template>
  <div class="container cart-page">
    <header class="page-head">
      <h2>购物车 <small v-if="cart.items.length">（{{ totalCount }} 件商品）</small></h2>
      <router-link to="/" class="go-buy">继续购物 ›</router-link>
    </header>

    <!-- 空购物车 -->
    <div v-if="!cart.items.length" class="empty">
      <div class="empty-ico">🛒</div>
      <p>购物车还是空的</p>
      <span>快去挑几件心仪的好物吧</span>
      <router-link to="/" class="cta">去逛逛</router-link>
    </div>

    <template v-else>
      <!-- 列表头 -->
      <div class="cart-head">
        <label class="col-check">
          <input type="checkbox" :checked="allSelected" @change="toggleAll()" /> 全选
        </label>
        <span class="col-info">商品信息</span>
        <span class="col-price">单价</span>
        <span class="col-qty">数量</span>
        <span class="col-sub">小计</span>
        <span class="col-op">操作</span>
      </div>

      <!-- 列表 -->
      <div class="cart-body">
        <div class="cart-row" v-for="item in cart.items" :key="item.pid">
          <label class="col-check">
            <input type="checkbox" :checked="item.selected" @change="toggleSelect(item.pid)" />
          </label>
          <div class="col-info" @click="$router.push(`/product/${item.pid}`)">
            <div class="thumb">
              <ProductImage :image="item.image" :category="item.category" :name="item.name" radius="4px" />
            </div>
            <div class="meta">
              <h4 class="ellipsis-2">{{ item.name }}</h4>
              <span class="cat">{{ item.category }}</span>
            </div>
          </div>
          <div class="col-price">{{ item.price }}</div>
          <div class="col-qty">
            <div class="qty">
              <button @click="updateQty(item.pid, item.qty - 1)" :disabled="item.qty <= 1">-</button>
              <input :value="item.qty" @change="onQtyChange(item.pid, $event)" />
              <button @click="updateQty(item.pid, item.qty + 1)">+</button>
            </div>
          </div>
          <div class="col-sub">{{ (item.price * item.qty).toFixed(0) }}</div>
          <div class="col-op">
            <span @click="removeFromCart(item.pid)">删除</span>
            <span>移入收藏</span>
          </div>
        </div>
      </div>

      <!-- 结算条 -->
      <div class="settle-bar">
        <label class="col-check">
          <input type="checkbox" :checked="allSelected" @change="toggleAll()" /> 全选
        </label>
        <span class="del-all" @click="clearAll">清空购物车</span>
        <div class="settle-right">
          <span class="sel-info">已选 <b>{{ selCount }}</b> 件</span>
          <span class="total">合计 <em>{{ total.toFixed(0) }}</em></span>
          <button class="btn-checkout" :disabled="selCount === 0" @click="goConfirm">
            结 算
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  cart, selectedItems, totalPrice, toggleAll, toggleSelect,
  updateQty, removeFromCart,
} from '../store/cart'
import ProductImage from '../components/ProductImage.vue'

const router = useRouter()

const selCount = computed(() => selectedItems().reduce((s, i) => s + i.qty, 0))
const total = computed(() => totalPrice())
const totalCount = computed(() => cart.items.reduce((s, i) => s + i.qty, 0))
const allSelected = computed(() => cart.items.length > 0 && cart.items.every(i => i.selected))

function onQtyChange(pid: number, e: Event) {
  const v = Number((e.target as HTMLInputElement).value)
  if (v > 0) updateQty(pid, v)
}

function clearAll() {
  if (confirm('确认清空购物车吗？')) {
    cart.items = []; localStorage.setItem('yuexuan_cart', '[]')
  }
}

function goConfirm() {
  if (selCount.value === 0) return
  router.push('/confirm')
}
</script>

<style scoped>
.cart-page { padding: 16px 20px 40px; }

.page-head {
  display: flex; align-items: baseline; justify-content: space-between;
  margin: 8px 0 16px;
}
.page-head h2 { font-size: 22px; font-weight: 700; }
.page-head h2 small { font-size: 14px; color: var(--text-muted); font-weight: 400; margin-left: 6px; }
.go-buy { color: var(--primary); font-size: 14px; }

/* 空 */
.empty {
  background: #fff; border-radius: var(--r-md); box-shadow: var(--shadow-card);
  text-align: center; padding: 80px 20px;
}
.empty-ico { font-size: 70px; margin-bottom: 18px; opacity: 0.5; }
.empty p { font-size: 18px; color: var(--text-primary); margin-bottom: 6px; }
.empty span { font-size: 13px; color: var(--text-muted); display: block; margin-bottom: 24px; }
.empty .cta {
  display: inline-block;
  padding: 10px 36px;
  background: var(--primary); color: #fff;
  border-radius: var(--r-round); font-size: 15px; font-weight: 600;
}

/* 列表头 */
.cart-head, .cart-row {
  display: grid;
  grid-template-columns: 80px 1fr 120px 150px 120px 80px;
  align-items: center;
}
.cart-head {
  background: #fff;
  border-radius: var(--r-md) var(--r-md) 0 0;
  padding: 14px 16px;
  font-size: 13px; color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}
.col-check { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.col-price, .col-sub { text-align: center; }

/* 列表体 */
.cart-body { background: #fff; }
.cart-row {
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
}
.cart-row:last-child { border-bottom: none; border-radius: 0 0 var(--r-md) var(--r-md); }

.col-info { display: flex; gap: 12px; cursor: pointer; min-width: 0; }
.col-info .thumb { width: 84px; height: 84px; flex-shrink: 0; }
.col-info .meta { display: flex; flex-direction: column; justify-content: center; gap: 6px; min-width: 0; }
.col-info h4 { font-size: 14px; font-weight: 500; color: var(--text-primary); line-height: 1.4; }
.col-info:hover h4 { color: var(--primary); }
.col-info .cat { font-size: 12px; color: var(--text-muted); }

.col-price {
  color: var(--text-primary); font-size: 15px; font-weight: 600; text-align: center;
}
.col-price::before { content: '¥'; font-size: 12px; color: var(--text-secondary); margin-right: 2px; }
.col-sub { color: var(--primary); font-size: 17px; font-weight: 700; text-align: center; }
.col-sub::before { content: '¥'; font-size: 13px; margin-right: 1px; }

.qty {
  display: flex; justify-content: center;
  border: 1px solid var(--border-strong);
  border-radius: var(--r-sm);
  width: 110px; margin: 0 auto;
  overflow: hidden;
}
.qty button {
  width: 30px; height: 32px;
  background: var(--bg-gray);
  font-size: 16px; color: var(--text-regular);
}
.qty button:hover:not(:disabled) { background: var(--border-light); color: var(--primary); }
.qty button:disabled { color: #ccc; cursor: not-allowed; }
.qty input {
  width: 48px; height: 32px;
  text-align: center; border: none;
  border-left: 1px solid var(--border-light);
  border-right: 1px solid var(--border-light);
  font-size: 13px;
}
/* 隐藏 input number 上下箭头 */
.qty input::-webkit-outer-spin-button,
.qty input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }

.col-op { display: flex; flex-direction: column; gap: 8px; align-items: center; font-size: 12px; color: var(--text-muted); }
.col-op span { cursor: pointer; }
.col-op span:hover { color: var(--primary); }

/* input checkbox 美化 */
input[type="checkbox"] {
  width: 16px; height: 16px;
  accent-color: var(--primary);
  cursor: pointer;
}

/* 结算条 */
.settle-bar {
  display: flex; align-items: center; gap: 20px;
  background: #fff;
  border-radius: var(--r-md);
  padding: 12px 20px;
  margin-top: 16px;
  box-shadow: var(--shadow-card);
  position: sticky; bottom: 16px;
}
.del-all { color: var(--text-secondary); font-size: 13px; cursor: pointer; }
.del-all:hover { color: var(--primary); }
.settle-right {
  margin-left: auto;
  display: flex; align-items: center; gap: 24px;
}
.sel-info { font-size: 14px; color: var(--text-regular); }
.sel-info b { color: var(--primary); margin: 0 2px; }
.total { font-size: 14px; color: var(--text-regular); }
.total em {
  font-style: normal;
  font-size: 24px; font-weight: 800; color: var(--primary);
  margin-left: 4px;
}
.total em::before { content: '¥'; font-size: 14px; }
.btn-checkout {
  height: 48px; padding: 0 48px;
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  color: #fff;
  font-size: 18px; font-weight: 700; letter-spacing: 4px;
  border-radius: var(--r-round);
  box-shadow: 0 4px 12px rgba(255,68,0,0.3);
  transition: all 0.2s;
}
.btn-checkout:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(255,68,0,0.4); }
.btn-checkout:disabled { opacity: 0.4; cursor: not-allowed; background: #ccc; box-shadow: none; }
</style>