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
}
