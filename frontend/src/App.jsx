import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './AuthContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Backtest from './pages/Backtest'
import Results from './pages/Results'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import Marketplace from './pages/Marketplace'
import Workflow from './pages/Workflow'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="login" element={<Login />} />
            <Route path="backtest" element={<Backtest />} />
            <Route path="results" element={<Results />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="documents" element={<Documents />} />
            <Route path="marketplace" element={<Marketplace />} />
            <Route path="workflow" element={<Workflow />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
