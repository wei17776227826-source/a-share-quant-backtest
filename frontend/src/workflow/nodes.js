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
