// Phase 7 · 后端 API 封装
// 前端统一请求 /api/*，由 Vite 代理转发到 FastAPI（127.0.0.1:8000）。

async function request(url, options = {}) {
  let res
  try {
    res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch {
    throw new Error('无法连接后端，请确认 uvicorn app:app --port 8000 已启动')
  }
  const body = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(body.detail || `请求失败（${res.status}）`)
  }
  return body
}

/** 后端存活检查 */
export function health() {
  return request('/api/health')
}

/** 发消息。可能返回 pending_approval（下单审批） */
export function chat(sessionId, message) {
  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, message }),
  })
}

/** 审批下单。approved=true 时 note 作收货地址，否则作拒绝原因 */
export function approve(sessionId, approved, note = '') {
  return request('/api/approve', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, approved, note }),
  })
}

/** 拉取某会话的完整历史 */
export function history(sessionId) {
  return request(`/api/history/${sessionId}`)
}
