import { createRouter, createWebHistory } from 'vue-router'

// 引入你的组件
// 注意：确保你的 Gallery.vue 文件确实在 src/views/ 下
import Home from '../views/Home.vue'
import Chat from '@/views/Chat.vue'
import MusicAnalysis from '@/views/MusicAnalysis.vue'
import Map from '@/views/Map.vue'
import Finger from '@/views/Finger.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/chat2',
    name: 'MusicAnalysis',
    component: MusicAnalysis,
  },
  {
    path: '/environmentPanel',
    name: 'Map',
    component: Map,
  },
  {
    path: '/finger',
    name: 'Finger',
    component: Finger
  }

]

const router = createRouter({
  // 使用 createWebHistory 模式 (URL里不带 # 号，看起来像普通网站)
  history: createWebHistory(),
  routes
})

export default router