<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="handleClose">
      <div class="modal-content">
        <div class="modal-header">
          <h2>内容调优</h2>
          <button class="close-btn" @click="handleClose">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <div class="optimize-type">
            <button 
              class="type-btn"
              :class="{ active: optimizeType === 'all' }"
              @click="optimizeType = 'all'"
            >
              一键优化
            </button>
            <button 
              class="type-btn"
              :class="{ active: optimizeType === 'title' }"
              @click="optimizeType = 'title'"
            >
              优化标题
            </button>
            <button 
              class="type-btn"
              :class="{ active: optimizeType === 'content' }"
              @click="optimizeType = 'content'"
            >
              优化正文
            </button>
          </div>

          <!-- 标题 -->
          <div class="form-section">
            <label class="section-label">
              标题
              <button class="optimize-btn" @click="handleOptimizeTitle" :disabled="optimizing">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
                优化
              </button>
            </label>
            <textarea 
              v-model="localTitle" 
              class="form-textarea"
              placeholder="请输入标题"
              rows="2"
              :maxlength="MAX_TITLE_LENGTH"
            ></textarea>
            <div class="char-count">{{ Array.from(localTitle).length }}/{{ MAX_TITLE_LENGTH }}</div>
          </div>

          <!-- 正文 -->
          <div class="form-section">
            <label class="section-label">
              正文
              <button class="optimize-btn" @click="handleOptimizeContent" :disabled="optimizing">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
                优化
              </button>
            </label>
            <textarea 
              v-model="localContent" 
              class="form-textarea"
              placeholder="请输入正文"
              rows="8"
            ></textarea>
          </div>

          <!-- 标签 -->
          <div class="form-section">
            <label class="section-label">标签</label>
            <input 
              v-model="localTagsInput" 
              class="form-input"
              placeholder="用逗号分隔"
            />
          </div>

          <!-- 加载中 -->
          <div v-if="optimizing" class="loading-area">
            <div class="spinner"></div>
            <span>AI 优化中...</span>
          </div>

          <!-- 错误提示 -->
          <div v-if="error" class="error-message">
            {{ error }}
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-outline" @click="handleClose">取消</button>
          <button class="btn btn-primary" @click="handleApply" :disabled="applying">
            {{ applying ? '应用...' : '应用修改' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { refineTitle, refineContent, refineAll } from '../../api'
import { MAX_TITLE_LENGTH, truncateTitle } from '../../utils/title'

const props = defineProps<{
  visible: boolean
  initialTitle?: string
  initialContent?: string
  initialTags?: string[]
}>()

const emit = defineEmits<{
  close: []
  apply: [data: { title: string; content: string; tags: string[] }]
}>()

const optimizeType = ref<'all' | 'title' | 'content'>('all')
const localTitle = ref('')
const localContent = ref('')
const localTagsInput = ref('')
const optimizing = ref(false)
const applying = ref(false)
const error = ref('')

watch(() => props.visible, (val) => {
  if (val) {
    localTitle.value = truncateTitle(props.initialTitle || '')
    localContent.value = props.initialContent || ''
    localTagsInput.value = props.initialTags?.join(', ') || ''
    error.value = ''
  }
})

watch(localTitle, (val) => {
  const normalized = truncateTitle(val)
  if (normalized !== val) {
    localTitle.value = normalized
  }
})

function handleClose() {
  emit('close')
}

async function handleOptimizeTitle() {
  if (!localTitle.value.trim()) {
    error.value = '请先输入标题'
    return
  }

  optimizing.value = true
  error.value = ''

  try {
    const result = await refineTitle(localTitle.value)
    if (result.success && result.optimized_title) {
      localTitle.value = truncateTitle(result.optimized_title)
    } else {
      error.value = result.error || '优化失败'
    }
  } catch (e: any) {
    error.value = e.message || '优化失败'
  } finally {
    optimizing.value = false
  }
}

async function handleOptimizeContent() {
  if (!localContent.value.trim()) {
    error.value = '请先输入正文'
    return
  }

  optimizing.value = true
  error.value = ''

  try {
    const result = await refineContent(localContent.value)
    if (result.success && result.optimized_content) {
      localContent.value = result.optimized_content
    } else {
      error.value = result.error || '优化失败'
    }
  } catch (e: any) {
    error.value = e.message || '优化失败'
  } finally {
    optimizing.value = false
  }
}

async function handleOptimizeAll() {
  if (!localTitle.value.trim() && !localContent.value.trim()) {
    error.value = '请先输入标题或正文'
    return
  }

  optimizing.value = true
  error.value = ''

  try {
    const result = await refineAll({
      title: localTitle.value,
      content: localContent.value
    })
    
    if (result.success) {
      if (result.optimized_title) {
        localTitle.value = truncateTitle(result.optimized_title)
      }
      if (result.optimized_content) {
        localContent.value = result.optimized_content
      }
      if (result.tags && result.tags.length > 0) {
        localTagsInput.value = result.tags.join(', ')
      }
    } else {
      error.value = result.error || '优化失败'
    }
  } catch (e: any) {
    error.value = e.message || '优化失败'
  } finally {
    optimizing.value = false
  }
}

function handleApply() {
  applying.value = true
  
  const tags = localTagsInput.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t)

  emit('apply', {
    title: truncateTitle(localTitle.value),
    content: localContent.value,
    tags
  })
  
  applying.value = false
  emit('close')
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
  max-width: 560px;
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

.optimize-type {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  background: #f5f5f5;
  padding: 4px;
  border-radius: 8px;
}

.type-btn {
  flex: 1;
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.type-btn.active {
  background: #fff;
  color: #ff2442;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.form-section {
  margin-bottom: 16px;
}

.section-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.optimize-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: none;
  background: #fff5f5;
  color: #ff2442;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.optimize-btn:hover:not(:disabled) {
  background: #ffeaea;
}

.optimize-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.form-textarea:focus,
.form-input:focus {
  outline: none;
  border-color: #ff2442;
}

.char-count {
  margin-top: 6px;
  text-align: right;
  font-size: 12px;
  color: #999;
}

.loading-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  color: #666;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f0f0f0;
  border-top-color: #ff2442;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: #ff4d4f;
  font-size: 14px;
  padding: 12px;
  background: #fff2f0;
  border-radius: 8px;
  margin-top: 12px;
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
