import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Phase 7 · 前端开发代理
// 前端统一请求 /api/*，Vite 转发到 FastAPI 后端（127.0.0.1:8000）并去掉 /api 前缀。
// 好处：浏览器端同源，无跨域问题；后端零改动。
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
