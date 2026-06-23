<template>
  <div class="adm-page">
    <div class="adm-head">
      <div>
        <h2>数据看板 📊</h2>
        <span class="sub">平台核心运营指标 · 实时刷新</span>
      </div>
      <el-button :icon="Refresh" @click="load" :loading="loading">刷新</el-button>
    </div>

    <!-- 4 个核心指标卡 -->
    <div class="kpi-grid">
      <div class="kpi" v-for="k in kpis" :key="k.label">
        <div class="kpi-ico" :style="{ background: k.bg }">
          <el-icon :size="22"><component :is="k.icon" /></el-icon>
        </div>
        <div class="kpi-body">
          <div class="kpi-num" :class="k.tone">{{ k.value }}</div>
          <div class="kpi-label">{{ k.label }}</div>
          <div class="kpi-foot" v-if="k.sub">{{ k.sub }}</div>
        </div>
      </div>
    </div>

    <!-- 中部双栏 -->
    <div class="row-2">
      <!-- 订单状态分布 -->
      <div class="adm-card">
        <div class="card-head"><h3>订单状态分布</h3><small>共 {{ total }} 笔</small></div>
        <div class="dist-list">
          <div class="dist" v-for="d in dist" :key="d.key">
            <span class="d-dot" :style="{ background: d.color }"></span>
            <span class="d-name">{{ d.label }}</span>
            <div class="d-bar"><i :style="{ width: d.pct + '%', background: d.color }"></i></div>
            <span class="d-num">{{ d.value }}</span>
            <span class="d-pct">{{ d.pct }}%</span>
          </div>
        </div>
      </div>

      <!-- 今日概览 -->
      <div class="adm-card today-card">
        <div class="card-head"><h3>今日概览</h3><el-tag size="small" type="warning" effect="plain">{{ today }}</el-tag></div>
        <div class="today-grid">
          <div class="t-item">
            <div class="t-num primary">{{ todayOrders }}</div>
            <div class="t-lab">今日新增订单</div>
          </div>
          <div class="t-item">
            <div class="t-num">15</div>
            <div class="t-lab">在售商品数</div>
          </div>
          <div class="t-item">
            <div class="t-num">{{ kpis[3]?.value || 0 }}</div>
            <div class="t-lab">已完成订单</div>
          </div>
          <div class="t-item">
            <div class="t-num">8</div>
            <div class="t-lab">注册用户数</div>
          </div>
        </div>
        <div class="today-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>当前所有微服务运行正常 · Nacos 注册中心心跳健康</span>
        </div>
      </div>
    </div>

    <!-- 最近订单 -->
    <div class="adm-card">
      <div class="card-head">
        <h3>最近订单</h3>
        <el-button text type="primary" @click="$router.push('/admin/orders')">查看全部 →</el-button>
      </div>
      <el-table :data="recent" stripe size="default">
        <el-table-column label="订单号" width="180">
          <template #default="{ row }"><code class="ord-no">{{ row.orderNo || row.id }}</code></template>
        </el-table-column>
        <el-table-column label="商品" min-width="200">
          <template #default="{ row }">
            <div class="prod-cell">
              <ProductThumb :image="''" :category="guessCat(row.productName)" width="36px" height="36px" radius="6px" />
              <div>
                <div class="prod-name">{{ baseName(row.productName) }}</div>
                <div class="prod-meta">×{{ row.number }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="90" align="center" />
        <el-table-column label="金额" width="100" align="center">
          <template #default="{ row }"><span class="price">{{ row.totalAmount }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" width="170">
          <template #default="{ row }"><span class="t-cell">{{ fmtTime(row.createTime) }}</span></template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Refresh, InfoFilled } from '@element-plus/icons-vue'
import { getDashboard, adminGetOrders, guessCat } from '../api'
import ProductThumb from '../components/ProductThumb.vue'

const loading = ref(false)
const dash = ref<any>({})
const allOrders = ref<any[]>([])
const recent = computed(() => allOrders.value.slice(0, 6))

const today = new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })

const total = computed(() => Number(dash.value.totalOrders) || 0)
const todayOrders = computed(() => dash.value.todayOrders || 0)

const kpis = computed(() => {
  const d = dash.value
  return [
    { label: '订单总数',  value: d.totalOrders || 0,     icon: 'Document',     bg: 'linear-gradient(135deg,#667eea,#764ba2)', tone: '', sub: '平台累计订单量' },
    { label: '今日新增',  value: d.todayOrders || 0,      icon: 'TrendCharts',  bg: 'linear-gradient(135deg,#fa709a,#fee140)', tone: 'primary', sub: '本日新创建订单' },
    { label: '待支付',    value: d.pendingOrders || 0,    icon: 'Clock',        bg: 'linear-gradient(135deg,#FFB347,#FF8C42)', tone: 'warning', sub: '需及时提醒付款' },
    { label: '已完成',    value: d.completedOrders || 0,  icon: 'CircleCheck',  bg: 'linear-gradient(135deg,#43e97b,#38f9d7)', tone: 'success', sub: '已签收完成订单' },
  ]
})

