<script setup>
import { nextTick, ref, watch } from 'vue'
import ApprovalCard from './ApprovalCard.vue'

// 消息流：文本气泡（user / assistant）+ 审批卡片（approval）+ 思考中指示
const props = defineProps({
  messages: { type: Array, default: () => [] },
  thinking: { type: Boolean, default: false },
  busy: { type: Boolean, default: false }, // 审批请求进行中
})

const emit = defineEmits(['approve'])

const scroller = ref(null)

// 新消息 / 思考状态变化时自动滚到底部
watch(
  () => [props.messages.length, props.thinking, props.busy],
  async () => {
    await nextTick()
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
  },
  { flush: 'post' },
)

function fmtTime(ts) {
  const d = new Date(ts * 1000)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<template>
  <div ref="scroller" class="chat-messages">
    <template v-for="(m, i) in messages" :key="i">
      <!-- 文本气泡 -->
      <div v-if="m.kind === 'text'" class="msg-row" :class="m.role">
        <div class="msg-col">
          <div class="bubble">{{ m.content }}</div>
          <div class="meta">{{ fmtTime(m.ts) }}</div>
        </div>
      </div>

      <!-- 审批卡片 -->
      <div v-else-if="m.kind === 'approval'" class="msg-row">
        <ApprovalCard :payload="m.payload" :busy="busy" @approve="emit('approve', $event)" />
      </div>
    </template>

    <!-- 正在思考 -->
    <div v-if="thinking" class="msg-row assistant">
      <div class="bubble thinking-bubble">🤔 正在思考…</div>
    </div>
  </div>
</template>
