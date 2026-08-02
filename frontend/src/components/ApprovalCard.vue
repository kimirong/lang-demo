<script setup>
import { ref } from 'vue'

// 下单人工审批卡片：展示订单详情，批准 / 拒绝由人工决定
const props = defineProps({
  payload: { type: Object, required: true }, // { action, product, price, address, question }
  busy: { type: Boolean, default: false },
})

const emit = defineEmits(['approve'])

const note = ref('') // 批准时填收货地址，拒绝时填原因

function doApprove(approved) {
  emit('approve', { approved, note: note.value.trim() })
}
</script>

<template>
  <el-card class="approval-card" shadow="never">
    <template #header>
      <div class="approval-header">
        <el-tag type="warning" size="small">待人工审批</el-tag>
        <span class="approval-question">{{ payload.question || '是否批准这笔下单？' }}</span>
      </div>
    </template>

    <el-descriptions :column="1" border size="small">
      <el-descriptions-item label="商品">
        {{ payload.product }}
      </el-descriptions-item>
      <el-descriptions-item label="价格">
        ¥{{ payload.price }}
      </el-descriptions-item>
      <el-descriptions-item label="收货地址">
        {{ payload.address }}
      </el-descriptions-item>
    </el-descriptions>

    <el-input
      v-model="note"
      class="approval-note"
      :placeholder="'可选：' + (payload.address ? '修改收货地址' : '填写收货地址')"
      :disabled="busy"
    />

    <div class="approval-actions">
      <el-button type="primary" :loading="busy" @click="doApprove(true)">✅ 批准下单</el-button>
      <el-button type="danger" plain :loading="busy" @click="doApprove(false)">
        🚫 拒绝下单
      </el-button>
    </div>
  </el-card>
</template>

<style scoped>
.approval-card {
  max-width: 480px;
  border: 1px solid #e6a23c;
}

.approval-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.approval-question {
  font-size: 13px;
  color: #606266;
}

.approval-note {
  margin-top: 12px;
}

.approval-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}
</style>
