import { useState } from 'react'

const docs = [
  {
    section: '快速开始',
    items: [
      { id: 'intro', title: '平台介绍' },
      { id: 'quickstart', title: '3分钟快速上手' },
    ],
  },
  {
    section: '回测指南',
    items: [
      { id: 'backtest-intro', title: '回测原理' },
      { id: 'backtest-strategies', title: '内置策略说明' },
      { id: 'backtest-params', title: '参数调优' },
    ],
  },
  {
    section: '数据源',
    items: [
      { id: 'data-eastmoney', title: '东方财富 A 股' },
      { id: 'data-indicators', title: '技术指标说明' },
    ],
  },
  {
    section: '策略案例',
    items: [
      { id: 'example-ma', title: '双均线策略' },
      { id: 'example-rsi', title: 'RSI 策略' },
      { id: 'example-macd', title: 'MACD 策略' },
      { id: 'example-bollinger', title: '布林带策略' },
    ],
  },
  {
    section: '部署与运维',
    items: [
      { id: 'deploy-server', title: '服务器部署' },
      { id: 'deploy-config', title: '配置文件说明' },
    ],
  },
]

const contents = {
  intro: {
    title: '平台介绍',
    body: `# A股量化回测平台

## 概述

专注 A 股市场的量化回测系统，支持多种内置策略、真实行情数据和可视化分析。

## 核心功能

- **回测引擎**：支持双均线、RSI、MACD、布林带四种内置策略
- **真实数据**：通过东方财富 API 获取 A 股实时行情
- **K 线分析**：内置 K 线图、均线系统、成交量分析
- **权益曲线**：回测结果可视化展示
- **历史记录**：回测结果云端存储，支持查看和对比

## 技术栈

- 后端：Python 3.x, FastAPI, SQLAlchemy, SQLite
- 前端：React 18, Vite, Tailwind CSS
- 图表：lightweight-charts`,
  },
  quickstart: {
    title: '3分钟快速上手',
    body: `# 3分钟快速上手

## 1. 登录系统

访问平台首页，点击右上角「登录」按钮。
默认管理员账号：root

## 2. 运行回测

1. 点击导航栏「回测」
2. 输入股票代码（如 600519 贵州茅台）
3. 选择策略类型和参数
4. 点击「运行回测」
5. 查看结果和交易记录

## 3. 查看历史

点击「回测结果」查看所有历史记录。`,
  },
  'backtest-intro': {
    title: '回测原理',
    body: `# 回测原理

## 什么是回测

回测（Backtesting）是用历史数据模拟策略在过去的表现，评估策略的有效性。

## 回测流程

1. **获取数据**：从东方财富 API 拉取指定股票的日 K 线数据
2. **计算指标**：自动计算 MA5/10/20/60、MACD、RSI、布林带等技术指标
3. **执行策略**：逐日扫描，根据策略规则生成买卖信号
4. **记录交易**：记录每笔交易的方向、价格、数量、收益
5. **计算绩效**：计算总收益率、年化收益、最大回撤、夏普比率、胜率

## 注意事项

- 回测结果不代表未来表现
- 未考虑滑点和交易成本
- A 股市场有涨跌停限制`,
  },
  'backtest-strategies': {
    title: '内置策略说明',
    body: `# 内置策略说明

## 双均线策略

短期均线上穿长期均线时买入（金叉），下穿时卖出（死叉）。

- **参数**：短期周期、长期周期
- **适合**：趋势行情
- **默认**：MA5 / MA20

## RSI 策略

RSI 低于超卖线时买入，高于超买线时卖出。

- **参数**：RSI 周期、超卖线、超买线
- **适合**：震荡行情
- **默认**：周期14, 超卖30, 超买70

## MACD 策略

MACD 金叉买入，死叉卖出。

- **无需参数**
- **特点**：跟随趋势，在强趋势行情中表现较好

## 布林带策略

价格触及下轨买入，触及上轨卖出。

- **无需参数**
- **特点**：均值回归思路，适合震荡行情`,
  },
  'backtest-params': {
    title: '参数调优',
    body: `# 参数调优

## 调整策略参数

不同的市场环境适合不同的参数设置。

### 双均线

- **短期**：5-10（灵敏）适合快速行情
- **长期**：20-60（稳健）适合慢速行情
- 差距越小，交易越频繁

### RSI

- **周期**：7-14（灵敏），21-28（稳健）
- **超卖线**：20-30（越低信号越少但准确率高）
- **超买线**：70-80（越高信号越少但准确率高）

## 调整回测周期

- 短期（30-90天）：适合测试近期表现
- 中期（180-365天）：适合评估策略稳定性
- 长期（730天）：适合完整牛熊周期测试`,
  },
  'data-eastmoney': {
    title: '东方财富 A 股数据源',
    body: `# 东方财富 A 股数据源

## 数据来源

平台使用东方财富 API 获取 A 股历史行情数据。

## 支持的股票代码

任意 A 股 6 位数字代码：

| 代码 | 名称 | 交易所 |
|------|------|--------|
| 600519 | 贵州茅台 | 上交所 |
| 000001 | 平安银行 | 深交所 |
| 300750 | 宁德时代 | 创业板 |
| 601318 | 中国平安 | 上交所 |
| 000858 | 五粮液 | 深交所 |

## 数据字段

- date（日期）、open（开盘）、high（最高）、low（最低）、close（收盘）
- volume（成交量）、amount（成交额）
- MA5/MA10/MA20/MA60（移动平均线）
- EMA12/EMA26、MACD、RSI(14)、布林带

## 数据频率

日 K 线，前复权。`,
  },
  'data-indicators': {
    title: '技术指标说明',
    body: `# 技术指标说明

## 移动平均线 (MA)

- **MA5**：5日均线，短期趋势
- **MA10**：10日均线，短期趋势
- **MA20**：20日均线，中期趋势
- **MA60**：60日均线，长期趋势

## MACD

由快线（EMA12）、慢线（EMA26）、柱状图组成。
- 快线上穿慢线 = 金叉（买入信号）
- 快线下穿慢线 = 死叉（卖出信号）

## RSI

相对强弱指标，衡量价格变动的速度和幅度。
- RSI > 70：超买，可能回调
- RSI < 30：超卖，可能反弹

## 布林带

由中轨（MA20）、上轨、下轨组成。
- 价格触及上轨：超买
- 价格触及下轨：超卖`,
  },
  'example-ma': {
    title: '双均线策略案例',
    body: `# 双均线策略案例

## 策略逻辑

当短期均线上穿长期均线时买入，下穿时卖出。

## 适用场景

- **上升趋势**：表现优异，能捕捉主升浪
- **震荡行情**：可能频繁假信号
- **下降趋势**：可以空仓避险

## 参数建议

| 周期 | 短期 | 长期 | 特点 |
|------|------|------|------|
| 短线 | 5 | 20 | 交易频繁 |
| 中线 | 10 | 30 | 平衡 |
| 长线 | 20 | 60 | 稳健 |`,
  },
  'example-rsi': {
    title: 'RSI 策略案例',
    body: `# RSI 策略案例

## 策略逻辑

当 RSI 低于超卖线时买入，高于超买线时卖出。

## 适用场景

- **震荡行情**：表现优异
- **单边趋势**：可能过早止盈/止损

## 参数建议

- RSI 周期：14（标准）
- 超卖线：30（激进可设25）
- 超买线：70（激进可设75）`,
  },
  'example-macd': {
    title: 'MACD 策略案例',
    body: `# MACD 策略案例

## 策略逻辑

MACD 金叉买入，死叉卖出。适合趋势行情。

## 优点

- 趋势跟随，在强趋势中表现好
- 无需额外参数

## 缺点

- 在震荡行情中表现一般
- 信号滞后`,
  },
  'example-bollinger': {
    title: '布林带策略案例',
    body: `# 布林带策略案例

## 策略逻辑

价格触及下轨买入，触及上轨卖出。

## 适用场景

- **震荡行情**：表现最好
- **单边突破**：可能反向交易导致亏损

## 建议

- 结合 RSI 一起使用效果更好
- 在大行情启动时慎用`,
  },
  'deploy-server': {
    title: '服务器部署',
    body: `# 服务器部署

## 启动服务

\`\`\`bash
cd /path/to/a-share-quant-backtest

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python database/models.py

# 启动
python -m uvicorn web.app:app --host 0.0.0.0 --port 8000
\`\`\`

## 前端构建

\`\`\`bash
cd frontend
npm install
npm run build
\`\`\`

构建后的文件在 frontend/dist/ 目录。

## 生产环境建议

- 使用 Nginx 反向代理
- 配置 HTTPS
- 修改 JWT SECRET_KEY`,
  },
  'deploy-config': {
    title: '配置文件说明',
    body: `# 配置文件说明

## config.yaml

\`\`\`yaml
server:
  host: "0.0.0.0"
  port: 8000
  url: "http://your-domain:8000"

admin:
  username: "root"
  password: "your-password"

database:
  path: "database/quant.db"
\`\`\`

## 安全建议

- 修改默认密码
- 生产环境使用环境变量而非配置文件存储密码
- 定期备份数据库`,
  },
}

