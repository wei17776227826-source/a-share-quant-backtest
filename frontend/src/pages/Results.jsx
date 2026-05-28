import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { backtest } from '../api'

export default function Results() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [detailId, setDetailId] = useState(null)
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    loadResults()
  }, [user])

  const loadResults = async () => {
    setLoading(true)
    try {
      const data = await backtest.list(50, 0)
      setResults(data.results || [])
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const loadDetail = async (id) => {
    setDetailId(id)
    setDetail(null)
    try {
      const data = await backtest.detail(id)
      setDetail(data)
    } catch {
      setDetail({ error: '加载失败' })
    }
  }

  const handleDelete = async (id) => {
    try {
      await backtest.delete(id)
      if (detailId === id) {
        setDetailId(null)
        setDetail(null)
      }
      loadResults()
    } catch {
      // ignore
    }
  }

  const formatDate = (s) => s ? s.slice(0, 10) : '-'

  if (!user) return null

  return (
    <div style={{ display: 'flex', gap: 24, padding: 24, maxWidth: 1400, margin: '0 auto' }}>
      {/* 左侧列表 */}
      <div className="card" style={{ width: 420, flexShrink: 0, padding: 20, height: 'calc(100vh - 100px)', overflow: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, color: '#e6edf3' }}>
            回测记录
          </h2>
          <span style={{ color: '#8b949e', fontSize: 13 }}>
            {results.length} 条
          </span>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', color: '#595e6b', padding: 40 }}>加载中...</div>
        ) : results.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#595e6b', padding: 40 }}>
            <div style={{ fontSize: 36, marginBottom: 8 }}>📭</div>
            <div style={{ fontSize: 14 }}>还没有回测记录</div>
            <button
              className="btn btn-primary"
              style={{ marginTop: 16, fontSize: 13 }}
              onClick={() => navigate('/backtest')}
            >
              去运行回测
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {results.map(r => (
              <button
                key={r.id}
                onClick={() => loadDetail(r.id)}
                style={{
                  textAlign: 'left',
                  padding: '12px 14px',
                  borderRadius: 8,
                  border: `1px solid ${detailId === r.id ? '#58a6ff' : '#2d3343'}`,
                  backgroundColor: detailId === r.id ? 'rgba(88,166,255,0.08)' : 'transparent',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ color: '#e6edf3', fontWeight: 500, fontSize: 14 }}>
                    {r.symbol}
                  </span>
                  <span style={{
                    fontSize: 13,
                    fontWeight: 600,
                    color: r.total_return >= 0 ? '#3fb950' : '#f85149',
                  }}>
                    {(r.total_return * 100).toFixed(2)}%
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 8, fontSize: 12, color: '#8b949e' }}>
                  <span className="badge badge-blue">{r.strategy_name}</span>
                  <span>{formatDate(r.created_at)}</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 右侧详情 */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {!detailId ? (
          <div className="card" style={{
            padding: 60,
            textAlign: 'center',
            color: '#595e6b',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 12,
          }}>
            <div style={{ fontSize: 48 }}>📋</div>
            <div style={{ color: '#8b949e' }}>选择左侧一条记录查看详情</div>
          </div>
        ) : detail?.error ? (
          <div className="card" style={{ padding: 40, textAlign: 'center', color: '#f85149' }}>
            加载失败
          </div>
        ) : !detail ? (
          <div className="card" style={{ padding: 40, textAlign: 'center', color: '#595e6b' }}>
            加载中...
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* 概要 */}
            <div className="card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: 20, fontWeight: 600, color: '#e6edf3' }}>{detail.symbol}</span>
                  <span className="badge badge-blue">{detail.strategy_name}</span>
                </div>
                <button
                  className="btn btn-ghost"
                  style={{ padding: '4px 12px', fontSize: 12, color: '#f85149', borderColor: 'rgba(248,81,73,0.3)' }}
                  onClick={() => handleDelete(detail.id)}
                >
                  删除
                </button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12 }}>
                {[
                  { label: '总收益率', value: `${(detail.total_return * 100).toFixed(2)}%`, color: detail.total_return >= 0 ? '#3fb950' : '#f85149' },
                  { label: '年化收益', value: `${(detail.annual_return * 100).toFixed(2)}%`, color: '#58a6ff' },
                  { label: '最大回撤', value: `${(detail.max_drawdown * 100).toFixed(2)}%`, color: '#d29922' },
                  { label: '夏普比率', value: detail.sharpe_ratio?.toFixed(2) || '-', color: '#e6edf3' },
                  { label: '交易次数', value: detail.total_trades, color: '#e6edf3' },
                  { label: '胜率', value: `${(detail.win_rate * 100).toFixed(1)}%`, color: '#3fb950' },
                ].map(item => (
                  <div key={item.label} className="card" style={{ padding: '12px 14' }}>
                    <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 2 }}>{item.label}</div>
                    <div style={{ fontSize: 18, fontWeight: 600, color: item.color }}>
                      {item.value}
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 12, fontSize: 12, color: '#595e6b' }}>
                {detail.start_date} ~ {detail.end_date} | 初始资金: {(detail.initial_capital || 100000).toLocaleString()}
              </div>
            </div>

            {/* 交易记录 */}
            <div className="card" style={{ padding: 20 }}>
              <h3 style={{ fontSize: 15, color: '#e6edf3', marginBottom: 12 }}>交易记录</h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #2d3343' }}>
                      <th style={{ textAlign: 'left', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>日期</th>
                      <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>方向</th>
                      <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>价格</th>
                      <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>数量</th>
                      <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>收益</th>
                      <th style={{ textAlign: 'right', padding: '8px 12px', color: '#8b949e', fontWeight: 400 }}>总资产</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(detail.trades || []).map((t, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #1c2333' }}>
                        <td style={{ padding: '8px 12px', color: '#e6edf3' }}>
                          {t.date?.slice(0, 10) || '-'}
                        </td>
                        <td style={{
                          padding: '8px 12px',
                          textAlign: 'right',
                          color: t.side === 'buy' ? '#3fb950' : '#f85149',
                        }}>
                          {t.side === 'buy' ? '买入' : '卖出'}
                        </td>
                        <td style={{ padding: '8px 12px', textAlign: 'right', color: '#e6edf3' }}>
                          {t.price?.toFixed(2) || '-'}
                        </td>
                        <td style={{ padding: '8px 12px', textAlign: 'right', color: '#e6edf3' }}>
                          {t.quantity || '-'}
                        </td>
                        <td style={{
                          padding: '8px 12px',
                          textAlign: 'right',
                          color: (t.pnl || 0) >= 0 ? '#3fb950' : '#f85149',
                        }}>
                          {t.pnl ? `${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}` : '-'}
                        </td>
                        <td style={{ padding: '8px 12px', textAlign: 'right', color: '#e6edf3' }}>
                          {t.total_capital ? t.total_capital.toFixed(2) : '-'}
                        </td>
                      </tr>
                    ))}
                    {(!detail.trades || detail.trades.length === 0) && (
                      <tr>
                        <td colSpan={6} style={{ padding: 20, textAlign: 'center', color: '#595e6b' }}>
                          无交易记录
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
