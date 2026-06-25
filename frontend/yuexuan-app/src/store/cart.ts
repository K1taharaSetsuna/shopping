import { reactive } from 'vue'

export interface CartItem {
  pid: number
  name: string
  price: number
  category: string
  image: string
  qty: number
  selected: boolean
}

const KEY = 'yuexuan_cart'

function load(): CartItem[] {
  try { return JSON.parse(localStorage.getItem(KEY) || '[]') } catch { return [] }
}

function save(items: CartItem[]) {
  localStorage.setItem(KEY, JSON.stringify(items))
}

export const cart = reactive<{ items: CartItem[] }>({ items: load() })

export function addToCart(pid: number, name: string, price: number, category: string, image: string = '', qty: number = 1) {
  const exist = cart.items.find(i => i.pid === pid)
  if (exist) { exist.qty += qty } else {
    cart.items.push({ pid, name: name.split('—')[0], price, category, image, qty, selected: true })
  }
  save(cart.items)
}

export function removeFromCart(pid: number) {
  cart.items = cart.items.filter(i => i.pid !== pid)
  save(cart.items)
}

export function updateQty(pid: number, qty: number) {
  const item = cart.items.find(i => i.pid === pid)
  if (item && qty > 0) { item.qty = qty; save(cart.items) }
}

export function toggleSelect(pid: number) {
  const item = cart.items.find(i => i.pid === pid)
  if (item) { item.selected = !item.selected; save(cart.items) }
}

export function toggleAll() {
  const all = cart.items.every(i => i.selected)
  cart.items.forEach(i => i.selected = !all)
  save(cart.items)
}

export function clearSelected() {
  cart.items = cart.items.filter(i => !i.selected)
  save(cart.items)
}

export const selectedItems = () => cart.items.filter(i => i.selected)
export const totalPrice = () => selectedItems().reduce((s, i) => s + i.price * i.qty, 0)
export const cartCount = () => cart.items.reduce((s, i) => s + i.qty, 0)
