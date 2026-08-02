<script setup>
// Phase 7 · Markdown 渲染组件
// 用 markdown-it 把助理的回复渲染成富文本（加粗 / 列表 / 代码块等）。
// html:false → 原始 HTML 一律转义，防止提示词注入脚本。
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  html: false,   // 不渲染原始 HTML（防注入）
  linkify: true, // 自动把 URL 转成链接
  breaks: true,  // 单换行渲染成 <br>，符合聊天场景
})

const props = defineProps({
  content: { type: String, default: '' },
})

const rendered = computed(() => md.render(props.content))
</script>

<template>
  <div class="markdown-body" v-html="rendered" />
</template>

<style scoped>
/* 渲染后的富文本样式（作用于 markdown-it 产出的内部元素） */
.markdown-body {
  font-size: 14px;
  line-height: 1.7;
}

.markdown-body > :first-child {
  margin-top: 0;
}

.markdown-body > :last-child {
  margin-bottom: 0;
}

.markdown-body :deep(p) {
  margin: 0.5em 0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 0.7em 0 0.4em;
  font-size: 1.1em;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.4em 0;
  padding-left: 1.5em;
}

.markdown-body :deep(li) {
  margin: 0.2em 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

/* 行内代码 */
.markdown-body :deep(code) {
  background: #f0f2f5;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
}

/* 代码块 */
.markdown-body :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.6em 0;
}

.markdown-body :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}

.markdown-body :deep(blockquote) {
  margin: 0.5em 0;
  padding-left: 12px;
  border-left: 3px solid #409eff;
  color: #909399;
}

.markdown-body :deep(a) {
  color: #409eff;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 0.6em 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e4e7ed;
  padding: 6px 10px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f5f7fa;
}
</style>
