<template>
  <div class="adm-page">
    <div class="adm-head">
      <div>
        <h2>订单管理 🚚</h2>
        <span class="sub">查看全部订单 · 处理发货流转 · 共 {{ allOrders.length }} 笔</span>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button>
    </div>

    <!-- 状态筛选 -->
    <div class="adm-card filter-card">
      <el-tabs v-model="activeStatus" class="status-tabs">
        <el-tab-pane v-for="s in statusesWithCount" :key="s.value" :name="s.value">
          <template #label>
            <span class="tab-label">
              {{ s.label }}
              <em class="tab-count" :class="{ on: s.value === activeStatus }" v-if="s.count > 0">{{ s.count }}</em>
            </span>
          </template>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 订单表格 -->
    <div class="adm-card table-card">
      <el-table :data="orders" stripe v-loading="loading" size="default">
        <el-table-column prop="id" label="#" width="56" align="center" />
        <el-table-column label="订单号" width="180">
          <template #default="{ row }"><code class="ord-no">{{ row.orderNo || row.id }}</code></template>
        </el-table-column>

        <el-table-column label="商品" min-width="220">
          <template #default="{ row }">
            <div class="prod-cell">
              <ProductThumb :image="''" :category="guessCat(row.productName)" :name="row.productName" width="44px" height="44px" radius="6px" />
              <div class="prod-info">
                <div class="prod-name">{{ baseName(row.productName) }}</div>
                <div class="prod-meta">×{{ row.number }} · 单价 ¥{{ row.productPrice }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="username" label="用户" width="90" align="center" />

        <el-table-column label="金额" width="110" align="center">
          <template #default="{ row }"><span class="price">{{ row.totalAmount }}</span></template>
        </el-table-column>

        <el-table-column label="收货信息" min-width="200">
          <template #default="{ row }">
            <div class="rcv">
              <div class="rcv-name"><el-icon><User /></el-icon> {{ row.receiverName || '-' }}</div>
              <div class="rcv-phone"><el-icon><Phone /></el-icon> {{ row.receiverPhone || '-' }}</div>
              <div class="rcv-addr"><el-icon><Location /></el-icon> {{ row.address || '-' }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="下单时间" width="170">
          <template #default="{ row }"><span class="t-cell">{{ fmtTime(row.createTime) }}</span></template>
        </el-table-column>

        <el-table-column label="操作" width="110" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'PAID'"
              type="primary" size="small" :icon="Van"
              @click="handleShip(row)"
            >发货</el-button>
            <el-tag v-else-if="row.status === 'SHIPPING'" type="primary" size="small" effect="plain">待收货</el-tag>
            <el-tag v-else-if="row.status === 'COMPLETED'" type="success" size="small" effect="plain">已签收</el-tag>
            <el-tag v-else-if="row.status === 'CANCELLED'" type="info" size="small" effect="plain">已取消</el-tag>
            <span v-else class="no-op">待付款</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div class="empty" v-if="!loading && !orders.length">
        <div class="empty-ico">📭</div>
        <p>{{ activeStatus ? '该状态下暂无订单' : '暂无订单' }}</p>
      </div>
    </div>

    <!-- 状态图例 -->
    <div class="legend">
      <span>状态流转：</span>
      <el-tag size="small" type="warning" effect="light">待支付</el-tag>
      <span class="arrow">→</span>
      <el-tag size="small" effect="light">已支付/待发货</el-tag>
      <span class="arrow">→</span>
      <el-tag size="small" type="primary" effect="light">配送中</el-tag>
      <span class="arrow">→</span>
      <el-tag size="small" type="success" effect="light">已完成</el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Van } from '@element-plus/icons-vue'
import { adminGetOrders, adminShipOrder, guessCat } from '../api'
import ProductThumb from '../components/ProductThumb.vue'

const loading = ref(false)
const activeStatus = ref('')
const allOrders = ref<any[]>([])

const statuses = [
  { label: '全部',   value: '' },
  { label: '待支付', value: 'PENDING' },
  { label: '待发货', value: 'PAID' },
  { label: '配送中', value: 'SHIPPING' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '已取消', value: 'CANCELLED' },
]

const statusCounts = computed<Record<string, number>>(() => {
  const map: Record<string, number> = {}
  allOrders.value.forEach(o => { map[o.status] = (map[o.status] || 0) + 1 })
  return { '': allOrders.value.length, ...map }
})
const statusesWithCount = computed(() =>
  statuses.map(s => ({ ...s, count: statusCounts.value[s.value] || 0 }))
)

const orders = computed(() => {
  if (!activeStatus.value) return allOrders.value
  return allOrders.value.filter(o => o.status === activeStatus.value)
})

function statusType(s: string) { return ({ PENDING:'warning', PAID:'', SHIPPING:'primary', COMPLETED:'success', CANCELLED:'danger' } as any)[s] || 'info' }
function statusText(s: string) { return ({ PENDING:'待支付', PAID:'待发货', SHIPPING:'配送中', COMPLETED:'已完成', CANCELLED:'已取消' } as any)[s] || s }
function baseName(n: string) { return (n || '').split('—')[0].trim() }
function fmtTime(t: string) { return t ? String(t).substring(0, 19).replace('T', ' ') : '-' }

async function load() {
  loading.value = true
  try { allOrders.value = await adminGetOrders() || [] }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function handleShip(row: any) {
  try {
    await ElMessageBox.confirm(`确认对订单「${row.orderNo || row.id}」执行发货吗？`, '确认发货', {
      type: 'warning', confirmButtonText: '确认发货', cancelButtonText: '取消'
    })
    await adminShipOrder(row.id)
    ElMessage.success('发货成功，订单已进入配送中')
    load()
  } catch (e) { /* 取消 */ }
}

onMounted(load)
</script>

<style scoped>
.filter-card { padding: 0 22px; margin-bottom: 16px; }
.status-tabs :deep(.el-tabs__header) { margin: 0 0 8px; }
.tab-label {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 14px;
}
.tab-count {
  font-style: normal;
  background: var(--border-light);
  color: var(--text-secondary);
  font-size: 11px; font-weight: 700;
  padding: 0 8px; border-radius: 999px; min-width: 22px; text-align: center;
}
.tab-count.on { background: var(--primary); color: #fff; }

.table-card { padding: 8px 16px 16px; }

.prod-cell { display: flex; align-items: center; gap: 12px; }
.prod-info { min-width: 0; }
.prod-name { font-size: 14px; font-weight: 500; color: var(--text-primary); line-height: 1.3; }
.prod-meta { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.rcv { display: flex; flex-direction: column; gap: 3px; line-height: 1.4; }
.rcv > div {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--text-regular);
}
.rcv > div .el-icon { font-size: 12px; color: var(--text-muted); flex-shrink: 0; }
.rcv-name { font-weight: 500; color: var(--text-primary) !important; }
.rcv-phone, .rcv-addr { color: var(--text-muted); }

.ord-no {
  background: var(--bg-soft); padding: 2px 8px; border-radius: 4px;
  font-family: monospace; font-size: 12px; color: var(--text-regular);
}
.t-cell { font-size: 12px; color: var(--text-muted); }
.no-op { color: #ccc; font-size: 12px; }

.empty { padding: 60px 20px; text-align: center; color: var(--text-muted); }
.empty-ico { font-size: 56px; opacity: 0.5; margin-bottom: 14px; }
.empty p { font-size: 14px; }

.legend {
  display: flex; align-items: center; gap: 10px;
  margin-top: 18px; padding: 14px 22px;
  background: var(--bg-soft);
  border-radius: var(--r-md);
  font-size: 13px; color: var(--text-muted);
  flex-wrap: wrap;
}
.legend .arrow { color: #bbb; }
</style>
