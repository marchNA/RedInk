<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content">
        <div class="modal-header">
          <h2>发布到小红书</h2>
          <button class="close-btn" @click="handleClose">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <!-- 登录状态 -->
          <div v-if="!isLoggedIn" class="login-prompt">
            <div class="icon-area">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ff2442" stroke-width="1.5">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                <polyline points="22,6 12,13 2,6"></polyline>
              </svg>
            </div>
            <p>请先在设置中登录小红书账号</p>
            <button class="btn btn-outline" @click="goToSettings">
              去设置
            </button>
          </div>

          <!-- 发布表单 -->
          <div v-else class="publish-form">
            <!-- 选择封面 -->
            <div class="form-section">
              <label class="section-label">选择封面</label>
              <div class="cover-grid">
                <div 
                  v-for="(img, idx) in images" 
                  :key="idx"
                  class="cover-item"
                  :class="{ active: selectedCover === idx }"
                  @click="selectedCover = idx"
                >
                  <img :src="img.url" />
                  <div v-if="selectedCover === idx" class="cover-check">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            <!-- 标题 -->
            <div class="form-section">
              <label class="section-label">标题</label>
              <div v-if="initialTitles.length > 0" class="title-options">
                <button
                  v-for="(t, idx) in initialTitles"
                  :key="idx"
                  class="title-option-btn"
                  :class="{ active: title.trim() === t.trim() }"
                  @click="title = truncateTitle(t)"
                >
                  备选{{ idx + 1 }}: {{ t }}
                </button>
              </div>
              <textarea 
                v-model="title" 
                class="form-textarea"
                placeholder="请输入笔记标题"
                rows="2"
                :maxlength="MAX_TITLE_LENGTH"
              ></textarea>
              <div class="char-count">{{ Array.from(title).length }}/{{ MAX_TITLE_LENGTH }}</div>
            </div>

            <!-- 正文 -->
            <div class="form-section">
              <label class="section-label">正文</label>
              <textarea 
                v-model="content" 
                class="form-textarea"
                placeholder="请输入笔记正文"
                rows="6"
              ></textarea>
            </div>

            <!-- 标签 -->
            <div class="form-section">
              <label class="section-label">标签</label>
              <input 
                v-model="tagsInput" 
                class="form-input"
                placeholder="用逗号分隔，如：护肤，教程"
              />
            </div>

            <!-- 错误提示 -->
            <div v-if="error" class="error-message">
              {{ error }}
            </div>
          </div>
        </div>

        <div class="modal-footer" v-if="isLoggedIn">
          <button class="btn btn-outline" @click="handleClose">取消</button>
          <button 
            class="btn btn-primary" 
            @click="handlePublish"
            :disabled="publishing"
          >
            {{ publishing ? '发布中...' : '立即发布' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getXhsAuthStatus, publishNote } from '../../api'
import { MAX_TITLE_LENGTH, truncateTitle, truncateTitles } from '../../utils/title'

const props = defineProps<{
  visible: boolean
  images: { url: string }[]
  initialTitles?: string[]
  initialTitle?: string
  initialContent?: string
  initialTags?: string[]
}>()

const emit = defineEmits<{
  close: []
  published: [result: { note_id: string; url: string }]
}>()

const router = useRouter()

const isLoggedIn = ref(false)
const selectedCover = ref(0)
const title = ref('')
const content = ref('')
const tagsInput = ref('')
const publishing = ref(false)
const error = ref('')
const initialTitles = computed(() => truncateTitles((props.initialTitles || []).filter(t => !!t?.trim())))

watch(() => props.visible, async (val) => {
  if (val) {
    await checkLoginStatus()
    title.value = truncateTitle(props.initialTitle || initialTitles.value[0] || '')
    content.value = props.initialContent || ''
    tagsInput.value = props.initialTags?.join(', ') || ''
  }
})

watch(title, (val) => {
  const trimmed = truncateTitle(val)
  if (trimmed !== val) {
    title.value = trimmed
  }
})

async function checkLoginStatus() {
  try {
    const status = await getXhsAuthStatus()
    isLoggedIn.value = status.logged_in
  } catch (e) {
    isLoggedIn.value = false
  }
}

function goToSettings() {
  router.push('/settings/xhs')
  emit('close')
}

function handleClose() {
  emit('close')
}

async function handlePublish() {
  if (!title.value.trim()) {
    error.value = '请输入标题'
    return
  }

  if (props.images.length === 0) {
    error.value = '没有可用的图片'
    return
  }

  error.value = ''
  publishing.value = true

  try {
    const toImagePath = (rawUrl: string): string => {
      const imageUrl = new URL(rawUrl, window.location.origin)
      const pathname = imageUrl.pathname
      if (pathname.startsWith('/api/images/')) {
        return '/output/' + pathname.slice('/api/images/'.length)
      }
      if (pathname.startsWith('/output/')) {
        return pathname
      }
      return pathname
    }

    // 发布整组图片，选中的封面排在第一位
    const allPaths = props.images.map(img => toImagePath(img.url))
    const coverFirst = [
      allPaths[selectedCover.value],
      ...allPaths.filter((_, idx) => idx !== selectedCover.value)
    ].filter(Boolean)

    const tags = tagsInput.value
      .split(',')
      .map(t => t.trim())
      .filter(t => t)

    const safeTitle = truncateTitle(title.value)
    const result = await publishNote({
      title: safeTitle,
      content: content.value,
      image_paths: coverFirst,
      tags
    })

    if (result.success) {
      emit('published', { note_id: result.note_id || '', url: result.url || '' })
      emit('close')
    } else {
      error.value = result.error || '发布失败'
    }
  } catch (e: any) {
    error.value = e.message || '发布失败'
  } finally {
    publishing.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 520px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  border: none;
  background: none;
  cursor: pointer;
  color: #999;
  padding: 4px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.login-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px 20px;
  text-align: center;
}

.icon-area {
  width: 80px;
  height: 80px;
  background: #fff5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-prompt p {
  color: #666;
  margin: 0;
}

.form-section {
  margin-bottom: 20px;
}

.section-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.char-count {
  margin-top: 6px;
  text-align: right;
  font-size: 12px;
  color: #999;
}

.cover-grid {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.cover-item {
  position: relative;
  width: 80px;
  height: 107px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  flex-shrink: 0;
}

.cover-item.active {
  border-color: #ff2442;
}

.cover-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-check {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: #ff2442;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-textarea,
.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  resize: none;
  font-family: inherit;
}

.title-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}

.title-option-btn {
  border: 1px solid #e8e8e8;
  background: #fff;
  color: #333;
  font-size: 13px;
  padding: 8px 10px;
  border-radius: 8px;
  text-align: left;
  cursor: pointer;
}

.title-option-btn:hover {
  border-color: #ffb3bf;
}

.title-option-btn.active {
  border-color: #ff2442;
  background: #fff1f4;
  color: #a8071a;
}

.form-textarea:focus,
.form-input:focus {
  outline: none;
  border-color: #ff2442;
}

.error-message {
  color: #ff4d4f;
  font-size: 14px;
  padding: 12px;
  background: #fff2f0;
  border-radius: 8px;
  margin-top: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #eee;
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
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
</style>
