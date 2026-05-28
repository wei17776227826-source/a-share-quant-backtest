import { useState, useEffect } from 'react'
import { useAuth } from '../AuthContext'
import { backtest } from '../api'
import { useNavigate } from 'react-router-dom'
import KLineChart from '../components/KLineChart'
import EquityCurveChart from '../components/EquityCurveChart'

const STRATEGIES = [
  { id: 'dual_ma', name: '双均线策略', desc: '短期均线上穿长期均线买入，下穿卖出', params: [
    { key: 'short_period', label: '短期均线', default: 5, min: 2, max: 50 },
    { key: 'long_period', label: '长期均线', default: 20, min: 10, max: 200 },
  ]},
  { id: 'rsi', name: 'RSI 策略', desc: 'RSI 低于超卖线买入，高于超买线卖出', params: [
    { key: 'period', label: 'RSI 周期', default: 14, min: 5, max: 50 },
    { key: 'oversold', label: '超卖线', default: 30, min: 10, max: 50 },
    { key: 'overbought', label: '超买线', default: 70, min: 50, max: 90 },
  ]},
  { id: 'macd', name: 'MACD 策略', desc: 'MACD 金叉买入，死叉卖出', params: [] },
  { id: 'bollinger', name: '布林带策略', desc: '价格触及下轨买入，触及上轨卖出', params: [] },
]

const DAYS_OPTIONS = [30, 60, 90, 180, 365, 730]
const CAPITAL_OPTIONS = [10000, 50000, 100000, 500000, 1000000]

