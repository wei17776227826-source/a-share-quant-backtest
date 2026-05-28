import { createContext, useContext, useState, useEffect } from 'react'
import { auth } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // 初始化时检查是否已登录
  useEffect(() => {
    const token = localStorage.getItem('token')
    const username = localStorage.getItem('username')
    if (token && username) {
      // 验证 token 是否有效
      auth.me()
        .then((data) => {
          setUser({ username: data.username, id: data.id })
        })
        .catch(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('username')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username, password) => {
    const data = await auth.login(username, password)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    setUser({ username: data.username })
    return data
  }

  const register = async (username, password) => {
    const data = await auth.register(username, password)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    setUser({ username: data.username })
    return data
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
