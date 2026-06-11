import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 自动带上 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器 - 401 自动清除 token
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
    }
    return Promise.reject(err)
  }
)

export default api

// 认证接口
export const auth = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }).then(r => r.data),

  register: (username, password) =>
    api.post('/auth/register', { username, password }).then(r => r.data),

  me: () =>
    api.get('/auth/me').then(r => r.data),
}

// 回测接口
export const backtest = {
  run: (data) =>
    api.post('/backtest/run', data).then(r => r.data),

  list: (limit = 20, offset = 0) =>
    api.get('/backtest/results', { params: { limit, offset } }).then(r => r.data),

  detail: (id) =>
    api.get(`/backtest/results/${id}`).then(r => r.data),

  delete: (id) =>
    api.delete(`/backtest/results/${id}`).then(r => r.data),
}

// 策略接口
export const strategies = {
  list: () =>
    api.get('/strategies').then(r => r.data),

  create: (data) =>
    api.post('/strategies', data).then(r => r.data),

  detail: (id) =>
    api.get(`/strategies/${id}`).then(r => r.data),

  update: (id, data) =>
    api.put(`/strategies/${id}`, data).then(r => r.data),

  delete: (id) =>
    api.delete(`/strategies/${id}`).then(r => r.data),
}

// 产业链研究接口
export const industry = {
  chains: () =>
    api.get('/industry/chains').then(r => r.data),

  chainDetail: (industryId) =>
    api.get(`/industry/chains/${industryId}`).then(r => r.data),

  research: (industryId) =>
    api.post('/industry/research', { industry_id: industryId }).then(r => r.data),

  list: (limit = 20, offset = 0) =>
    api.get('/industry/research', { params: { limit, offset } }).then(r => r.data),

  detail: (id) =>
    api.get(`/industry/research/${id}`).then(r => r.data),

  delete: (id) =>
    api.delete(`/industry/research/${id}`).then(r => r.data),

  search: (industryId, keyword) =>
    api.get('/industry/search', { params: { industry_id: industryId, keyword } }).then(r => r.data),
}
