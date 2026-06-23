<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside :width="colla ? '64px' : '220px'" class="aside">
      <div class="logo" @click="$router.push('/admin/dashboard')">
        <span class="logo-mark">悦</span>
        <span v-if="!colla" class="logo-text">悦选 Admin</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="colla"
        background-color="transparent"
        text-color="rgba(255,255,255,0.72)"
        active-text-color="#fff"
        router
        class="side-menu"
      >
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <template #title>
            <span class="m-text">{{ m.label }}</span>
          </template>
        </el-menu-item>
      </el-menu>

      <div class="side-foot" v-if="!colla">
        <div class="sf-env">
          <span class="dot on"></span> Nacos · Gateway · 6 services
        </div>
        <p>Spring Cloud Alibaba 实训</p>
      </div>
    </el-aside>

    <!-- 主区域 -->
    <el-container>
      <el-header class="header">
        <div class="h-left">
          <el-icon class="colla-btn" @click="colla = !colla">
            <Fold v-if="!colla" /><Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/" class="crumb">
            <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="h-right">
          <el-tooltip content="返回商城" placement="bottom">
            <el-icon class="h-ico" @click="goShopping"><Shop /></el-icon>
          </el-tooltip>
          <el-tooltip content="刷新页面" placement="bottom">
            <el-icon class="h-ico" @click="$router.go(0)"><Refresh /></el-icon>
          </el-tooltip>
          <el-divider direction="vertical" />
          <el-dropdown @command="onCmd">
            <div class="user">
              <span class="avatar">{{ initial }}</span>
              <div class="u-meta">
                <strong>{{ username || '管理员' }}</strong>
                <small>{{ roleLabel }}</small>
              </div>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile"><el-icon><User /></el-icon> 个人信息</el-dropdown-item>
                <el-dropdown-item command="pwd"><el-icon><Lock /></el-icon> 修改密码</el-dropdown-item>
                <el-dropdown-item divided command="logout"><el-icon><SwitchButton /></el-icon> 退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const colla = ref(false)

const menus = [
  { path: '/admin/dashboard', label: '仪表盘',   icon: 'DataBoard' },
  { path: '/admin/products',  label: '商品管理', icon: 'Goods' },
  { path: '/admin/orders',    label: '订单管理', icon: 'Document' },
]
const activeMenu = computed(() => route.path)
const currentTitle = computed(() => menus.find(m => m.path === route.path)?.label || '管理')

const username = computed(() => {
  try { return JSON.parse(sessionStorage.getItem('yuexuan_user') || '{}').username || '' } catch { return '' }
})
const role = computed(() => {
  try { return JSON.parse(sessionStorage.getItem('yuexuan_user') || '{}').role || '' } catch { return '' }
})
const initial = computed(() => (username.value || 'A').slice(0, 1).toUpperCase())
const roleLabel = computed(() => {
  const map: Record<string, string> = { platform: '平台管理员', admin: '管理员', shop: '商家' }
  return map[role.value] || '管理员'
})

function onCmd(c: string) {
  if (c === 'logout') {
    ElMessageBox.confirm('确认退出登录吗？', '提示', { type: 'warning' }).then(() => {
      sessionStorage.removeItem('yuexuan_token')
      sessionStorage.removeItem('yuexuan_user')
      router.push('/login')
    }).catch(() => {})
  } else if (c === 'profile' || c === 'pwd') {
    ElMessageBox.alert('实训演示项目，暂未实现该功能。', '提示')
  }
}

function goShopping() {
  window.location.hash = '#/'
}
</script>

<style scoped>
.layout { height: 100vh; }

/* 侧边栏：深棕黑 */
.aside {
  background: linear-gradient(180deg, #2A1810 0%, #1A0F0A 100%);
  transition: width 0.28s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 64px;
  display: flex; align-items: center; gap: 10px;
  padding: 0 20px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.logo-mark {
  width: 36px; height: 36px;
  background: linear-gradient(135deg, var(--primary), var(--yellow));
  color: #fff; font-size: 20px; font-weight: 800;
  display: grid; place-items: center;
  border-radius: var(--r-sm);
  box-shadow: 0 4px 10px rgba(255,68,0,0.4);
  flex-shrink: 0;
}
.logo-text { color: #fff; font-size: 17px; font-weight: 700; letter-spacing: 1px; white-space: nowrap; }

.side-menu { border-right: none; flex: 1; padding-top: 10px; }
.side-menu :deep(.el-menu-item) {
  margin: 4px 10px;
  border-radius: var(--r-sm);
  height: 46px;
  line-height: 46px;
}
.side-menu :deep(.el-menu-item:hover) { background: rgba(255,255,255,0.06) !important; }
.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, var(--primary), var(--primary-hover)) !important;
  color: #fff !important;
  box-shadow: 0 4px 12px rgba(255,68,0,0.35);
}
.m-text { font-size: 14px; }
.m-badge {
  font-style: normal;
  margin-left: 8px;
  background: var(--yellow);
  color: #1a1a1a;
  font-size: 11px; font-weight: 700;
  padding: 0 7px; border-radius: 999px;
  min-width: 18px; text-align: center;
}

.side-foot {
  padding: 14px 20px 20px;
  color: rgba(255,255,255,0.4);
  font-size: 11px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.sf-env { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.dot { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; }
.dot.on { box-shadow: 0 0 6px #4ade80; }
.side-foot p { margin: 0; }

/* 顶栏 */
.header {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff;
  padding: 0 28px;
  height: 60px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  z-index: 1;
}
.h-left { display: flex; align-items: center; gap: 18px; }
.colla-btn { font-size: 20px; cursor: pointer; color: var(--text-secondary); }
.colla-btn:hover { color: var(--primary); }
.crumb { font-size: 14px; }

.h-right { display: flex; align-items: center; gap: 14px; }
.h-ico { font-size: 18px; cursor: pointer; color: var(--text-secondary); }
.h-ico:hover { color: var(--primary); }

.user {
  display: flex; align-items: center; gap: 10px;
  cursor: pointer;
  padding: 5px 10px 5px 5px;
  border-radius: var(--r-round);
  transition: background 0.2s;
}
.user:hover { background: var(--bg-gray); }
.avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--yellow));
  color: #fff; font-size: 16px; font-weight: 700;
  display: grid; place-items: center;
}
.u-meta { display: flex; flex-direction: column; line-height: 1.25; }
.u-meta strong { font-size: 13px; color: var(--text-primary); }
.u-meta small { font-size: 11px; color: var(--text-muted); }
</style>
