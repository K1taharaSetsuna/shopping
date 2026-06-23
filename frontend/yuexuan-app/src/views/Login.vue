<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <section class="hero-side">
      <div class="hero-inner">
        <div class="brand">
          <span class="brand-mark">悦</span>
          <div>
            <strong>悦选</strong>
            <small>YUE SELECT</small>
          </div>
        </div>
        <h1>AI 智能购物<br>遇见生活美好</h1>
        <p>Spring Cloud Alibaba 微服务实训项目 · 全栈真实链路</p>
        <ul class="feats">
          <li>🛒 两步式防重下单</li>
          <li>🔐 JWT 网关统一鉴权</li>
          <li>📊 管理后台数据看板</li>
          <li>🔍 Sleuth + Zipkin 链路追踪</li>
          <li>⚖️ Sentinel 流控 · Nacos 注册中心</li>
        </ul>
      </div>
    </section>

    <!-- 右侧表单区 -->
    <section class="form-side">
      <div class="form-card">
        <div class="tabs">
          <span :class="{ on: tab === 'login' }" @click="tab = 'login'">
            <b>登录</b><i v-if="tab==='login'"></i>
          </span>
          <span :class="{ on: tab === 'register' }" @click="tab = 'register'">
            <b>注册</b><i v-if="tab==='register'"></i>
          </span>
        </div>

        <!-- 登录表单 -->
        <form v-if="tab === 'login'" @submit.prevent="handleLogin" class="form">
          <label class="field">
            <span>用户名</span>
            <div class="ipt">
              <el-icon><User /></el-icon>
              <input v-model.trim="loginForm.username" placeholder="请输入用户名" autocomplete="username" />
            </div>
          </label>
          <label class="field">
            <span>密码</span>
            <div class="ipt">
              <el-icon><Lock /></el-icon>
              <input v-model="loginForm.password" type="password" placeholder="请输入密码" autocomplete="current-password" />
            </div>
          </label>
          <div class="row">
            <label class="remember"><input type="checkbox" v-model="remember" /> 记住我</label>
            <a class="forgot">忘记密码？</a>
          </div>
          <button type="submit" class="submit" :disabled="loading">
            <span v-if="!loading">登 录</span>
            <span v-else>登录中...</span>
          </button>
        </form>

        <!-- 注册表单 -->
        <form v-else @submit.prevent="handleRegister" class="form">
          <label class="field">
            <span>用户名</span>
            <div class="ipt">
              <el-icon><User /></el-icon>
              <input v-model.trim="regForm.username" placeholder="请设置用户名" />
            </div>
          </label>
          <label class="field">
            <span>密码</span>
            <div class="ipt">
              <el-icon><Lock /></el-icon>
              <input v-model="regForm.password" type="password" placeholder="请设置密码" />
            </div>
          </label>
          <label class="field">
            <span>手机号</span>
            <div class="ipt">
              <el-icon><Phone /></el-icon>
              <input v-model.trim="regForm.phone" placeholder="请输入手机号" />
            </div>
          </label>
          <button type="submit" class="submit" :disabled="loading">
            <span v-if="!loading">注 册</span>
            <span v-else>注册中...</span>
          </button>
        </form>

        <!-- 演示账号 -->
        <div class="demo">
          <p class="demo-title">演示账号 · 密码 <code>123456</code></p>
          <div class="demo-chips">
            <span
              v-for="a in demoAccounts" :key="a.u"
              @click="fillDemo(a.u)"
              :class="{ vip: a.vip }"
            >
              {{ a.u }}<em>{{ a.tag }}</em>
            </span>
          </div>
        </div>

        <p v-if="errMsg" class="err">⚠ {{ errMsg }}</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { login, register, parseRole } from '../api'

const router = useRouter()
const tab = ref<'login' | 'register'>('login')
const loading = ref(false)
const errMsg = ref('')
const remember = ref(false)

const loginForm = reactive({ username: 'user1', password: '123456' })
const regForm = reactive({ username: '', password: '', phone: '' })

const demoAccounts = [
  { u: 'user1',      tag: '顾客', vip: false },
  { u: 'shop1',      tag: '商家', vip: false },
  { u: 'shoe_shop',  tag: '商家', vip: false },
  { u: 'cloth_shop', tag: '商家', vip: false },
  { u: 'admin',      tag: '平台', vip: true },
]

const ADMIN_ROLES = ['shop', 'admin', 'platform']

function fillDemo(u: string) {
  loginForm.username = u
  loginForm.password = '123456'
  tab.value = 'login'
}

/** 登录成功后根据角色跳转 */
function redirectByRole(role: string) {
  if (ADMIN_ROLES.includes(role)) {
    router.push('/admin/dashboard')
  } else {
    router.push('/')
  }
}

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) { errMsg.value = '请输入用户名和密码'; return }
  loading.value = true; errMsg.value = ''
  try {
    const res: any = await login(loginForm.username, loginForm.password)
    const token = res.token
    const role = parseRole(token)
    sessionStorage.setItem('yuexuan_token', token)
    sessionStorage.setItem('yuexuan_user', JSON.stringify({ username: loginForm.username, role }))
    redirectByRole(role)
  } catch (e: any) {
    errMsg.value = '登录失败：' + (e?.message || '账号或密码错误')
  } finally { loading.value = false }
}

