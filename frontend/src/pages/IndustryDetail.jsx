import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'
import { industry } from '../api'

const LAYER_COLORS = [
  '#58a6ff', '#3fb950', '#d29922', '#f85149', '#bc8cff',
  '#79c0ff', '#56d364', '#e3b341', '#ff7b72', '#d2a8ff',
]

export default function IndustryDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()

  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    loadReport()
  }, [id, user])

  const loadReport = async () => {
    setLoading(true)
    try {
      const data = await industry.detail(id)
      setReport(data)
    } catch (e) {
      setError(e.response?.data?.detail || '加载报告失败')
    }
    setLoading(false)
  }

  if (!user) return null
  if (loading) return (
    <div style={{ padding: 40, textAlign: 'center', color: '#595e6b' }}>
      加载中...
    </div>
  )
  if (error) return (
    <div style={{ padding: 40, textAlign: 'center', color: '#f85149' }}>
      {error}
    </div>
  )
  if (!report) return null

  const r = report.report

  return (
    <div style={{ padding: 24, maxWidth: 1000, margin: '0 auto' }}>
      {/* 面包屑 */}
      <div style={{ marginBottom: 20 }}>
        <button
          onClick={() => navigate(-1)}
          className="btn btn-ghost"
          style={{ padding: '4px 12px', fontSize: 12 }}
        >
          ← 返回
        </button>
      </div>

      {/* 报告头部 */}
      <div className="card" style={{ padding: 24, marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#e6edf3', marginBottom: 8 }}>
          {r.industry_name} · 深度研究报告
        </h1>
        <p style={{ color: '#8b949e', fontSize: 13, marginBottom: 12 }}>{r.description}</p>
        <div style={{ display: 'flex', gap: 24, color: '#595e6b', fontSize: 12 }}>
          <span>市场: {r.market}</span>
          <span>层级: {r.summary?.total_layers}</span>
          <span>标的: {r.summary?.total_companies}</span>
          <span>时间: {r.created_at?.slice(0, 10)}</span>
        </div>
      </div>

      {/* 产业链全景图 */}
      <div className="card" style={{ padding: 24, marginBottom: 24 }}>
        <h2 style={{ fontSize: 17, fontWeight: 600, color: '#e6edf3', marginBottom: 16 }}>
          产业链全景图
        </h2>

        {/* 层级链可视化 */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap',
          padding: 16, backgroundColor: '#161b22', borderRadius: 8, marginBottom: 16,
        }}>
          {r.layers?.map((layer, idx) => (
            <div key={layer.layer_id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{
                padding: '6px 12px', borderRadius: 6, fontSize: 12, whiteSpace: 'nowrap',
                border: `1px solid ${LAYER_COLORS[idx % LAYER_COLORS.length]}44`,
                backgroundColor: `${LAYER_COLORS[idx % LAYER_COLORS.length]}11`,
                color: LAYER_COLORS[idx % LAYER_COLORS.length],
              }}>
                {idx + 1}. {layer.layer_name}
                <span style={{ opacity: 0.5, marginLeft: 4 }}>({layer.company_count})</span>
              </div>
              {idx < r.layers.length - 1 && (
                <span style={{ color: '#30363d', fontSize: 16 }}>→</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 各层级详细分析 */}
      <h2 style={{ fontSize: 17, fontWeight: 600, color: '#e6edf3', marginBottom: 16 }}>
        层级分析
      </h2>

      {r.layers?.map((layer, idx) => (
        <div key={layer.layer_id} className="card" style={{ padding: 20, marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              width: 24, height: 24, borderRadius: '50%',
              backgroundColor: LAYER_COLORS[idx % LAYER_COLORS.length],
              color: '#0d1117', fontSize: 12, fontWeight: 700,
            }}>{layer.layer_rank}</span>
            <h3 style={{ fontSize: 15, color: '#e6edf3', fontWeight: 600 }}>
              {layer.layer_name}
            </h3>
            <span style={{ color: '#595e6b', fontSize: 12 }}>
              — 层级排序: #{layer.layer_rank}
            </span>
          </div>

          {layer.companies.length === 0 ? (
            <div style={{
              padding: 16, backgroundColor: '#161b22', borderRadius: 6,
              color: '#595e6b', fontSize: 12, fontStyle: 'italic',
              textAlign: 'center',
            }}>
              此层级暂无映射标的（可扩展）
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {layer.companies.map((company, ci) => (
                <div key={company.symbol} style={{
                  padding: '10px 14px', backgroundColor: '#161b22', borderRadius: 6,
                  borderLeft: `3px solid ${LAYER_COLORS[idx % LAYER_COLORS.length]}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 14, color: '#e6edf3', fontWeight: 500 }}>
                        {company.name}
                        <span style={{ color: '#595e6b', fontSize: 11, marginLeft: 8 }}>
                          {company.symbol}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: '#8b949e', marginTop: 2 }}>
                        {company.desc}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}

      {/* 研究关键词 */}
      <div className="card" style={{ padding: 20, marginTop: 8 }}>
        <h3 style={{ fontSize: 14, color: '#e6edf3', marginBottom: 8 }}>研究关键词</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 12 }}>
          {r.keywords?.map(kw => (
            <span key={kw} style={{
              padding: '3px 10px', borderRadius: 4,
              backgroundColor: 'rgba(88,166,255,0.1)', color: '#58a6ff',
              fontSize: 12,
            }}>
              {kw}
            </span>
          ))}
        </div>
        <div style={{ fontSize: 12, color: '#8b949e' }}>
          <span style={{ color: '#595e6b' }}>建议数据源：</span>
          {r.source_hints?.join('、')}
        </div>
      </div>
    </div>
  )
}
