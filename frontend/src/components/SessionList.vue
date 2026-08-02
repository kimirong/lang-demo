<script setup>
// 左侧会话列表：新建会话 + 历史会话（来自 localStorage，点击切换）

defineProps({
  sessions: { type: Array, default: () => [] },
  currentId: { type: String, default: null },
})

const emit = defineEmits(['new-session', 'select'])

// 把秒级时间戳格式化为 MM-DD HH:mm
function fmtTime(ts) {
  const d = new Date(ts * 1000)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<template>
  <aside class="sidebar">
    <el-button class="new-session" type="primary" @click="emit('new-session')">
      ＋ 新建会话
    </el-button>

    <div class="session-list">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="session-item"
        :class="{ active: s.id === currentId }"
        @click="emit('select', s.id)"
      >
        <span class="session-title">{{ s.title }}</span>
        <span class="session-time">{{ fmtTime(s.ts) }}</span>
      </div>

      <div v-if="!sessions.length" class="empty">暂无会话，点击上方新建</div>
    </div>
  </aside>
</template>
