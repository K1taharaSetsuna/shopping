<template>
  <!-- 管理后台布局 -->
  <MainLayout v-if="$route.meta.layout === 'admin'">
    <router-view />
  </MainLayout>

  <!-- C端购物布局 -->
  <div v-else class="app-shell">
    <SiteHeader />
    <main class="app-main">
      <router-view />
    </main>
    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import SiteHeader from './components/SiteHeader.vue'
import SiteFooter from './components/SiteFooter.vue'
import MainLayout from './layout/MainLayout.vue'
</script>

<style>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-page);
}
.app-main {
  flex: 1;
}
</style>
