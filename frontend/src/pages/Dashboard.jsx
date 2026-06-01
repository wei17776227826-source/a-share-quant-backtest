import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import api from '../api'

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return
    if (!user) { navigate('/login'); return }
    loadData()
  }, [user, authLoading])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await api.get('/dashboard/summary')
      setData(res.data)
    } catch { /* ignore */ }
    setLoading(false)
  }

  if (!user) return null

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 'calc(100vh - 56px)', color: '#595e6b' }}>
        加载中...
      </div>
    )
  }

  const stats = [
    { label: '回测次数', value: data?.total_backtests || 0, icon: '📊', color: '#58a6ff' },
    { label: '策略数量', value: data?.total_strategies || 0, icon: '🎯', color: '#d29922' },
    { label: '平均收益', value: `${data?.avg_return || 0}%`, icon: '📈', color: data?.avg_return >= 0 ? '#3fb950' : '#f85149' },
    { label: '胜率', value: `${data?.win_rate || 0}%`, icon: '🏆', color: data?.win_rate >= 50 ? '#3fb950' : '#d29922' },
    { label: '最佳收益', value: `${data?.best_return || 0}%`, icon: '🔥', color: '#3fb950' },
    { label: '最差收益', value: `${data?.worst_return || 0}%`, icon: '💀', color: '#f85149' },
  ]

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3', marginBottom: 24 }}>数据看板</h1>

      {/* 统计卡片 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12, marginBottom: 24 }}>
        {stats.map(s => (
          <div key={s.label} className="card" style={{ padding: '16px 14' }}>
            <div style={{ fontSize: 22, marginBottom: 6 }}>{s.icon}</div>
            <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 2 }}>{s.label}</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* 策略表现 */}
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: '#e6edf3', marginBottom: 16 }}>策略表现</h3>
          {data?.strategy_perf && data.strategy_perf.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.strategy_perf.map(sp => (
                <div key={sp.name} style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #2d3343' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ color: '#e6edf3', fontSize: 14 }}>{sp.name}</span>
                    <span style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: sp.avg_return >= 0 ? '#3fb950' : '#f85149',
                    }}>
                      {sp.avg_return >= 0 ? '+' : ''}{sp.avg_return}%
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: '#595e6b' }}>运行 {sp.count} 次</div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#595e6b', padding: 30 }}>
              暂无回测数据
              <br />
              <Link to="/backtest" style={{ color: '#58a6ff', fontSize: 13 }}>去运行回测</Link>
            </div>
          )}
        </div>

        {/* 股票表现 */}
        <div className="card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: '#e6edf3', marginBottom: 16 }}>股票表现 Top 10</h3>
          {data?.symbol_perf && data.symbol_perf.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.symbol_perf.map(sp => (
                <div key={sp.symbol} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '8px 14px',
                  borderRadius: 6,
                  border: '1px solid #2d3343',
                }}>
                  <span style={{ color: '#e6edf3', fontSize: 14 }}>{sp.symbol}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: 12, color: '#595e6b' }}>{sp.count} 次</span>
                    <span style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: sp.avg_return >= 0 ? '#3fb950' : '#f85149',
                    }}>
                      {sp.avg_return >= 0 ? '+' : ''}{sp.avg_return}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#595e6b', padding: 30 }}>
              暂无回测数据
              <br />
              <Link to="/backtest" style={{ color: '#58a6ff', fontSize: 13 }}>去运行回测</Link>
            </div>
          )}
        </div>

        {/* 最近回测 */}
        <div className="card" style={{ padding: 20, gridColumn: '1 / -1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: '#e6edf3' }}>最近回测</h3>
            <Link to="/results" style={{ color: '#58a6ff', fontSize: 13, textDecoration: 'none' }}>查看全部 →</Link>
          </div>
          {data?.recent && data.recent.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #2d3343' }}>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>日期</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>股票</th>
                    <th style={{ textAlign: 'left', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>策略</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>收益</th>
                    <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>交易次数</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent.map(r => (
                    <tr key={r.id} style={{ borderBottom: '1px solid #1c2333' }}>
                      <td style={{ padding: '8px 12px', color: '#8b949e' }}>{r.created_at}</td>
                      <td style={{ padding: '8px 12px', color: '#e6edf3' }}>{r.symbol}</td>
                      <td style={{ padding: '8px 12px' }}>
                        <span className="badge badge-blue">{r.strategy_name}</span>
                      </td>
                      <td style={{
                        padding: '8px 12px',
                        textAlign: 'right',
                        fontWeight: 600,
                        color: r.total_return >= 0 ? '#3fb950' : '#f85149',
                      }}>
                        {(r.total_return * 100).toFixed(2)}%
                      </td>
                      <td style={{ padding: '8px 12px', textAlign: 'right', color: '#e6edf3' }}>{r.total_trades}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#595e6b', padding: 30 }}>
              暂无回测记录
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