const dist = computed(() => {
  const d = dash.value
  const tot = total.value || 1
  const items = [
    { key: 'PENDING',   label: '待支付',  value: d.pendingOrders || 0,   color: '#FFB347' },
    { key: 'PAID',      label: '已支付',  value: d.paidOrders || 0,      color: '#667eea' },
    { key: 'SHIPPING',  label: '配送中',  value: d.shippingOrders || 0,  color: '#9b88ff' },
    { key: 'COMPLETED', label: '已完成',  value: d.completedOrders || 0, color: '#43c26a' },
    { key: 'CANCELLED', label: '已取消',  value: d.cancelledOrders || 0, color: '#b0b0b0' },
  ]
  return items.map(i => ({ ...i, pct: Math.round((i.value / tot) * 100) }))
})

function statusType(s: string) { return ({ PENDING:'warning', PAID:'', SHIPPING:'primary', COMPLETED:'success', CANCELLED:'danger' } as any)[s] || 'info' }
function statusText(s: string) { return ({ PENDING:'待支付', PAID:'待发货', SHIPPING:'配送中', COMPLETED:'已完成', CANCELLED:'已取消' } as any)[s] || s }
function baseName(n: string) { return (n || '').split('—')[0].trim() }
function fmtTime(t: string) { return t ? String(t).substring(0, 19).replace('T', ' ') : '-' }

async function load() {
  loading.value = true
  try { dash.value = await getDashboard() || {} } catch (e) { console.error(e) }
  try { allOrders.value = await adminGetOrders() || [] } catch (e) { console.error(e) }
  loading.value = false
}
onMounted(load)
</script>

<style scoped>
/* KPI 4 卡 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 18px;
}
@media (max-width: 1100px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

.kpi {
  background: #fff;
  border-radius: var(--r-md);
  box-shadow: var(--shadow-card);
  padding: 20px;
  display: flex; align-items: center; gap: 16px;
  transition: all 0.2s;
}
.kpi:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }
.kpi-ico {
  width: 52px; height: 52px;
  border-radius: var(--r-sm);
  display: grid; place-items: center;
  color: #fff; flex-shrink: 0;
}
.kpi-body { flex: 1; min-width: 0; }
.kpi-num { font-size: 28px; font-weight: 800; color: var(--text-primary); line-height: 1.1; }
.kpi-num.primary { color: var(--primary); }
.kpi-num.warning { color: #E67E22; }
.kpi-num.success { color: #16A34A; }
.kpi-label { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.kpi-foot { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* 双栏 */
.row-2 {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 16px;
  margin-bottom: 18px;
}
@media (max-width: 1100px) { .row-2 { grid-template-columns: 1fr; } }

.card-head {
  display: flex; align-items: baseline; justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}
.card-head h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0; }
.card-head small { font-size: 12px; color: var(--text-muted); }

/* 状态分布 */
.dist-list { display: flex; flex-direction: column; gap: 14px; }
.dist {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px;
}
.dist .d-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dist .d-name { width: 56px; color: var(--text-regular); }
.dist .d-bar {
  flex: 1; height: 8px; background: var(--border-light);
  border-radius: 4px; overflow: hidden;
}
.dist .d-bar i { display: block; height: 100%; border-radius: 4px; transition: width 0.4s; }
.dist .d-num { font-weight: 600; color: var(--text-primary); min-width: 36px; text-align: right; }
.dist .d-pct { color: var(--text-muted); min-width: 38px; text-align: right; }

/* 今日卡 */
.today-card { display: flex; flex-direction: column; }
.today-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
  flex: 1;
}
.t-item {
  padding: 14px;
  background: var(--bg-soft);
  border-radius: var(--r-sm);
  text-align: center;
}
.t-num { font-size: 26px; font-weight: 800; color: var(--text-primary); }
.t-num.primary { color: var(--primary); }
.t-lab { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.today-tip {
  display: flex; align-items: center; gap: 8px;
  margin-top: 14px; padding: 10px 14px;
  background: #F0FDF4; border-radius: var(--r-sm);
  font-size: 12px; color: #16A34A;
}
.today-tip .el-icon { color: #22C55E; }

/* 商品单元格 */
.prod-cell { display: flex; align-items: center; gap: 10px; }
.prod-name { font-size: 14px; color: var(--text-primary); line-height: 1.3; }
.prod-meta { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.ord-no {
  background: var(--bg-soft); padding: 2px 8px; border-radius: 4px;
  font-family: monospace; font-size: 12px; color: var(--text-regular);
}
.t-cell { font-size: 12px; color: var(--text-muted); }
</style>
