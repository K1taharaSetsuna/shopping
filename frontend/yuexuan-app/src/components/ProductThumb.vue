<template>
  <div class="a-thumb" :style="{ width, height, borderRadius: radius }">
    <img
      v-if="src && !failed"
      :src="src"
      :alt="alt"
      @error="failed = true"
    />
    <div v-else class="ph" :style="{ background: cat.bg }">
      <span :style="{ color: cat.fg }">{{ cat.ico }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps({
  image:    { type: String, default: '' },
  category: { type: String, default: '' },
  name:     { type: String, default: '' },
  width:    { type: String, default: '44px' },
  height:   { type: String, default: '44px' },
  radius:   { type: String, default: '8px' },
  alt:      { type: String, default: '商品图' },
})

const failed = ref(false)
watch(() => props.image, () => { failed.value = false })

const CAT: Record<string, { ico: string; bg: string; fg: string }> = {
  '运动鞋': { ico: '👟', bg: 'linear-gradient(135deg,#FFF3E0,#FFE0B2)', fg: '#E65100' },
  'T恤':   { ico: '👕', bg: 'linear-gradient(135deg,#F3E5F5,#E1BEE7)', fg: '#7B1FA2' },
  '数码':   { ico: '🎧', bg: 'linear-gradient(135deg,#E0F7FA,#B2EBF2)', fg: '#00838F' },
  '食品':   { ico: '🥜', bg: 'linear-gradient(135deg,#F1F8E9,#DCEDC8)', fg: '#558B2F' },
  '家居':   { ico: '🏠', bg: 'linear-gradient(135deg,#EFEBE9,#D7CCC8)', fg: '#5D4037' },
}
const DEFAULT = { ico: '📦', bg: 'linear-gradient(135deg,#ECEFF1,#CFD8DC)', fg: '#455A64' }

const cat = computed(() => CAT[props.category] || DEFAULT)

const src = computed(() => {
  const im = props.image || ''
  if (!im) return ''
  if (/^https?:\/\//i.test(im)) return im
  if (im.startsWith('/')) return im
  return `/images/${im}`
})
</script>

<style scoped>
.a-thumb {
  flex-shrink: 0;
  overflow: hidden;
  background: #fff;
}
.a-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.ph { width: 100%; height: 100%; display: grid; place-items: center; }
.ph span { font-size: 1.5em; line-height: 1; }
</style>
