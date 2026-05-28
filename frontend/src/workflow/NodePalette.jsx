import { nodeTypes, nodeCategories } from './nodes'

export default function NodePalette() {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  // 按分类分组
  const grouped = {}
  Object.entries(nodeTypes).forEach(([key, def]) => {
    const cat = def.category
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push({ key, ...def })
  })

  return (
    <div style={{
      width: 220,
      flexShrink: 0,
      borderRight: '1px solid #21262d',
      padding: 16,
      overflow: 'auto',
    }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, color: '#e6edf3', marginBottom: 16 }}>
        节点库
      </h3>

      {Object.entries(grouped).map(([cat, items]) => (
        <div key={cat} style={{ marginBottom: 16 }}>
          <div style={{
            fontSize: 11,
            fontWeight: 500,
            color: nodeCategories[cat]?.color || '#8b949e',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            marginBottom: 8,
          }}>
            {nodeCategories[cat]?.label || cat}
          </div>

          {items.map(item => (
            <div
              key={item.key}
              draggable
              onDragStart={(e) => onDragStart(e, item.key)}
              style={{
                padding: '10px 12px',
                borderRadius: 8,
                border: `1px solid #2d3343`,
                marginBottom: 6,
                cursor: 'grab',
                backgroundColor: '#1a1f2e',
                transition: 'all 0.15s',
                userSelect: 'none',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.borderColor = item.color
                e.currentTarget.style.backgroundColor = `${item.color}10`
              }}
              onMouseLeave={e => {
                e.currentTarget.style.borderColor = '#2d3343'
                e.currentTarget.style.backgroundColor = '#1a1f2e'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                <span>{item.icon}</span>
                <span style={{ fontSize: 13, fontWeight: 500, color: '#e6edf3' }}>{item.label}</span>
              </div>
              <div style={{ fontSize: 11, color: '#595e6b', marginLeft: 24 }}>
                {item.description}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
