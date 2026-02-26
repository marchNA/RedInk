import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import OutlineView from '../views/OutlineView.vue'
import GenerateView from '../views/GenerateView.vue'
import ResultView from '../views/ResultView.vue'
import HistoryView from '../views/HistoryView.vue'
import SettingsView from '../views/SettingsView.vue'
import XhsSettingsView from '../views/XhsSettingsView.vue'
import DebugImageView from '../views/DebugImageView.vue'
import PoemCoverView from '../views/PoemCoverView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/outline',
      name: 'outline',
      component: OutlineView
    },
    {
      path: '/generate',
      name: 'generate',
      component: GenerateView
    },
    {
      path: '/result',
      name: 'result',
      component: ResultView
    },
    {
      path: '/history',
      name: 'history',
      component: HistoryView
    },
    {
      path: '/brainstorm',
      name: 'brainstorm',
      redirect: '/'
    },
    {
      path: '/history/:id',
      name: 'history-detail',
      component: HistoryView
    },
    {
      path: '/debug-image',
      name: 'debug-image',
      component: DebugImageView
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView
    },
    {
      path: '/settings/xhs',
      name: 'xhs-settings',
      component: XhsSettingsView
    },
    {
      path: '/poem-cover',
      name: 'poem-cover',
      component: PoemCoverView
    }
  ]
})

export default router
