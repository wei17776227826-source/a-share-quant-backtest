import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { industry, backtest } from '../api'

// 产业链层级颜色映射
const LAYER_COLORS = [
  '#58a6ff', '#3fb950', '#d29922', '#f85149', '#bc8cff',
  '#79c0ff', '#56d364', '#e3b341', '#ff7b72', '#d2a8ff',
]

export default function IndustryResearch() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [chains, setChains] = useState([])
  const [selectedChain, setSelectedChain] = useState('')
  const [loading, setLoading] = useState(true)
  const [researching, setResearching] = useState(false)
  const [currentReport, setCurrentReport] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState(null)
  const [scoredReport, setScoredReport] = useState(null)

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    loadChains()
    loadHistory()
  }, [user])

  const loadChains = async () => {
    try {
      const data = await industry.chains()
      setChains(data.chains || [])
      if (data.chains?.length > 0) {
        setSelectedChain(data.chains[0].id)
      }
    } catch (e) {
      setError('加载产业链列表失败')
    }
    setLoading(false)
  }

  const loadHistory = async () => {
    try {
      const data = await industry.list()
      setHistory(data.results || [])
    } catch {
      // ignore
    }
  }

  const handleResearch = async () => {
    if (!selectedChain) return
    setResearching(true)
    setError(null)
    setCurrentReport(null)
    setScoredReport(null)

    try {
      const result = await industry.research(selectedChain)
      setCurrentReport(result.report)
      // 刷新历史
      loadHistory()
    } catch (e) {
      setError(e.response?.data?.detail || '研究执行失败')
    } finally {
      setResearching(false)
    }
  }

  const handleBacktest = async (symbol, companyName) => {
    try {
      const result = await backtest.run({
        strategy_type: 'dual_ma',
        symbol: symbol,
        days: 365,
        initial_capital: 100000,
        data_source: 'real',
        parameters: {},
      })
      navigate('/results')
    } catch (e) {
      alert(e.response?.data?.detail || '回测执行失败')
    }
  }

  const handleViewDetail = (reportId) => {
    navigate(`/industry/${reportId}`)
  }

  const handleDelete = async (id) => {
    if (!confirm('确定删除此研究报告？')) return
    try {
      await industry.delete(id)
      loadHistory()
    } catch {
      // ignore
    }
  }

  const selectedChainInfo = chains.find(c => c.id === selectedChain)

  if (!user) return null

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      {/* 头部 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#e6edf3', marginBottom: 4 }}>产业链研究</h1>
          <p style={{ color: '#8b949e', fontSize: 14 }}>
            基于 Serenity 方法论的产业链瓶颈研究 —— 选行业 → 拆层级 → 找卡点 → 排序 → 回测验证
          </p>
        </div>
      </div>

      {error && (
        <div className="card" style={{ padding: 16, marginBottom: 16, borderLeft: '3px solid #f85149', color: '#f85149' }}>
          {error}
        </div>
      )}

      {/* 行业选择 + 研究按钮 */}
      <div className="card" style={{ padding: 24, marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 250 }}>
            <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 6 }}>选择产业链</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {chains.map(chain => (
                <button
                  key={chain.id}
                  onClick={() => setSelectedChain(chain.id)}
                  style={{
                    textAlign: 'left',
                    padding: '10px 14px',
                    borderRadius: 8,
                    border: `1px solid ${selectedChain === chain.id ? '#58a6ff' : '#2d3343'}`,
                    backgroundColor: selectedChain === chain.id ? 'rgba(88,166,255,0.08)' : 'transparent',
                    color: selectedChain === chain.id ? '#e6edf3' : '#8b949e',
                    cursor: 'pointer',
                    fontSize: 13,
                  }}
                >
                  <div style={{ fontWeight: 500, fontSize: 14 }}>{chain.name}</div>
                  <div style={{ fontSize: 11, color: '#595e6b', marginTop: 2 }}>
                    {chain.description} · {chain.layer_count} 个层级
                  </div>
                </button>
              ))}
            </div>
          </div>

          <button
            className="btn btn-primary"
            style={{ padding: '12px 32px', fontSize: 15, whiteSpace: 'nowrap' }}
            onClick={handleResearch}
            disabled={researching || !selectedChain}
          >
            {researching ? (
              <>
                <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite', marginRight: 8 }}>⟳</span>
                研究中...
              </>
            ) : '🔬 执行产业链研究'}
          </button>
        </div>
      </div>

      {/* 研究报告结果 */}
      {currentReport && (
        <div className="card" style={{ padding: 24, marginBottom: 24 }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: 20, paddingBottom: 16, borderBottom: '1px solid #21262d',
          }}>
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: '#e6edf3' }}>
                {currentReport.industry_name} · 研究报告
              </h2>
              <p style={{ color: '#8b949e', fontSize: 13, marginTop: 4 }}>
                {currentReport.description}
              </p>
            </div>
            <div style={{ textAlign: 'right', color: '#595e6b', fontSize: 12 }}>
              <div>{currentReport.summary?.total_layers} 个层级</div>
              <div>{currentReport.summary?.total_companies} 个标的</div>
            </div>
          </div>

          {/* 产业链层级图 */}
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 15, color: '#e6edf3', marginBottom: 12 }}>产业链层级</h3>
            <div style={{
              display: 'flex', gap: 6, flexWrap: 'wrap',
              padding: 16, backgroundColor: '#161b22', borderRadius: 8,
            }}>
              {currentReport.layers?.map((layer, idx) => (
                <div
                  key={layer.layer_id}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 6,
                    border: `1px solid ${LAYER_COLORS[idx % LAYER_COLORS.length]}44`,
                    backgroundColor: `${LAYER_COLORS[idx % LAYER_COLORS.length]}11`,
                    fontSize: 12,
                    color: '#e6edf3',
                  }}
                >
                  <span style={{ color: LAYER_COLORS[idx % LAYER_COLORS.length], fontWeight: 600 }}>
                    {idx + 1}.
                  </span>
                  {' '}{layer.layer_name}
                  <span style={{ color: '#595e6b', marginLeft: 6 }}>
                    ({layer.company_count}家)
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 层级详细公司列表 */}
          <h3 style={{ fontSize: 15, color: '#e6edf3', marginBottom: 12 }}>各层级标的</h3>
          {currentReport.layers?.map((layer, idx) => (
            <div key={layer.layer_id} style={{ marginBottom: layer.companies.length ? 16 : 8 }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8,
              }}>
                <span style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  width: 22, height: 22, borderRadius: '50%',
                  backgroundColor: LAYER_COLORS[idx % LAYER_COLORS.length],
                  color: '#0d1117', fontSize: 11, fontWeight: 700,
                }}>{idx + 1}</span>
                <h4 style={{ fontSize: 14, color: '#e6edf3', fontWeight: 600 }}>
                  {layer.layer_name}
                </h4>
                <span style={{ color: '#595e6b', fontSize: 12 }}>
                  — {layer.company_count} 个标的
                </span>
              </div>

              {layer.companies.length === 0 ? (
                <p style={{ color: '#595e6b', fontSize: 12, marginLeft: 30, fontStyle: 'italic' }}>
                  暂无映射公司（可扩展）
                </p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginLeft: 30 }}>
                  {layer.companies.map((company, ci) => (
                    <div key={company.symbol} className="card" style={{
                      padding: '10px 14px',
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      border: '1px solid #21262d',
                    }}>
                      <div>
                        <div style={{ fontSize: 13, color: '#e6edf3', fontWeight: 500 }}>
                          {company.name}
                          <span style={{ color: '#595e6b', fontSize: 11, marginLeft: 8 }}>
                            {company.symbol}
                          </span>
                        </div>
                        <div style={{ fontSize: 11, color: '#8b949e', marginTop: 2 }}>
                          {company.desc}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          className="btn btn-primary"
                          style={{ padding: '4px 10px', fontSize: 11 }}
                          onClick={() => handleBacktest(company.symbol, company.name)}
                          title="回测此标的"
                        >
                          📊 回测
                        </button>
                        <button
                          className="btn btn-ghost"
                          style={{ padding: '4px 10px', fontSize: 11 }}
                          onClick={() => window.open(`https://xueqiu.com/S/${company.symbol}`, '_blank')}
                          title="雪球查看"
                        >
                          查看
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* 研究来源 */}
          {currentReport.keywords && (
            <div style={{ marginTop: 16, padding: '12px 16px', backgroundColor: '#161b22', borderRadius: 8 }}>
              <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 6 }}>研究方向提示</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {currentReport.keywords.map(kw => (
                  <span key={kw} style={{
                    padding: '2px 8px', borderRadius: 4,
                    backgroundColor: 'rgba(88,166,255,0.1)', color: '#58a6ff',
                    fontSize: 11,
                  }}>
                    {kw}
                  </span>
                ))}
              </div>
              <div style={{ fontSize: 11, color: '#595e6b', marginTop: 6 }}>
                数据源建议: {currentReport.source_hints?.join('、')}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 研究历史 */}
      <div style={{ marginTop: 32 }}>
        <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 16 }}>研究历史</h3>
        {history.length === 0 ? (
          <div className="card" style={{ padding: 40, textAlign: 'center', color: '#595e6b', fontSize: 14 }}>
            还没有产业链研究记录
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {history.map(item => (
              <div key={item.id} className="card" style={{
                padding: '14px 18px', display: 'flex', justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontSize: 14, color: '#e6edf3', fontWeight: 500 }}>
                    {item.industry_name}
                  </div>
                  <div style={{ fontSize: 12, color: '#595e6b', marginTop: 2 }}>
                    {item.summary?.layer_chain?.substring(0, 80)}
                    {(item.summary?.layer_chain?.length || 0) > 80 ? '...' : ''}
                  </div>
                  <div style={{ fontSize: 11, color: '#595e6b', marginTop: 2 }}>
                    {item.summary?.total_companies} 个标的 · {item.created_at?.slice(0, 16) || ''}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button
                    className="btn btn-ghost"
                    style={{ padding: '4px 10px', fontSize: 11 }}
                    onClick={() => handleViewDetail(item.id)}
                  >
                    查看报告
                  </button>
                  <button
                    className="btn btn-ghost"
                    style={{ padding: '4px 10px', fontSize: 11, color: '#f85149', borderColor: 'rgba(248,81,73,0.3)' }}
                    onClick={() => handleDelete(item.id)}
                  >
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
