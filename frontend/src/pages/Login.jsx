import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Login() {
  const [tab, setTab] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (tab === 'login') {
        await login(username, password)
      } else {
        await register(username, password)
      }
      navigate('/backtest')
    } catch (err) {
      const detail = err.response?.data?.detail || '操作失败，请重试'
      setError(detail)
    } finally {
      setLoading(false)
    }
  }

  const isFormValid = username.length >= 2 && password.length >= 4

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: 'calc(100vh - 56px)',
      padding: 24,
    }}>
      <div className="card" style={{
        width: 420,
        padding: 40,
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: 36, fontWeight: 700, color: '#e6edf3', marginBottom: 8 }}>
            AQ
          </div>
          <div style={{ color: '#8b949e', fontSize: 14 }}>
            A股量化回测平台
          </div>
        </div>

        {/* 标签切换 */}
        <div style={{
          display: 'flex',
          backgroundColor: '#161b22',
          borderRadius: 10,
          padding: 4,
          marginBottom: 24,
        }}>
          {[
            { key: 'login', label: '登录' },
            { key: 'register', label: '注册' },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => { setTab(t.key); setError('') }}
              style={{
                flex: 1,
                padding: '10px 0',
                borderRadius: 8,
                border: 'none',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 500,
                backgroundColor: tab === t.key ? '#1c2333' : 'transparent',
                color: tab === t.key ? '#e6edf3' : '#8b949e',
                transition: 'all 0.2s',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* 错误提示 */}
        {error && (
          <div style={{
            padding: '10px 14px',
            borderRadius: 8,
            backgroundColor: 'rgba(248,81,73,0.1)',
            color: '#f85149',
            fontSize: 13,
            marginBottom: 16,
          }}>
            {error}
          </div>
        )}

        {/* 表单 */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', color: '#8b949e', fontSize: 13, marginBottom: 6 }}>
              用户名
            </label>
            <input
              className="input"
              type="text"
              placeholder="输入用户名"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoFocus
            />
          </div>
          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', color: '#8b949e', fontSize: 13, marginBottom: 6 }}>
              密码
            </label>
            <input
              className="input"
              type="password"
              placeholder="输入密码"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px 0', fontSize: 15 }}
            disabled={!isFormValid || loading}
          >
            {loading ? '处理中...' : tab === 'login' ? '登录' : '注册'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <span style={{ color: '#595e6b', fontSize: 13 }}>
            {tab === 'login' ? '还没有账号？' : '已有账号？'}
          </span>
          <button
            onClick={() => { setTab(tab === 'login' ? 'register' : 'login'); setError('') }}
            style={{
              background: 'none',
              border: 'none',
              color: '#58a6ff',
              cursor: 'pointer',
              fontSize: 13,
              marginLeft: 4,
            }}
          >
            {tab === 'login' ? '立即注册' : '去登录'}
          </button>
        </div>
      </div>
    </div>
  )
}