export default function Documents() {
  const [activeDoc, setActiveDoc] = useState('intro')

  const doc = contents[activeDoc]

  return (
    <div style={{ display: 'flex', minHeight: 'calc(100vh - 56px)' }}>
      {/* 侧边栏 */}
      <div style={{
        width: 260,
        flexShrink: 0,
        borderRight: '1px solid #21262d',
        padding: '20px 0',
        overflow: 'auto',
      }}>
        <div style={{ padding: '0 20px', marginBottom: 16 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: '#e6edf3' }}>文档中心</h2>
        </div>
        {docs.map(section => (
          <div key={section.section} style={{ marginBottom: 12 }}>
            <div style={{
              padding: '6px 20px',
              fontSize: 12,
              fontWeight: 500,
              color: '#8b949e',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
            }}>
              {section.section}
            </div>
            {section.items.map(item => (
              <button
                key={item.id}
                onClick={() => setActiveDoc(item.id)}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 20px 8px 28px',
                  border: 'none',
                  background: 'none',
                  cursor: 'pointer',
                  fontSize: 14,
                  color: activeDoc === item.id ? '#e6edf3' : '#8b949e',
                  backgroundColor: activeDoc === item.id ? '#1c2333' : 'transparent',
                  borderRight: activeDoc === item.id ? '2px solid #58a6ff' : '2px solid transparent',
                  transition: 'all 0.15s',
                }}
              >
                {item.title}
              </button>
            ))}
          </div>
        ))}
      </div>

      {/* 内容区 */}
      <div style={{
        flex: 1,
        padding: '32px 48px',
        maxWidth: 800,
        overflow: 'auto',
      }}>
        {doc && (
          <div style={{
            color: '#e6edf3',
            fontSize: 15,
            lineHeight: 1.7,
          }}>
            {/* 渲染简单的 Markdown（标题/段落/列表/代码块） */}
            {doc.body.split('\n').map((line, i) => {
              // 标题
              if (line.startsWith('# ')) {
                return <h1 key={i} style={{ fontSize: 28, fontWeight: 700, margin: '0 0 16px 0', color: '#e6edf3' }}>{line.slice(2)}</h1>
              }
              if (line.startsWith('## ')) {
                return <h2 key={i} style={{ fontSize: 20, fontWeight: 600, margin: '24px 0 12px 0', color: '#e6edf3' }}>{line.slice(3)}</h2>
              }
              if (line.startsWith('### ')) {
                return <h3 key={i} style={{ fontSize: 16, fontWeight: 600, margin: '20px 0 8px 0', color: '#e6edf3' }}>{line.slice(4)}</h3>
              }
              // 代码块
              if (line.startsWith('```')) {
                return null
              }
              if (line.startsWith('```yaml') || line.startsWith('```bash')) {
                return null
              }
              // 表格
              if (line.startsWith('|') && line.includes('---')) {
                return null
              }
              if (line.startsWith('|')) {
                const cells = line.split('|').filter(Boolean).map(c => c.trim())
                if (cells.length >= 2) {
                  // 简单渲染为列表项
                  return (
                    <div key={i} style={{ display: 'flex', gap: 16, padding: '4px 0', fontSize: 14, color: '#8b949e' }}>
                      {cells.map((c, j) => <span key={j} style={{ flex: 1 }}>{c}</span>)}
                    </div>
                  )
                }
              }
              // 列表项
              if (line.startsWith('- ')) {
                return <li key={i} style={{ color: '#8b949e', margin: '2px 0' }}>{line.slice(2)}</li>
              }
              // 空行
              if (!line.trim()) {
                return <div key={i} style={{ height: 8 }} />
              }
              // 段落
              return <p key={i} style={{ margin: '0 0 8px 0', color: '#8b949e' }}>{line}</p>
            })}
          </div>
        )}
      </div>
    </div>
  )
}
