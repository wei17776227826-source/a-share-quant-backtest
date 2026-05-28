import { useState, useCallback, useRef, useEffect } from 'react'
import {
  ReactFlow,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  ReactFlowProvider,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import NodePalette from '../workflow/NodePalette'
import ConfigPanel from '../workflow/ConfigPanel'
import BaseNode from '../workflow/NodeComponent'
import { nodeTypes as nodeDefs, nodeDimensions, generateBacktestRequest, isValidConnection, validateFlow } from '../workflow/nodes'
import { saveToLocal, loadAll, loadByName, deleteByName, generateFileName } from '../workflow/storage'
import { backtest } from '../api'
import { useAuth } from '../AuthContext'

// 注册自定义节点类型
const customNodeTypes = {}
Object.keys(nodeDefs).forEach(key => {
  customNodeTypes[key] = BaseNode
})

let nodeId = 0
const getId = () => `node_${++nodeId}`

const defaultEdgeOptions = {
  animated: true,
  style: { stroke: '#2d3343', strokeWidth: 2 },
  activeStyle: { stroke: '#58a6ff' },
}

export default function Workflow() {
  return (
    <ReactFlowProvider>
      <WorkflowInner />
    </ReactFlowProvider>
  )
}

function WorkflowInner() {
  const { user } = useAuth()
  const reactFlowWrapper = useRef(null)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const onConnect = useCallback(
    (params) => {
      // 验证连接是否合法
      const sourceEdge = edges.find(e => e.source === params.source && e.sourceHandle === params.sourceHandle)
      if (sourceEdge) {
        // 同一个输出端口不能有多个连接
        return
      }
      setEdges((eds) => addEdge({ ...params, animated: true }, eds))
    },
    [setEdges, edges]
  )

  const onConnectValidation = useCallback(
    (connection) => {
      // 连线校验
      const sourceNode = nodes.find(n => n.id === connection.source)
      const targetNode = nodes.find(n => n.id === connection.target)
      if (!sourceNode || !targetNode) return false
      return isValidConnection(
        sourceNode.type,
        connection.sourceHandle,
        targetNode.type,
        connection.targetHandle
      )
    },
    [nodes]
  )

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event) => {
      event.preventDefault()
      const type = event.dataTransfer.getData('application/reactflow')
      if (!type || !nodeDefs[type]) return

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      const dims = nodeDimensions[type] || { width: 220, height: 120 }
      const def = nodeDefs[type]

      const newNode = {
        id: getId(),
        type,
        position,
        data: { ...def.defaults, label: def.label },
        ...dims,
      }

      setNodes((nds) => nds.concat(newNode))
    },
    [reactFlowInstance, setNodes]
  )

  const onNodeClick = useCallback((_, node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const handleNodeUpdate = useCallback(
    (nodeId, newData) => {
      setNodes((nds) =>
        nds.map((n) => (n.id === nodeId ? { ...n, data: newData } : n))
      )
      // 同步更新选中节点
      setSelectedNode((prev) =>
        prev?.id === nodeId ? { ...prev, data: newData } : prev
      )
    },
    [setNodes]
  )

  const handleRun = async () => {
    if (!user) return

    // 先做数据流完整性校验
    const issues = validateFlow(nodes, edges)
    if (issues.length > 0) {
      setError('数据流不完整：\n' + issues.join('\n'))
      return
    }

    setRunning(true)
    setError('')
    setResult(null)

    const request = generateBacktestRequest(
      Object.fromEntries(nodes.map(n => [n.id, n])),
      edges
    )

    if (!request) {
      setError('请确保至少包含数据源和策略节点')
      setRunning(false)
      return
    }

    try {
      const data = await backtest.run(request)
      setResult(data)
      // 更新结果节点状态
      setNodes((nds) =>
        nds.map((n) =>
          n.type === 'result' ? { ...n, data: { ...n.data, hasResult: true } } : n
        )
      )
    } catch (err) {
      setError(err.response?.data?.detail || '回测执行失败')
    } finally {
      setRunning(false)
    }
  }

  const handleClear = () => {
    setNodes([])
    setEdges([])
    setSelectedNode(null)
    setResult(null)
    setError('')
  }

  // 保存/加载状态
  const [savedList, setSavedList] = useState([])
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [showLoadModal, setShowLoadModal] = useState(false)

  useEffect(() => {
    setSavedList(Object.values(loadAll()))
  }, [showLoadModal, showSaveModal])

  const handleSave = () => {
    const name = saveName || generateFileName()
    saveToLocal(name, nodes, edges)
    setShowSaveModal(false)
    setSaveName('')
  }

  const handleLoad = (name) => {
    const data = loadByName(name)
    if (data) {
      setNodes(data.nodes)
      setEdges(data.edges)
      setResult(null)
      setError('')
      setShowLoadModal(false)
    }
  }

  const handleDelete = (name) => {
    deleteByName(name)
    setSavedList(Object.values(loadAll()))
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 56px)' }}>
      {/* 左侧节点库 */}
      <NodePalette />

      {/* 画布 */}
      <div style={{ flex: 1, position: 'relative' }} ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          isValidConnection={onConnectValidation}
          nodeTypes={customNodeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          fitView
          style={{ backgroundColor: '#0d1117' }}
          colorMode="dark"
        >
          <Controls style={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3343', borderRadius: 8, color: '#8b949e' }} />
          <Background color="#1c2333" gap={20} />
          <MiniMap
            style={{ backgroundColor: '#1a1f2e', border: '1px solid #2d3343', borderRadius: 8 }}
            nodeColor={() => '#58a6ff'}
            maskColor="rgba(13,17,23,0.7)"
          />
        </ReactFlow>

        {/* 工具栏 */}
        <div style={{
          position: 'absolute',
          top: 12,
          right: 12,
          display: 'flex',
          gap: 8,
          zIndex: 10,
        }}>
          <button
            className="btn btn-primary"
            style={{ fontSize: 13 }}
            onClick={handleRun}
            disabled={running || nodes.length === 0}
          >
            {running ? '运行中...' : '▶ 运行回测'}
          </button>
          <button
            className="btn btn-ghost"
            style={{ fontSize: 13 }}
            onClick={() => { setSaveName(''); setShowSaveModal(true) }}
            disabled={nodes.length === 0}
          >
            💾 保存
          </button>
          <button
            className="btn btn-ghost"
            style={{ fontSize: 13 }}
            onClick={() => setShowLoadModal(true)}
          >
            📂 加载
          </button>
          <button
            className="btn btn-ghost"
            style={{ fontSize: 13, color: '#f85149', borderColor: 'rgba(248,81,73,0.3)' }}
            onClick={handleClear}
          >
            清空画布
          </button>
        </div>

        {/* 保存模态框 */}
        {showSaveModal && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 100,
          }}>
            <div className="card" style={{ width: 360, padding: 24 }}>
              <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 16 }}>保存策略</h3>
              <input
                className="input"
                value={saveName}
                onChange={e => setSaveName(e.target.value)}
                placeholder={generateFileName()}
                autoFocus
              />
              <div style={{ fontSize: 11, color: '#595e6b', marginTop: 4 }}>留空使用自动生成名称</div>
              <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleSave}>保存</button>
                <button className="btn btn-ghost" style={{ flex: 1 }} onClick={() => setShowSaveModal(false)}>取消</button>
              </div>
            </div>
          </div>
        )}

        {/* 加载模态框 */}
        {showLoadModal && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            zIndex: 100,
          }}>
            <div className="card" style={{ width: 400, padding: 24, maxHeight: 400, overflow: 'auto' }}>
              <h3 style={{ fontSize: 16, color: '#e6edf3', marginBottom: 16 }}>加载策略</h3>
              {savedList.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#595e6b', padding: 20 }}>
                  暂无已保存的策略
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {savedList.map(s => (
                    <div key={s.name} style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '10px 14px',
                      borderRadius: 8,
                      border: '1px solid #2d3343',
                    }}>
                      <div>
                        <div style={{ fontSize: 14, color: '#e6edf3' }}>{s.name}</div>
                        <div style={{ fontSize: 11, color: '#595e6b' }}>
                          {new Date(s.savedAt).toLocaleString('zh-CN')} · {s.nodes?.length || 0} 个节点
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button className="btn btn-primary" style={{ padding: '4px 12px', fontSize: 12 }} onClick={() => handleLoad(s.name)}>
                          加载
                        </button>
                        <button className="btn btn-ghost" style={{ padding: '4px 12px', fontSize: 12, color: '#f85149' }} onClick={() => handleDelete(s.name)}>
                          删除
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <button className="btn btn-ghost" style={{ width: '100%', marginTop: 12 }} onClick={() => setShowLoadModal(false)}>
                关闭
              </button>
            </div>
          </div>
        )}

        {/* 错误提示 */}
        {error && (
          <div style={{
            position: 'absolute',
            bottom: 12,
            left: '50%',
            transform: 'translateX(-50%)',
            padding: '8px 20px',
            borderRadius: 8,
            backgroundColor: 'rgba(248,81,73,0.9)',
            color: '#fff',
            fontSize: 13,
            zIndex: 10,
          }}>
            {error}
          </div>
        )}

        {/* 空画布提示 */}
        {nodes.length === 0 && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            color: '#595e6b',
            pointerEvents: 'none',
          }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>🔧</div>
            <div style={{ fontSize: 16, color: '#8b949e', marginBottom: 8 }}>从左侧拖拽节点到画布</div>
            <div style={{ fontSize: 13 }}>数据源 → 技术指标 → 策略 → 回测引擎 → 结果展示</div>
          </div>
        )}
      </div>

      {/* 右侧配置面板 */}
      <ConfigPanel node={selectedNode} onUpdate={handleNodeUpdate} />
    </div>
  )
}
