// 画布策略的保存和加载

const STORAGE_KEY = 'aq_workflow_saved'

// 保存到 localStorage
export function saveToLocal(name, nodes, edges) {
  const saved = loadAll()
  saved[name] = {
    name,
    nodes,
    edges,
    savedAt: new Date().toISOString(),
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(saved))
  return true
}

// 从 localStorage 加载所有保存的策略
export function loadAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

// 加载指定策略
export function loadByName(name) {
  const all = loadAll()
  return all[name] || null
}

// 删除策略
export function deleteByName(name) {
  const all = loadAll()
  delete all[name]
  localStorage.setItem(STORAGE_KEY, JSON.stringify(all))
}

// 生成默认文件名
export function generateFileName() {
  const now = new Date()
  const date = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`
  const all = loadAll()
  const count = Object.keys(all).length + 1
  return `策略_${date}_#${count}`
}
