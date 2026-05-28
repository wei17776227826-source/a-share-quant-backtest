function App() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#0d1117]">
      <div className="card p-8 text-center">
        <h1 className="text-2xl font-bold mb-2" style={{ color: '#e6edf3' }}>A股量化回测平台</h1>
        <p className="mb-4" style={{ color: '#8b949e' }}>BeeQuant 风格前端重构中</p>
        <div className="flex gap-3 justify-center">
          <span className="badge badge-blue">Phase 1.2</span>
          <span className="badge badge-green">Tailwind OK</span>
        </div>
      </div>
    </div>
  )
}

export default App
