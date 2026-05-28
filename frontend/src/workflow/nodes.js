/**
 * 节点类型定义 - 画布工作流引擎
 */

// 节点分类和颜色
export const nodeCategories = {
  dataSource: { label: '数据源', color: '#3fb950' },
  processing: { label: '数据处理', color: '#58a6ff' },
  strategy: { label: '策略', color: '#d29922' },
  output: { label: '输出', color: '#f0883e' },
}

// 可用的节点类型
export const nodeTypes = {
  // 数据源节点
  dataSource: {
    category: 'dataSource',
    label: '数据源',
    icon: '📡',
    description: 'A 股行情数据',
    color: nodeCategories.dataSource.color,
    defaults: {
      symbol: '600519',
      days: 365,
    },
    inputs: [],
    outputs: ['ohlcv'],
  },

  // 技术指标节点
  indicators: {
    category: 'processing',
    label: '技术指标',
    icon: '📐',
    description: 'MA, MACD, RSI, 布林带',
    color: nodeCategories.processing.color,
    defaults: {},
    inputs: ['ohlcv'],
    outputs: ['features'],
  },

  // 策略节点
  strategy: {
    category: 'strategy',
    label: '交易策略',
    icon: '🎯',
    description: '策略逻辑',
    color: nodeCategories.strategy.color,
    defaults: {
      type: 'dual_ma',
      params: {},
    },
    inputs: ['features'],
    outputs: ['signals'],
  },

  // 回测节点
  backtest: {
    category: 'processing',
    label: '回测引擎',
    icon: '⚙️',
    description: '运行回测',
    color: nodeCategories.processing.color,
    defaults: {
      capital: 100000,
    },
    inputs: ['signals', 'ohlcv'],
    outputs: ['result'],
  },

  // 结果展示节点
  result: {
    category: 'output',
    label: '结果展示',
    icon: '📊',
    description: '查看回测结果',
    color: nodeCategories.output.color,
    defaults: {},
    inputs: ['result'],
    outputs: [],
  },
}

// 节点初始尺寸
export const nodeDimensions = {
  dataSource: { width: 220, height: 120 },
  indicators: { width: 220, height: 100 },
  strategy: { width: 220, height: 140 },
  backtest: { width: 220, height: 120 },
  result: { width: 220, height: 100 },
}

// 连线验证 - 判断两个节点能否连接
// 规则：source 的输出类型必须匹配 target 的输入类型
const compatiblePorts = {
  ohlcv: ['ohlcv'],      // ohlcv 只能连 ohlcv
  features: ['features'], // features 只能连 features
  signals: ['signals'],   // signals 只能连 signals
  result: ['result'],     // result 只能连 result
}

export function isValidConnection(sourceType, sourcePort, targetType, targetPort) {
  const sourceDef = nodeTypes[sourceType]
  const targetDef = nodeTypes[targetType]
  if (!sourceDef || !targetDef) return false

  // 检查输出端口是否存在
  if (!sourceDef.outputs.includes(sourcePort)) return false
  // 检查输入端口是否存在
  if (!targetDef.inputs.includes(targetPort)) return false

  // 检查端口兼容性
  const compatible = compatiblePorts[sourcePort]
  if (!compatible || !compatible.includes(targetPort)) return false

  return true
}

// 检查画布上的数据流是否完整（从数据源到结果节点的完整链路）
export function validateFlow(nodes, edges) {
  const issues = []

  // 1. 检查是否有必需节点
  const hasSource = nodes.some(n => n.type === 'dataSource')
  const hasStrategy = nodes.some(n => n.type === 'strategy')
  const hasBacktest = nodes.some(n => n.type === 'backtest')

  if (nodes.length > 0 && !hasSource) issues.push('缺少数据源节点')
  if (nodes.length > 0 && !hasStrategy) issues.push('缺少策略节点')
  if (nodes.length > 0 && !hasBacktest) issues.push('缺少回测引擎节点')

  // 2. 检查是否有孤立节点（没有连线的节点）
  if (nodes.length > 1) {
    const connectedNodeIds = new Set()
    edges.forEach(e => {
      connectedNodeIds.add(e.source)
      connectedNodeIds.add(e.target)
    })
    nodes.forEach(n => {
      if (!connectedNodeIds.has(n.id) && n.type !== 'dataSource') {
        issues.push(`"${nodeTypes[n.type]?.label}" 节点未连接`)
      }
    })
  }

  return issues
}

// 从画布配置生成回测 API 请求参数
export function generateBacktestRequest(nodes, edges) {
  // 找数据源节点
  const dataSourceNode = Object.values(nodes).find(n => n.type === 'dataSource')
  // 找策略节点
  const strategyNode = Object.values(nodes).find(n => n.type === 'strategy')

  if (!dataSourceNode || !strategyNode) return null

  return {
    strategy_type: strategyNode.data?.params?.type || 'dual_ma',
    symbol: dataSourceNode.data?.symbol || '600519',
    days: dataSourceNode.data?.days || 365,
    initial_capital: 100000,
    data_source: 'real',
    parameters: strategyNode.data?.params?.params || {},
  }
}
