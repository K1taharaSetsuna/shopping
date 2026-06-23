import { createApp } from 'vue'
import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './style.css'
import App from './App.vue'
import { parseRole } from './api'

// ==================== 懒加载页面 ====================
const Login = () => import('./views/Login.vue')
// C端（购物）
const HomePage = () => import('./views/HomePage.vue')
const ProductDetail = () => import('./views/ProductDetail.vue')
const Cart = () => import('./views/Cart.vue')
const ConfirmOrder = () => import('./views/ConfirmOrder.vue')
const PayResult = () => import('./views/PayResult.vue')
const UserOrders = () => import('./views/Orders.vue')
const Recognize = () => import('./views/Recognize.vue')
// 管理后台
const Dashboard = () => import('./views/Dashboard.vue')
const ProductManage = () => import('./views/ProductManage.vue')
const OrderManage = () => import('./views/OrderManage.vue')

// ==================== 路由表 ====================
const ADMIN_ROLES = ['shop', 'admin', 'platform']

const routes: RouteRecordRaw[] = [
  // ---- 公共 ----
  { path: '/login', name: 'login', component: Login },

  // ---- C端 购物（仅 user） ----
  { path: '/',              name: 'home',     component: HomePage },
  { path: '/product/:id',   name: 'product',  component: ProductDetail },
  { path: '/cart',          name: 'cart',     component: Cart },
  { path: '/confirm',       name: 'confirm',  component: ConfirmOrder },
  { path: '/result',        name: 'result',   component: PayResult },
  { path: '/orders',        name: 'orders',   component: UserOrders },
  { path: '/recognize',     name: 'recognize', component: Recognize },

  // ---- 管理后台（shop / admin / platform） ----
  { path: '/admin/dashboard', name: 'dashboard',      component: Dashboard,      meta: { layout: 'admin', roles: ADMIN_ROLES } },
  { path: '/admin/products',  name: 'admin-products', component: ProductManage,   meta: { layout: 'admin', roles: ADMIN_ROLES } },
  { path: '/admin/orders',    name: 'admin-orders',   component: OrderManage,     meta: { layout: 'admin', roles: ADMIN_ROLES } },
]

const router = createRouter({ history: createWebHashHistory(), routes })

// ==================== 路由守卫 ====================
const PUBLIC_PATHS = ['/login']

// 已登录用户根据 role 跳转到正确首页
function getHomeByRole(role: string): string {
  if (ADMIN_ROLES.includes(role)) return '/admin/dashboard'
  return '/'  // user 或未知 → C端首页
}

router.beforeEach((to, _from) => {
  const token = sessionStorage.getItem('yuexuan_token')

  // 1) 未登录 → 只能访问 /login
  if (!token && !PUBLIC_PATHS.includes(to.path)) {
    return '/login'
  }

  // 2) 已登录 → 检查角色权限
  if (token) {
    const role = parseRole(token)

    // 已登录访问 /login → 自动跳转到对应首页
    if (to.path === '/login') {
      return getHomeByRole(role)
    }

    // 路由有角色限制 → 越权自动跳转
    if (to.meta.roles) {
      const allowed = to.meta.roles as string[]
      if (!allowed.includes(role)) {
        return getHomeByRole(role)
      }
    }
  }
})

// ==================== 启动 ====================
const app = createApp(App)

// 全局注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(router).use(ElementPlus).mount('#app')
