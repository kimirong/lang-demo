import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'

import App from './App.vue'
import './assets/style.css'

// 教学演示：Element Plus 全量引入，配置最简
const app = createApp(App)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
