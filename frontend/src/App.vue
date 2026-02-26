<template>
  <div id="app" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- 侧边栏 Sidebar -->
    <aside class="layout-sidebar">
      <button
        class="sidebar-toggle-btn"
        :title="sidebarCollapsed ? '展开侧边栏' : '隐藏侧边栏'"
        @click="toggleSidebar"
      >
        {{ sidebarCollapsed ? '>' : '<' }}
      </button>

      <div class="logo-area">
        <img :src="sidebarCollapsed ? '/logo.png' : '/logo-banner.png'" alt="红墨 - 灵感一触即发" class="logo-icon" />
      </div>
      
      <nav class="nav-menu">
        <RouterLink to="/" class="nav-item" active-class="active" title="创作中心" data-tip="主题输入并生成大纲">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
          <span class="nav-label">创作中心</span>
        </RouterLink>
        <RouterLink to="/history" class="nav-item" active-class="active" title="历史记录" data-tip="查看与继续历史任务">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          <span class="nav-label">历史记录</span>
        </RouterLink>
        <RouterLink to="/debug-image" class="nav-item" active-class="active" title="调试生图" data-tip="测试 system/user 生图">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
          <span class="nav-label">调试生图</span>
        </RouterLink>
        <RouterLink to="/settings" class="nav-item" active-class="active" title="系统设置" data-tip="配置文本与图片供应商">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M12 1v6m0 6v6m-6-6h6m6 0h-6"></path><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
          <span class="nav-label">系统设置</span>
        </RouterLink>
        <RouterLink to="/settings/xhs" class="nav-item" active-class="active" title="小红书" data-tip="登录与发布配置">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
          <span class="nav-label">小红书</span>
        </RouterLink>
        <RouterLink to="/poem-cover" class="nav-item" active-class="active" title="三行诗封面" data-tip="左配置右预览">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
          <span class="nav-label">三行诗封面</span>
        </RouterLink>
      </nav>
      
    </aside>

    <!-- 主内容区 -->
    <main class="layout-main">
      <RouterView v-slot="{ Component, route }">
        <component :is="Component" />

        <!-- 全局页脚版权信息（首页除外） -->
        <footer v-if="route.path !== '/'" class="global-footer">
          <div class="footer-content">
            <div class="footer-tip">
              配置不成功？访问 <a href="https://redink.top" target="_blank" rel="noopener noreferrer">redink.top</a> 官方站点即刻体验
            </div>
            <div class="footer-text">
              © 2025 <a href="https://github.com/HisMax/RedInk" target="_blank" rel="noopener noreferrer">RedInk</a> by 默子 (Histone)
            </div>
            <div class="footer-license">
              Licensed under <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="noopener noreferrer">CC BY-NC-SA 4.0</a>
            </div>
          </div>
        </footer>
      </RouterView>
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
import { onMounted, ref, watch } from 'vue'
import { setupAutoSave } from './stores/generator'

const SIDEBAR_STATE_KEY = 'redink.sidebar.collapsed'
const sidebarCollapsed = ref(false)

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 启用自动保存到 localStorage
onMounted(() => {
  setupAutoSave()
  sidebarCollapsed.value = localStorage.getItem(SIDEBAR_STATE_KEY) === '1'
})

watch(sidebarCollapsed, (val) => {
  localStorage.setItem(SIDEBAR_STATE_KEY, val ? '1' : '0')
})
</script>

<style scoped>
.sidebar-toggle-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 28px;
  height: 28px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: #fff;
  color: var(--text-sub);
  font-weight: 700;
  cursor: pointer;
  line-height: 1;
}

.sidebar-toggle-btn:hover {
  color: var(--primary);
}

.layout-sidebar {
  overflow-y: auto;
}

#app.sidebar-collapsed .layout-sidebar {
  width: 86px;
  padding: 32px 12px;
}

#app.sidebar-collapsed .layout-main {
  margin-left: 86px;
}

#app.sidebar-collapsed .logo-area {
  margin-bottom: 36px;
}

#app.sidebar-collapsed .logo-icon {
  max-width: 42px;
  margin: 0 auto;
}

#app.sidebar-collapsed .nav-item {
  position: relative;
  justify-content: center;
  padding: 14px 10px;
}

#app.sidebar-collapsed .nav-item:hover::after {
  content: attr(data-tip);
  position: absolute;
  left: calc(100% + 10px);
  top: 50%;
  transform: translateY(-50%);
  background: #1f2937;
  color: #fff;
  font-size: 12px;
  line-height: 1.4;
  padding: 6px 10px;
  border-radius: 6px;
  white-space: nowrap;
  z-index: 300;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

#app.sidebar-collapsed .nav-label {
  display: none;
}
</style>
