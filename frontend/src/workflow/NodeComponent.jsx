import { memo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { nodeTypes } from './nodes'

function BaseNode({ id, data, type, selected }) {
  const def = nodeTypes[type]
  if (!def) return null

  return (
    <div className="card" style={{
      width: 220,
      padding: 0,
      border: `1px solid ${selected ? def.color : '#2d3343'}`,
      boxShadow: selected ? `0 0 0 1px ${def.color}40` : 'none',
      overflow: 'hidden',
    }}>
      {/* 头部 */}
      <div style={{
        padding: '10px 14px',
        backgroundColor: `${def.color}15`,
        borderBottom: '1px solid #2d3343',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
      }}>
        <span style={{ fontSize: 16 }}>{def.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#e6edf3' }}>{def.label}</div>
          <div style={{ fontSize: 11, color: '#595e6b' }}>{def.description}</div>
        </div>
      </div>

      {/* 内容 */}
      <div style={{ padding: '10px 14px', fontSize: 12, color: '#8b949e' }}>
        {type === 'dataSource' && (
          <div>
            代码: <span style={{ color: '#e6edf3' }}>{data?.symbol || '600519'}</span>
            <br />
            周期: <span style={{ color: '#e6edf3' }}>{data?.days || 365}天</span>
          </div>
        )}
        {type === 'strategy' && (
          <div>
            策略: <span style={{ color: '#e6edf3' }}>{data?.params?.type || 'dual_ma'}</span>
          </div>
        )}
        {type === 'backtest' && (
          <div>
            资金: <span style={{ color: '#e6edf3' }}>{data?.capital?.toLocaleString() || '100,000'}</span>
          </div>
        )}
        {type === 'result' && (
          <div style={{ color: '#3fb950' }}>
            {data?.hasResult ? '✅ 有结果' : '待运行'}
          </div>
        )}
        {type === 'indicators' && (
          <div style={{ color: '#8b949e' }}>
            MA5/10/20, MACD, RSI, 布林带
          </div>
        )}
      </div>

      {/* 输入连接点 */}
      {def.inputs.map((port, i) => (
        <Handle
          key={`in-${port}`}
          type="target"
          position={Position.Left}
          id={port}
          style={{
            width: 10,
            height: 10,
            backgroundColor: '#2d3343',
            border: `2px solid ${def.color}`,
            top: 50 + i * 40,
          }}
          title={port}
        />
      ))}

      {/* 输出连接点 */}
      {def.outputs.map((port, i) => (
        <Handle
          key={`out-${port}`}
          type="source"
          position={Position.Right}
          id={port}
          style={{
            width: 10,
            height: 10,
            backgroundColor: '#2d3343',
            border: `2px solid ${def.color}`,
            top: 50 + i * 40,
          }}
          title={port}
        />
      ))}
    </div>
  )
}

export default memo(BaseNode)