export default function Backtest() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [symbol, setSymbol] = useState('600519')
  const [strategyId, setStrategyId] = useState('dual_ma')
  const [days, setDays] = useState(365)
  const [capital, setCapital] = useState(100000)
  const [params, setParams] = useState({})
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [klineData, setKlineData] = useState(null)
  const [klineLoading, setKlineLoading] = useState(false)

  const currentStrategy = STRATEGIES.find(s => s.id === strategyId)

  // 输入股票代码后自动加载 K 线数据
  useEffect(() => {
    if (!symbol.trim() || symbol.length < 6) return
    const timer = setTimeout(async () => {
      setKlineLoading(true)
      try {
        const res = await fetch(`/api/market/kline?symbol=${symbol.trim()}&days=${days}`)
        if (res.ok) {
          const data = await res.json()
          setKlineData(data.klines)
        }
      } catch {
        // 忽略自动加载失败
      } finally {
        setKlineLoading(false)
      }
    }, 800)
    return () => clearTimeout(timer)
  }, [symbol, days])

  const handleParamChange = (key, value) => {
    setParams(prev => ({ ...prev, [key]: Number(value) }))
  }

  const handleRun = async () => {
    if (!user) {
      navigate('/login')
      return
    }
    setRunning(true)
    setError('')
    setResult(null)
    try {
      const data = await backtest.run({
        strategy_type: strategyId,
        symbol: symbol.trim(),
        days,
        initial_capital: capital,
        data_source: 'real',
        parameters: params,
      })
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || '回测执行失败')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 24, padding: 24, maxWidth: 1400, margin: '0 auto' }}>
      {/* 左侧配置区 */}
      <div className="card" style={{ width: 380, padding: 24, flexShrink: 0 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: '#e6edf3', marginBottom: 24 }}>
          回测配置
        </h2>

        {/* 股票代码 */}
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', color: '#8b949e', fontSize: 13, marginBottom: 6 }}>
            股票代码
          </label>
          <input
            className="input"
            value={symbol}
            onChange={e => setSymbol(e.target.value)}
            placeholder="如 600519、000001"
          />
          <div style={{ color: '#595e6b', fontSize: 12, marginTop: 4 }}>
            输入 A 股代码（6位数字）
          </div>
        </div>

        {/* 策略选择 */}
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', color: '#8b949e', fontSize: 13, marginBottom: 6 }}>
            策略类型
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {STRATEGIES.map(s => (
              <button
                key={s.id}
                onClick={() => { setStrategyId(s.id); setParams({}) }}
                style={{
                  textAlign: 'left',
                  padding: '10px 14px',
                  borderRadius: 8,
                  border: `1px solid ${strategyId === s.id ? '#58a6ff' : '#2d3343'}`,
                  backgroundColor: strategyId === s.id ? 'rgba(88,166,255,0.08)' : 'transparent',
                  color: strategyId === s.id ? '#e6edf3' : '#8b949e',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontWeight: 500, fontSize: 14 }}>{s.name}</div>
                {s.desc && (
                  <div style={{ fontSize: 12, marginTop: 2, color: '#595e6b' }}>{s.desc}</div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* 策略参数 */}
        {currentStrategy && currentStrategy.params.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', color: '#8b949e', fontSize: 13, marginBottom: 6 }}>
              策略参数
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {currentStrategy.params.map(p => (
                <div key={p.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ color: '#8b949e', fontSize: 12 }}>{p.label}</span>
                    <span style={{ color: '#e6edf3', fontSize: 12 }}>{params[p.key] || p.default}</span>
                  </div>
                  <input
                    type="range"
                    min={p.min}
                    max={p.max}
                    value={params[p.key] || p.default}
                    onChange={e => handleParamChange(p.key, e.target.value)}
                    style={{ width: '100%', accentColor: '#58a6ff' }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 天数选择 */}
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', color: '#8b949e', fontSize: 13, marginBottom: 6 }}>
            回测周期
          </label>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {DAYS_OPTIONS.map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 6,
                  border: `1px solid ${days === d ? '#58a6ff' : '#2d3343'}`,
                  backgroundColor: days === d ? 'rgba(88,166,255,0.08)' : 'transparent',
                  color: days === d ? '#e6edf3' : '#8b949e',
                  cursor: 'pointer',
                  fontSize: 13,
                }}
              >
                {d >= 365 ? `${d / 365}年` : `${d}天`}
              </button>
            ))}
          </div>
        </div>

        {/* 初始资金 */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', color: '#8b949e', fontSize: 13, marginBottom: 6 }}>
            初始资金
          </label>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {CAPITAL_OPTIONS.map(c => (
              <button
                key={c}
                onClick={() => setCapital(c)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 6,
                  border: `1px solid ${capital === c ? '#58a6ff' : '#2d3343'}`,
                  backgroundColor: capital === c ? 'rgba(88,166,255,0.08)' : 'transparent',
                  color: capital === c ? '#e6edf3' : '#8b949e',
                  cursor: 'pointer',
                  fontSize: 13,
                }}
              >
                {c >= 10000 ? `${c / 10000}万` : c}
              </button>
            ))}
          </div>
        </div>

        {/* 运行按钮 */}
        <button
          className="btn btn-primary"
          style={{ width: '100%', padding: '12px 0', fontSize: 15 }}
          onClick={handleRun}
          disabled={running || !symbol.trim()}
        >
          {running ? '回测运行中...' : '▶ 运行回测'}
        </button>

        {error && (
          <div style={{
            marginTop: 16,
            padding: '10px 14px',
            borderRadius: 8,
            backgroundColor: 'rgba(248,81,73,0.1)',
            color: '#f85149',
            fontSize: 13,
          }}>
            {error}
          </div>
        )}
      </div>

      {/* 右侧结果区 */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {!result ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* K 线图 */}
            <div className="card" style={{ padding: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 style={{ fontSize: 15, color: '#e6edf3' }}>
                  {symbol || '股票代码'} K 线图
                </h3>
                {klineLoading && <span style={{ color: '#8b949e', fontSize: 12 }}>加载中...</span>}
              </div>
              {klineData ? (
                <KLineChart data={klineData} height={450} />
              ) : (
                <div style={{
                  height: 450,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#595e6b',
                  gap: 8,
                }}>
                  <div style={{ fontSize: 36 }}>📊</div>
                  <div style={{ color: '#8b949e' }}>输入股票代码后自动加载行情</div>
                  <div style={{ fontSize: 12 }}>示例：600519（茅台）、000001（平安）</div>
                </div>
              )}
            </div>
            {/* 空状态提示 */}
            <div className="card" style={{
              padding: 40,
              textAlign: 'center',
              color: '#595e6b',
            }}>
              <div style={{ fontSize: 14 }}>左侧配置策略参数，点击运行回测查看结果</div>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* 概要信息 */}
            <div className="card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <span className="badge badge-blue">{result.strategy_name}</span>
                <span style={{ color: '#8b949e', fontSize: 13 }}>{result.symbol}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                {[
                  { label: '总收益率', value: `${(result.total_return * 100).toFixed(2)}%`, color: result.total_return >= 0 ? '#3fb950' : '#f85149' },
                  { label: '年化收益', value: `${(result.annual_return * 100).toFixed(2)}%`, color: '#58a6ff' },
                  { label: '最大回撤', value: `${(result.max_drawdown * 100).toFixed(2)}%`, color: '#d29922' },
                  { label: '夏普比率', value: result.sharpe_ratio.toFixed(2), color: '#e6edf3' },
                  { label: '总交易次数', value: result.total_trades, color: '#e6edf3' },
                  { label: '胜率', value: `${(result.win_rate * 100).toFixed(1)}%`, color: '#3fb950' },
                ].map(item => (
                  <div key={item.label} className="card" style={{ padding: '14px 16' }}>
                    <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 4 }}>{item.label}</div>
                    <div style={{ fontSize: 20, fontWeight: 600, color: item.color }}>
                      {item.value}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 权益曲线 */}
            <div className="card" style={{ padding: 16 }}>
              <h3 style={{ fontSize: 15, color: '#e6edf3', marginBottom: 12 }}>权益曲线</h3>
              {result.equity_curve && result.equity_curve.length > 0 ? (
                <EquityCurveChart data={result.equity_curve} height={250} />
              ) : (
                <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#595e6b' }}>
                  无权益数据
                </div>
              )}
            </div>

            {/* 交易列表 */}
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
                    </tr>
                  </thead>
                  <tbody>
                    {(result.trades || []).map((t, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #1c2333' }}>
                        <td style={{ padding: '8px 12px', color: '#e6edf3' }}>{t.date?.slice(0, 10)}</td>
                        <td style={{
                          padding: '8px 12px',
                          textAlign: 'right',
                          color: t.side === 'buy' ? '#3fb950' : '#f85149',
                        }}>
                          {t.side === 'buy' ? '买入' : '卖出'}
                        </td>
                        <td style={{ padding: '8px 12px', textAlign: 'right', color: '#e6edf3' }}>
                          {t.price?.toFixed(2)}
                        </td>
                        <td style={{ padding: '8px 12px', textAlign: 'right', color: '#e6edf3' }}>
                          {t.quantity}
                        </td>
                        <td style={{
                          padding: '8px 12px',
                          textAlign: 'right',
                          color: (t.pnl || 0) >= 0 ? '#3fb950' : '#f85149',
                        }}>
                          {t.pnl ? `${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}` : '-'}
                        </td>
                      </tr>
                    ))}
                    {(!result.trades || result.trades.length === 0) && (
                      <tr>
                        <td colSpan={5} style={{ padding: '20px', textAlign: 'center', color: '#595e6b' }}>
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