async function handleRegister() {
  if (!regForm.username || !regForm.password) { errMsg.value = '请填写用户名和密码'; return }
  loading.value = true; errMsg.value = ''
  try {
    const res: any = await register(regForm.username, regForm.password, regForm.phone)
    const token = res.token
    const role = parseRole(token)
    sessionStorage.setItem('yuexuan_token', token)
    sessionStorage.setItem('yuexuan_user', JSON.stringify({ username: regForm.username, role }))
    redirectByRole(role)
  } catch (e: any) {
    errMsg.value = '注册失败：' + (e?.message || '该用户名可能已存在')
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: var(--bg-page);
}

/* 左侧品牌区 */
.hero-side {
  background: linear-gradient(135deg, #FF4400 0%, #FF7A45 50%, #FFC400 100%);
  display: grid; place-items: center;
  position: relative;
  overflow: hidden;
  color: #fff;
}
.hero-side::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 30%, rgba(255,255,255,0.18), transparent 40%),
    radial-gradient(circle at 80% 80%, rgba(255,255,255,0.15), transparent 40%);
}
.hero-inner { position: relative; padding: 60px; }
.brand { display: flex; align-items: center; gap: 14px; margin-bottom: 50px; }
.brand-mark {
  width: 52px; height: 52px;
  background: rgba(255,255,255,0.25);
  border: 2px solid rgba(255,255,255,0.5);
  border-radius: var(--r-md);
  display: grid; place-items: center;
  font-size: 30px; font-weight: 800;
  backdrop-filter: blur(8px);
}
.brand strong { display: block; font-size: 22px; font-weight: 800; }
.brand small { font-size: 11px; letter-spacing: 2px; opacity: 0.85; }

.hero-side h1 {
  font-size: 42px; font-weight: 800; line-height: 1.3;
  margin-bottom: 16px; text-shadow: 0 3px 12px rgba(0,0,0,0.1);
}
.hero-side p {
  font-size: 14px; opacity: 0.9; margin-bottom: 40px;
}
.feats { display: flex; flex-direction: column; gap: 14px; }
.feats li {
  display: flex; align-items: center; gap: 12px;
  font-size: 14px;
  background: rgba(255,255,255,0.12);
  padding: 12px 18px;
  border-radius: var(--r-md);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.18);
}

/* 右侧表单区 */
.form-side { display: grid; place-items: center; padding: 40px; }
.form-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: var(--r-lg);
  padding: 36px 36px 30px;
  box-shadow: var(--shadow-md);
}
.tabs {
  display: flex;
  gap: 28px;
  padding-bottom: 4px;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.tabs span {
  position: relative;
  padding-bottom: 12px;
  font-size: 17px;
  color: var(--text-muted);
  cursor: pointer;
  font-weight: 500;
}
.tabs span.on { color: var(--primary); }
.tabs span.on i {
  position: absolute; left: 0; right: 0; bottom: -1px;
  height: 3px; background: var(--primary);
  border-radius: 2px;
}

.form { display: flex; flex-direction: column; gap: 18px; }
.field { display: flex; flex-direction: column; gap: 8px; }
.field > span { font-size: 13px; color: var(--text-secondary); }
.ipt {
  display: flex; align-items: center; gap: 10px;
  height: 44px; padding: 0 14px;
  border: 1px solid var(--border-strong);
  border-radius: var(--r-md);
  background: var(--bg-soft);
  transition: all 0.2s;
}
.ipt .el-icon { color: var(--text-muted); font-size: 17px; flex-shrink: 0; }
.ipt input {
  flex: 1; border: none; background: transparent;
  font-size: 14px; outline: none;
}
.ipt:focus-within {
  border-color: var(--primary);
  background: #fff;
  box-shadow: 0 0 0 3px var(--primary-light);
}

.row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px;
}
.remember { display: flex; align-items: center; gap: 6px; color: var(--text-secondary); cursor: pointer; }
.remember input { accent-color: var(--primary); }
.forgot { color: var(--primary); cursor: pointer; }

.submit {
  height: 46px;
  margin-top: 6px;
  background: linear-gradient(135deg, var(--primary), var(--primary-hover));
  color: #fff;
  font-size: 16px; font-weight: 700; letter-spacing: 4px;
  border-radius: var(--r-md);
  box-shadow: 0 6px 16px rgba(255,68,0,0.3);
  transition: all 0.2s;
  border: none;
}
.submit:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(255,68,0,0.4); }
.submit:disabled { opacity: 0.6; cursor: wait; transform: none; }

.demo {
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px dashed var(--border);
}
.demo-title {
  font-size: 12px; color: var(--text-muted); margin-bottom: 10px; text-align: center;
}
.demo-title code {
  background: var(--bg-gray); padding: 1px 6px; border-radius: 3px;
  font-family: monospace; color: var(--primary);
}
.demo-chips {
  display: flex; gap: 8px; justify-content: center; flex-wrap: wrap;
}
.demo-chips span {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px;
  background: var(--bg-gray);
  border-radius: var(--r-round);
  font-size: 12px; color: var(--text-regular);
  cursor: pointer;
  border: 1px solid var(--border);
  transition: all 0.2s;
}
.demo-chips span:hover { background: var(--primary-bg); border-color: var(--primary); color: var(--primary); }
.demo-chips span.vip { background: #FFF8E1; border-color: #FFE082; color: #B8860B; }
.demo-chips span em {
  font-style: normal; font-size: 10px;
  padding: 1px 5px; background: rgba(0,0,0,0.08); border-radius: 3px;
}

.err {
  margin-top: 14px;
  padding: 10px 14px;
  background: #FEF2F2;
  color: #DC2626;
  font-size: 13px;
  border-radius: var(--r-sm);
  border-left: 3px solid #DC2626;
  text-align: center;
}

@media (max-width: 800px) {
  .login-page { grid-template-columns: 1fr; }
  .hero-side { display: none; }
}
</style>
