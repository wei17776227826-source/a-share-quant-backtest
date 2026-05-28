import { useState, useCallback, useRef } from 'react'
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
import { nodeTypes as nodeDefs, nodeDimensions, generateBacktestRequest } from '../workflow/nodes'
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
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
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
            style={{ fontSize: 13, color: '#f85149', borderColor: 'rgba(248,81,73,0.3)' }}
            onClick={handleClear}
          >
            清空画布
          </button>
        </div>

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
