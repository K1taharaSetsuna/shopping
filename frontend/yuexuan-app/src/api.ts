import axios from 'axios'
import { ElMessage } from 'element-plus'

const raw = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// ==================== 请求拦截 ====================
raw.interceptors.request.use(config => {
  const jwt = sessionStorage.getItem('yuexuan_token')
  if (jwt) {
    config.headers.Authorization = `Bearer ${jwt}`
  }
  return config
})

// ==================== 响应拦截：自动解包 + 401 跳转 ====================
raw.interceptors.response.use(
  response => {
    const res = response.data
    // 标准格式 {code: 0, data: ...} → 自动解包
    if (res && typeof res.code === 'number') {
      if (res.code === 0) return res.data ?? res
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(res)
    }
    // 非标准格式（如 ProductController.findById 直接返回 Product）→ 透传
    return res
  },
  error => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('yuexuan_token')
      sessionStorage.removeItem('yuexuan_user')
      window.location.hash = '#/login'
    }
    ElMessage.error(error.message || '网络错误')
    return Promise.reject(error)
  }
)

/**
 * 类型包装器：拦截器已自动解包 response.data.data，
 * 但 TS 无法追踪拦截器对返回类型的改变 — 通过泛型包装解决。
 */
const http = {
  get<T = any>(url: string, config?: any): Promise<T>    { return raw.get(url, config) as any },
  post<T = any>(url: string, data?: any, config?: any): Promise<T> { return raw.post(url, data, config) as any },
  put<T = any>(url: string, data?: any, config?: any): Promise<T>  { return raw.put(url, data, config) as any },
  delete<T = any>(url: string, config?: any): Promise<T> { return raw.delete(url, config) as any },
}

export default http

// ==================== 类型定义 ====================
export interface Product {
  pid: number; name: string; price: number; image: string
  category: string; description: string; stock: number
  rating: number; reviewCount: number
}

export interface Order {
  id: number; orderNo: string; pid: number; productName: string; productPrice: number
  uid: number; username: string; number: number; totalAmount: number
  status: string; receiverName: string; receiverPhone: string; address: string
  handledByPort: string; createTime: string; payTime: string
}

export interface OrderSubmitItem { pid: number; qty: number }

export interface OrderSubmitRequest {
  confirmToken: string
  items: OrderSubmitItem[]
  receiverName: string
  receiverPhone: string
  address: string
}

export interface ConfirmVO {
  items: ConfirmItem[]
  totalAmount: number
  deliveryFee: number
  payAmount: number
  confirmToken: string
}

export interface ConfirmItem {
  pid: number; name: string; price: number; qty: number
  subtotal: number; stock: number; inStock: boolean
}

export interface PayInfo {
  payId: number; orderId: number; orderNo: string
  userId: number; amount: number; status: string
  createTime: string; payTime: string
}

// ==================== C端：商品 ====================
export const getProducts = (category?: string, keyword?: string): Promise<Product[]> =>
  http.get('/admin/products', { params: { category, keyword } })

export const getProductById = (pid: number): Promise<Product> =>
  http.get(`/admin/products/${pid}`)

// ==================== C端：订单 ====================
export const getOrders = (status?: string): Promise<Order[]> =>
  http.get('/a/orders', { params: status ? { status } : {} })

export const confirmOrder = (req: { items: OrderSubmitItem[], receiverName: string, receiverPhone: string, address: string }): Promise<ConfirmVO> =>
  http.post('/a/orders/confirm', req)

export const submitOrder = (req: OrderSubmitRequest): Promise<Order[]> =>
  http.post('/a/orders/submit', req)

export const payByService = (orderId: number): Promise<PayInfo> =>
  http.post('/a/payment/pay', { orderId })

export const cancelOrder = (id: number): Promise<void> =>
  http.put(`/a/orders/${id}/cancel`)

export const receiveOrder = (id: number): Promise<void> =>
  http.put(`/a/orders/${id}/receive`)

// ==================== 鉴权 ====================
export const login = (username: string, password: string): Promise<{ token: string }> =>
  http.post('/a/login', { username, password })

export const register = (username: string, password: string, phone: string): Promise<{ token: string }> =>
  http.post('/a/register', { username, password, phone })

// ==================== 管理后台 API ====================
export const getDashboard = (): Promise<any> =>
  http.get('/platform/dashboard')

export const adminGetProducts = (params?: any): Promise<Product[]> =>
  http.get('/admin/products', { params })

export const adminCreateProduct = (data: any): Promise<any> =>
  http.post('/admin/products', data)

export const adminUpdateProduct = (pid: number, data: any): Promise<any> =>
  http.put(`/admin/products/${pid}`, data)

export const adminDeleteProduct = (pid: number): Promise<any> =>
  http.delete(`/admin/products/${pid}`)

export const adminGetOrders = (params?: any): Promise<Order[]> =>
  http.get('/platform/orders', { params })

export const adminShipOrder = (id: number): Promise<any> =>
  http.post(`/m/orders/${id}/delivery`)

// ==================== 工具函数 ====================
/** 从 JWT 中解析 role（不验签，后端已验证） */
export function parseRole(token: string): string {
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload?.role || ''
  } catch { return '' }
}

/** 根据商品名猜测类目 */
export function guessCat(name?: string): string {
  const s = name || ''
  if (/鞋|跑鞋|板鞋|篮球鞋/.test(s)) return '运动鞋'
  if (/T恤|速干|卫衣/.test(s)) return 'T恤'
  if (/耳机|手表|音箱|数码|蓝牙/.test(s)) return '数码'
  if (/坚果|绿茶|零食|食品/.test(s)) return '食品'
  if (/台灯|坐垫|收纳|家居/.test(s)) return '家居'
  return ''
}
