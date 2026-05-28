import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const navLinks = [
  { path: '/', label: '首页', icon: '🏠' },
  { path: '/marketplace', label: '策略超市', icon: '🏪' },
  { path: '/backtest', label: '回测', icon: '📊' },
  { path: '/dashboard', label: '数据看板', icon: '📈' },
  { path: '/documents', label: '文档', icon: '📄' },
]

export default function Navbar() {
  const location = useLocation()
  const { user, logout } = useAuth()

  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      height: 56,
      padding: '0 24px',
      backgroundColor: '#0d1117',
      borderBottom: '1px solid #21262d',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      {/* Logo */}
      <Link to="/" style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        textDecoration: 'none',
        marginRight: 32,
      }}>
        <span style={{
          fontSize: 24,
          fontWeight: 700,
          color: '#e6edf3',
        }}>AQ</span>
        <span style={{
          fontSize: 14,
          color: '#8b949e',
          fontWeight: 400,
        }}>A股量化</span>
      </Link>

      {/* 导航链接 */}
      <div style={{ display: 'flex', gap: 4 }}>
        {navLinks.map(link => {
          const isActive = location.pathname === link.path ||
            (link.path !== '/' && location.pathname.startsWith(link.path))
          return (
            <Link
              key={link.path}
              to={link.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '8px 16px',
                borderRadius: 8,
                textDecoration: 'none',
                fontSize: 14,
                fontWeight: isActive ? 500 : 400,
                color: isActive ? '#e6edf3' : '#8b949e',
                backgroundColor: isActive ? '#1c2333' : 'transparent',
                transition: 'all 0.2s',
              }}
            >
              <span>{link.icon}</span>
              <span>{link.label}</span>
            </Link>
          )
        })}
      </div>

      {/* 右侧操作区 */}
      <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, alignItems: 'center' }}>
        {user ? (
          <>
            <Link to="/backtest">
              <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}>
                + 创建策略
              </button>
            </Link>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: '#8b949e', fontSize: 13 }}>
                {user.username}
              </span>
              <button
                onClick={logout}
                className="btn btn-ghost"
                style={{ padding: '4px 12px', fontSize: 12 }}
              >
                退出
              </button>
            </div>
          </>
        ) : (
          <>
            <Link to="/backtest">
              <button className="btn btn-primary" style={{ padding: '6px 16px', fontSize: 13 }}>
                + 创建策略
              </button>
            </Link>
            <Link to="/login">
              <button className="btn btn-ghost" style={{ padding: '6px 16px', fontSize: 13 }}>
                登录
              </button>
            </Link>
          </>
        )}
      </div>
    </nav>
  )
}
