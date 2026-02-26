<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title">小红书设置</h1>
      <p class="page-subtitle">管理账号登录和发布设置</p>
    </div>

    <div class="card">
      <div class="section-header">
        <div>
          <h2 class="section-title">账号管理</h2>
          <p class="section-desc">扫码登录后，可直接发布笔记到小红书</p>
        </div>
      </div>

      <!-- 登录状态 -->
      <div class="auth-status">
        <div v-if="loading" class="loading-container">
          <div class="spinner"></div>
          <p>检查登录状态...</p>
        </div>

        <div v-else class="status-content">
          <!-- 未登录 -->
          <div v-if="!authStatus.logged_in" class="not-logged-in">
            <div class="status-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="1.5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </div>
            <p class="status-text">未登录小红书账号</p>
            <button 
              class="btn btn-primary" 
              @click="startLogin"
              :disabled="loggingIn"
            >
              {{ loggingIn ? '启动中...' : '扫码登录' }}
            </button>
            <p v-if="loginMessage" class="login-message">{{ loginMessage }}</p>
          </div>

          <!-- 已登录 -->
          <div v-else class="logged-in">
            <div class="user-info">
              <div class="avatar">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </div>
              <div class="user-detail">
                <p class="user-name">{{ authStatus.user_info?.name || '小红书用户' }}</p>
                <p class="login-time">已登录</p>
              </div>
            </div>
            <button class="btn btn-outline" @click="handleLogout">
              退出登录
            </button>
          </div>
        </div>
      </div>

      <!-- 登录流程说明 -->
      <div class="help-section" v-if="!authStatus.logged_in">
        <h3>登录说明</h3>
        <ol>
          <li>点击「扫码登录」按钮，将弹出浏览器窗口</li>
          <li>使用小红书 App 扫描二维码完成登录</li>
          <li>登录成功后，浏览器会自动关闭</li>
          <li>登录状态会被保存，下次无需重复登录</li>
        </ol>
      </div>
    </div>

    <!-- 发布设置 -->
    <div class="card" v-if="authStatus.logged_in">
      <div class="section-header">
        <div>
          <h2 class="section-title">发布设置</h2>
          <p class="section-desc">配置发布时的默认选项</p>
        </div>
      </div>

      <div class="settings-form">
        <div class="form-group">
          <label class="form-label">默认标签</label>
          <input 
            type="text" 
            class="form-input" 
            v-model="defaultTags" 
            placeholder="用逗号分隔，如：护肤，教程"
          />
          <p class="form-hint">发布时会自动添加这些标签</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { 
  getXhsAuthStatus, 
  startXhsLogin, 
  checkXhsLogin, 
  completeXhsLogin, 
  logoutXhs 
} from '../api'
import type { AuthStatus } from '../api'

const loading = ref(true)
const authStatus = ref<AuthStatus>({
  logged_in: false,
  user_info: null,
  last_check: null
})

const loggingIn = ref(false)
const loginMessage = ref('')
const pollingInterval = ref<number | null>(null)
const completingLogin = ref(false)

const defaultTags = ref('')

onMounted(async () => {
  await checkAuthStatus()
  loading.value = false
})

async function checkAuthStatus() {
  try {
    authStatus.value = await getXhsAuthStatus()
  } catch (error) {
    console.error('检查登录状态失败:', error)
  }
}

async function startLogin() {
  loggingIn.value = true
  loginMessage.value = ''

  try {
    const result = await startXhsLogin()
    
    if (result.success) {
      loginMessage.value = result.message
      // 开始轮询检查登录状态
      startPolling()
    } else {
      loginMessage.value = result.message || '启动登录失败'
    }
  } catch (error: any) {
    loginMessage.value = error.message || '启动登录失败'
  } finally {
    loggingIn.value = false
  }
}

function startPolling() {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }

  pollingInterval.value = window.setInterval(async () => {
    if (completingLogin.value) return

    try {
      const result = await checkXhsLogin()
      
      if (result.logged_in) {
        // 先停止轮询，避免并发触发 complete
        stopPolling()
        completingLogin.value = true
        try {
          await completeXhsLogin(10)
        } finally {
          completingLogin.value = false
        }
        await checkAuthStatus()
        loginMessage.value = authStatus.value.logged_in ? '' : '登录状态确认失败，请重试'
      }
    } catch (error) {
      console.error('检查登录状态失败:', error)
    }
  }, 2000)
}

function stopPolling() {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

async function handleLogout() {
  try {
    stopPolling()
    completingLogin.value = false
    loginMessage.value = ''
    await logoutXhs()
    await checkAuthStatus()
  } catch (error) {
    console.error('退出登录失败:', error)
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 4px 0;
}

.section-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: #ff2442;
  color: #fff;
}

.btn-primary:hover {
  background: #e6203b;
}

.btn-primary:disabled {
  background: #ff99a8;
  cursor: not-allowed;
}

.btn-outline {
  background: #fff;
  color: #666;
  border: 1px solid #ddd;
}

.btn-outline:hover {
  background: #f5f5f5;
}

.btn-small {
  padding: 6px 12px;
  font-size: 13px;
}

.auth-status {
  padding: 20px 0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #666;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f0f0f0;
  border-top-color: #ff2442;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.not-logged-in {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.status-icon {
  width: 80px;
  height: 80px;
  background: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-text {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.login-message {
  font-size: 14px;
  color: #ff6b6b;
  margin: 0;
}

.logged-in {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f9f9f9;
  border-radius: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 56px;
  height: 56px;
  background: #ff2442;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.login-time {
  font-size: 13px;
  color: #4caf50;
  margin: 0;
}

.help-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #eee;
}

.help-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.help-section ol {
  margin: 0;
  padding-left: 20px;
  color: #666;
  font-size: 14px;
  line-height: 1.8;
}

.settings-form {
  padding: 16px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #ff2442;
}

.form-hint {
  font-size: 13px;
  color: #999;
  margin: 6px 0 0 0;
}
</style>
