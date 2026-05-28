import { nodeTypes } from './nodes'

const STRATEGY_OPTIONS = [
  { id: 'dual_ma', name: '双均线策略' },
  { id: 'rsi', name: 'RSI 策略' },
  { id: 'macd', name: 'MACD 策略' },
  { id: 'bollinger', name: '布林带策略' },
]

export default function ConfigPanel({ node, onUpdate }) {
  if (!node) {
    return (
      <div style={{
        width: 280,
        flexShrink: 0,
        borderLeft: '1px solid #21262d',
        padding: 20,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#595e6b',
        fontSize: 13,
        gap: 8,
      }}>
        <div style={{ fontSize: 32 }}>👈</div>
        <div>选择一个节点查看配置</div>
      </div>
    )
  }

  const def = nodeTypes[node.type]

  const updateData = (key, value) => {
    onUpdate(node.id, { ...node.data, [key]: value })
  }

  const updateParams = (key, value) => {
    const params = { ...(node.data?.params?.params || {}), [key]: value }
    updateData('params', { ...node.data?.params, params })
  }

  return (
    <div style={{
      width: 280,
      flexShrink: 0,
      borderLeft: '1px solid #21262d',
      padding: 20,
      overflow: 'auto',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <span style={{ fontSize: 18 }}>{def?.icon}</span>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: '#e6edf3' }}>{def?.label}</div>
          <div style={{ fontSize: 11, color: '#595e6b' }}>{def?.description}</div>
        </div>
      </div>

      {/* 数据源配置 */}
      {node.type === 'dataSource' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 4 }}>股票代码</label>
            <input
              className="input"
              value={node.data?.symbol || ''}
              onChange={e => updateData('symbol', e.target.value)}
              placeholder="600519"
            />
          </div>
          <div>
            <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 4 }}>回测周期（天）</label>
            <input
              className="input"
              type="number"
              value={node.data?.days || 365}
              onChange={e => updateData('days', parseInt(e.target.value) || 365)}
            />
          </div>
        </div>
      )}

      {/* 策略配置 */}
      {node.type === 'strategy' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 4 }}>策略类型</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {STRATEGY_OPTIONS.map(s => (
                <button
                  key={s.id}
                  onClick={() => updateData('params', { type: s.id, params: {} })}
                  style={{
                    textAlign: 'left',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: `1px solid ${node.data?.params?.type === s.id ? '#58a6ff' : '#2d3343'}`,
                    backgroundColor: node.data?.params?.type === s.id ? 'rgba(88,166,255,0.08)' : 'transparent',
                    color: node.data?.params?.type === s.id ? '#e6edf3' : '#8b949e',
                    cursor: 'pointer',
                    fontSize: 13,
                  }}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 回测配置 */}
      {node.type === 'backtest' && (
        <div>
          <label style={{ display: 'block', color: '#8b949e', fontSize: 12, marginBottom: 4 }}>初始资金</label>
          <input
            className="input"
            type="number"
            value={node.data?.capital || 100000}
            onChange={e => updateData('capital', parseInt(e.target.value) || 100000)}
          />
        </div>
      )}

      {node.type === 'indicators' && (
        <div style={{ color: '#8b949e', fontSize: 12, lineHeight: 1.8 }}>
          自动计算以下指标：
          <div style={{ marginTop: 8 }}>
            {['MA5 / MA10 / MA20 / MA60', 'MACD / Signal / Histogram', 'RSI(14)', '布林带 (20, 2)'].map((item, i) => (
              <div key={i} style={{ padding: '4px 0', color: '#595e6b' }}>• {item}</div>
            ))}
          </div>
        </div>
      )}

      {node.type === 'result' && (
        <div style={{ color: '#8b949e', fontSize: 12 }}>
          此节点展示回测结果，连接回测引擎节点后运行即可查看。
        </div>
      )}
    </div>
  )
}
