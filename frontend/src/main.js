import { createApp } from 'vue'
import App from './App.vue'
import axios from 'axios'

// 创建 Vue 应用
const app = createApp(App)

// 配置 axios
app.config.globalProperties.$axios = axios

// 引入 ECharts 和 ECharts GL
import * as echarts from 'echarts';
import 'echarts-gl';

// 配置 echarts
app.config.globalProperties.$echarts = echarts

// 挂载应用
app.mount('#app')