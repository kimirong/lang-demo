<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import SessionList from './components/SessionList.vue'
import MessageList from './components/MessageList.vue'
import * as api from './api.js'

// ---------- 会话列表（localStorage 记忆） ----------
const LS_KEY = 'lang-demo:sessions'
const sessions = ref([])

function loadSessions() {
  try {
    sessions.value = JSON.parse(localStorage.getItem(LS_KEY) || '[]')
  } catch {
    sessions.value = []
  }
}

function saveSessions() {
  localStorage.setItem(LS_KEY, JSON.stringify(sessions.value))
}

function registerSession(id, title) {
  if (!sessions.value.some((s) => s.id === id)) {
    sessions.value.unshift({
      id,
      title: title.slice(0, 20),
      ts: Math.floor(Date.now() / 1000),
    })
    saveSessions()
  }
}

// ---------- 当前会话状态 ----------
const currentId = ref(null) // null 表示"新建会话"草稿
const messages = ref([]) // { kind:'text'|'approval', role?, content?, payload?, ts }
const thinking = ref(false) // 后端生成中
const busy = ref(false) // 审批请求进行中
const backendUp = ref(null) // null 未知 / true / false

const pendingApproval = computed(() => messages.value.some((m) => m.kind === 'approval'))

// ---------- 动作 ----------
function newSession() {
  currentId.value = null
  messages.value = []
  thinking.value = false
}

async function selectSession(id) {
  currentId.value = id
  thinking.value = false
  messages.value = []
  try {
    const body = await api.history(id)
    messages.value = body.messages
      .filter((m) => ['human', 'ai'].includes(m.role))
      .map((m) => ({
        kind: 'text',
        role: m.role === 'human' ? 'user' : 'assistant',
        content: String(m.content),
        ts: Math.floor(Date.now() / 1000),
      }))
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function send() {
  const text = draft.value.trim()
  if (!text || thinking.value || pendingApproval.value) return

  draft.value = ''
  messages.value.push({ kind: 'text', role: 'user', content: text, ts: now() })
  thinking.value = true

  try {
    const res = await api.chat(currentId.value, text)
    currentId.value = res.session_id
    registerSession(res.session_id, text)

    if (res.status === 'pending_approval') {
      messages.value.push({ kind: 'approval', payload: res.interrupt, ts: now() })
    } else {
      messages.value.push({ kind: 'text', role: 'assistant', content: res.reply, ts: now() })
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    thinking.value = false
  }
}

async function handleApprove({ approved, note }) {
  if (!currentId.value || busy.value) return
  busy.value = true
  try {
    const res = await api.approve(currentId.value, approved, note)
    messages.value = messages.value.filter((m) => m.kind !== 'approval')
    messages.value.push({ kind: 'text', role: 'assistant', content: res.reply, ts: now() })
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    busy.value = false
  }
}

function now() {
  return Math.floor(Date.now() / 1000)
}

const draft = ref('')
const inputDisabled = computed(() => thinking.value || pendingApproval.value)

// ---------- 启动 ----------
onMounted(async () => {
  loadSessions()
  try {
    await api.health()
    backendUp.value = true
  } catch {
    backendUp.value = false
  }
})
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <span class="title">🛒 DeepSeek 智能客服助手</span>
      <span class="subtitle">LangChain + LangGraph + LangSmith · Phase 7 前端</span>
      <span
        class="status-dot"
        :class="backendUp === true ? 'online' : 'offline'"
        :title="backendUp === true ? '后端在线' : '后端未连接'"
      />
    </header>

    <div class="app-main">
      <SessionList
        :sessions="sessions"
        :current-id="currentId"
        @new-session="newSession"
        @select="selectSession"
      />

      <div class="chat-panel">
        <MessageList
          :messages="messages"
          :thinking="thinking"
          :busy="busy"
          @approve="handleApprove"
        />

        <!-- 审批挂起提示 -->
        <div v-if="pendingApproval" class="pending-hint">
          <el-alert type="warning" :closable="false" show-icon title="当前会话等待审批，请先处理上面的订单" />
        </div>

        <div class="chat-input">
          <el-input
            v-model="draft"
            type="textarea"
            :rows="1"
            resize="none"
            placeholder="输入消息，回车发送（Enter 发送 / Shift+Enter 换行）"
            :disabled="inputDisabled"
            @keydown.enter.exact.prevent="send"
          />
          <el-button
            type="primary"
            :loading="thinking"
            :disabled="inputDisabled || !draft.trim()"
            @click="send"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>
