import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { strategies, backtest } from '../api'

const STRATEGY_CONFIGS = {
  dual_ma: {
    name: '双均线策略',
    desc: '短期均线上穿长期均线买入，下穿卖出',
    params: [
      { key: 'short_period', label: '短期均线', default: 5, min: 2, max: 50 },
      { key: 'long_period', label: '长期均线', default: 20, min: 10, max: 200 },
    ],
  },
  rsi: {
    name: 'RSI 策略',
    desc: 'RSI 低于超卖线买入，高于超买线卖出',
    params: [
      { key: 'period', label: 'RSI 周期', default: 14, min: 5, max: 50 },
      { key: 'oversold', label: '超卖线', default: 30, min: 10, max: 50 },
      { key: 'overbought', label: '超买线', default: 70, min: 50, max: 90 },
    ],
  },
  macd: {
    name: 'MACD 策略',
    desc: 'MACD 金叉买入，死叉卖出',
    params: [],
  },
  bollinger: {
    name: '布林带策略',
    desc: '价格触及下轨买入，触及上轨卖出',
    params: [],
  },
}

export default function Marketplace() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [strategyList, setStrategyList] = useState([])
  const [loading, setLoading] = useState(true)
  const [showEditor, setShowEditor] = useState(false)
  const [editId, setEditId] = useState(null)
  const [runningId, setRunningId] = useState(null)

  // 编辑器表单状态
  const [form, setForm] = useState({
    name: '',
    description: '',
    strategy_type: 'dual_ma',
    parameters: {},
    symbol: '600519',
    days: 365,
  })

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    loadStrategies()
  }, [user])

  const loadStrategies = async () => {
    setLoading(true)
    try {
      const data = await strategies.list()
      setStrategyList(data.strategies || [])
    } catch { /* ignore */ }
    setLoading(false)
  }

  const openCreate = () => {
    setEditId(null)
    setForm({ name: '', description: '', strategy_type: 'dual_ma', parameters: {}, symbol: '600519', days: 365 })
    setShowEditor(true)
  }

  const openEdit = (s) => {
    setEditId(s.id)
    const params = s.parameters || {}
    setForm({
      name: s.name,
      description: s.description || '',
      strategy_type: s.strategy_type || 'dual_ma',
      parameters: params,
      symbol: '600519',
      days: 365,
    })
    setShowEditor(true)
  }

  const handleSave = async () => {
    if (!form.name.trim()) return
    try {
      if (editId) {
        await strategies.update(editId, {
          name: form.name,
          description: form.description,
          strategy_type: form.strategy_type,
          parameters: form.parameters,
        })
      } else {
        await strategies.create({
          name: form.name,
          description: form.description,
          strategy_type: form.strategy_type,
          parameters: form.parameters,
        })
      }
      setShowEditor(false)
      loadStrategies()
    } catch (err) {
      alert(err.response?.data?.detail || '保存失败')
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除此策略？')) return
    try {
      await strategies.delete(id)
      loadStrategies()
    } catch { /* ignore */ }
  }

  const handleRun = async (s) => {
    setRunningId(s.id)
    try {
      const result = await backtest.run({
        strategy_type: s.strategy_type || 'dual_ma',
        symbol: '600519',
        days: 365,
        initial_capital: 100000,
        data_source: 'real',
        parameters: s.parameters || {},
      })
      // 跳到结果页
      navigate('/results')
    } catch (err) {
      alert(err.response?.data?.detail || '回测执行失败')
    } finally {
      setRunningId(null)
    }
  }

  const getStrategyInfo = (type) => STRATEGY_CONFIGS[type] || { name: type, desc: '', params: [] }

  if (!user) return null

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      {/* 头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3', marginBottom: 4 }}>我的策略</h1>
          <p style={{ color: '#8b949e', fontSize: 14 }}>创建、编辑和管理你的量化策略</p>
        </div>
        <button className="btn btn-primary" style={{ fontSize: 14, padding: '10px 24px' }} onClick={openCreate}>
          + 新建策略
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: '#595e6b', padding: 60 }}>加载中...</div>
      ) : strategyList.length === 0 && !showEditor ? (
        <div className="card" style={{ padding: 60, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>📭</div>
          <div style={{ color: '#8b949e', marginBottom: 16 }}>还没有策略，点击右上角新建</div>
          <button className="btn btn-primary" onClick={openCreate}>+ 新建策略</button>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 24 }}>
          {/* 策略列表 */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {strategyList.map(s => {
              const info = getStrategyInfo(s.strategy_type)
              return (
                <div key={s.id} className="card" style={{ padding: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                        <h3 style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>{s.name}</h3>
                        <span className="badge badge-blue">{info.name}</span>
                      </div>
                      {s.description && (
                        <p style={{ color: '#8b949e', fontSize: 13, marginBottom: 8 }}>{s.description}</p>
                      )}
                      <div style={{ display: 'flex', gap: 16, fontSize: 12, color: '#595e6b' }}>
                        <span>创建于 {s.created_at?.slice(0, 10)}</span>
                        {s.updated_at && <span>更新于 {s.updated_at?.slice(0, 10)}</span>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
                      <button
                        className="btn btn-primary"
                        style={{ padding: '6px 14px', fontSize: 12 }}
                        onClick={() => handleRun(s)}
                        disabled={runningId === s.id}
                      >
                        {runningId === s.id ? '运行中...' : '▶ 回测'}
                      </button>
                      <button
                        className="btn btn-ghost"
                        style={{ padding: '6px 14px', fontSize: 12 }}
                        onClick={() => openEdit(s)}
                      >
                        编辑
                      </button>
                      <button
                        className="btn btn-ghost"
                        style={{ padding: '6px 14px', fontSize: 12, color: '#f85149', borderColor: 'rgba(248,81,73,0.3)' }}
                        onClick={() => handleDelete(s.id)}
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* 编辑器侧边面板 */}
          {showEditor && (
            <div className="card" style={{ width: 400, padding: 24, flexShrink: 0, height: 'fit-content' }}>
              <h3 style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3', marginBottom: 20 }}>
                {editId ? '编辑策略' : '新建策略'}
              </h3>

              {/* 策略名称 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 4 }}>策略名称</label>
                <input
                  className="input"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  placeholder="输入策略名称"
                />
              </div>

              {/* 描述 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 4 }}>描述（可选）</label>
                <textarea
                  className="input"
                  value={form.description}
                  onChange={e => setForm({ ...form, description: e.target.value })}
                  placeholder="策略说明"
                  style={{ minHeight: 60, resize: 'vertical' }}
                />
              </div>

              {/* 策略类型 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 4 }}>策略类型</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {Object.entries(STRATEGY_CONFIGS).map(([key, cfg]) => (
                    <button
                      key={key}
                      onClick={() => setForm({ ...form, strategy_type: key, parameters: {} })}
                      style={{
                        textAlign: 'left',
                        padding: '8px 12px',
                        borderRadius: 6,
                        border: `1px solid ${form.strategy_type === key ? '#58a6ff' : '#2d3343'}`,
                        backgroundColor: form.strategy_type === key ? 'rgba(88,166,255,0.08)' : 'transparent',
                        color: form.strategy_type === key ? '#e6edf3' : '#8b949e',
                        cursor: 'pointer',
                        fontSize: 13,
                      }}
                    >
                      <div style={{ fontWeight: 500 }}>{cfg.name}</div>
                      <div style={{ fontSize: 11, color: '#595e6b', marginTop: 2 }}>{cfg.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* 策略参数 */}
              {(() => {
                const cfg = STRATEGY_CONFIGS[form.strategy_type]
                if (!cfg || cfg.params.length === 0) return null
                return (
                  <div style={{ marginBottom: 16 }}>
                    <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 4 }}>参数调整</label>
                    {cfg.params.map(p => (
                      <div key={p.key} style={{ marginBottom: 10 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                          <span style={{ color: '#8b949e', fontSize: 12 }}>{p.label}</span>
                          <span style={{ color: '#e6edf3', fontSize: 12 }}>{form.parameters[p.key] || p.default}</span>
                        </div>
                        <input
                          type="range"
                          min={p.min}
                          max={p.max}
                          value={form.parameters[p.key] || p.default}
                          onChange={e => setForm({ ...form, parameters: { ...form.parameters, [p.key]: Number(e.target.value) } })}
                          style={{ width: '100%', accentColor: '#58a6ff' }}
                        />
                      </div>
                    ))}
                  </div>
                )
              })()}

              {/* 按钮 */}
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleSave} disabled={!form.name.trim()}>
                  保存
                </button>
                <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setShowEditor(false)}>
                  取消
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
