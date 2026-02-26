<template>
  <!-- 图片画廊模态框 -->
  <div v-if="visible && record" class="modal-fullscreen" @click="$emit('close')">
    <div class="modal-body" @click.stop>
      <!-- 头部区域 -->
      <div class="modal-header">
        <div style="flex: 1;">
          <!-- 标题区域 -->
          <div class="title-section">
            <h3
              class="modal-title"
              :class="{ 'collapsed': !titleExpanded && record.title.length > 80 }"
            >
              {{ record.title }}
            </h3>
            <button
              v-if="record.title.length > 80"
              class="title-expand-btn"
              @click="titleExpanded = !titleExpanded"
            >
              {{ titleExpanded ? '收起' : '展开' }}
            </button>
          </div>

          <div class="modal-meta">
            <span>{{ record.outline.pages.length }} 张图片 · {{ formattedDate }}</span>
            <button
              class="view-outline-btn"
              @click="$emit('showOutline')"
              title="查看完整大纲"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
              </svg>
              查看大纲
            </button>
          </div>
        </div>

        <div class="header-actions">
          <button
            v-if="canContinueGenerate"
            class="btn continue-btn"
            @click="$emit('continueGenerate')"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            继续生成图片
          </button>
          <button class="btn publish-btn" @click="$emit('publish')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
              <polyline points="22,6 12,13 2,6"></polyline>
            </svg>
            发布笔记
          </button>
          <button class="btn optimize-btn-header" @click="openRefineModal">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
            内容调优
          </button>
          <button class="btn download-btn" @click="$emit('downloadAll')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            打包下载
          </button>
          <button class="close-icon" @click="$emit('close')">×</button>
        </div>
      </div>

      <!-- 主内容区：图片网格 + 编辑面板 -->
      <div class="modal-main">
        <!-- 图片网格 -->
        <div class="modal-gallery-grid">
          <div
            v-for="(img, idx) in record.images.generated"
            :key="idx"
            class="modal-img-item"
            :class="{ 'selected': selectedImageIndex === idx }"
            @click="selectImage(idx)"
          >
            <div
              class="modal-img-preview"
              v-if="img"
              :class="{ 'regenerating': regeneratingImages.has(idx) }"
            >
              <img
                :src="`/api/images/${record.images.task_id}/${img}`"
                loading="lazy"
                decoding="async"
                @click.stop="openImagePreview(idx, img)"
              />
              <div class="modal-img-overlay">
                <button
                  class="modal-overlay-btn"
                  @click.stop="openImagePreview(idx, img)"
                >
                  查看大图
                </button>
                <button
                  class="modal-overlay-btn"
                  @click.stop="$emit('regenerate', idx)"
                  :disabled="regeneratingImages.has(idx)"
                >
                  <svg class="regenerate-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M23 4v6h-6"></path>
                    <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                  </svg>
                  {{ regeneratingImages.has(idx) ? '重绘中...' : '重新生成' }}
                </button>
              </div>
            </div>
            <div class="placeholder" v-else>Waiting...</div>

            <div class="img-footer">
              <span>Page {{ idx + 1 }}</span>
              <span
                v-if="img"
                class="download-link"
                @click.stop="$emit('download', img, idx)"
              >
                下载
              </span>
            </div>
          </div>
        </div>

        <!-- 悬浮编辑面板 -->
        <div class="edit-panel" :class="{ 'show': showEditPanel }">
          <div class="edit-panel-header">
            <h4>编辑内容 - Page {{ selectedImageIndex + 1 }}</h4>
            <button class="close-panel-btn" @click="showEditPanel = false">×</button>
          </div>
          <div class="edit-panel-body">
            <div class="form-group" v-if="isCoverPage">
              <label>标题</label>
              <textarea
                v-model="localTitle"
                rows="2"
                placeholder="请输入标题"
                :maxlength="MAX_TITLE_LENGTH"
              ></textarea>
              <div class="char-count">{{ Array.from(localTitle).length }}/{{ MAX_TITLE_LENGTH }}</div>
            </div>
            <div v-else class="title-lock-tip">
              仅第 1 张（封面）可编辑标题
            </div>
            <div class="form-group">
              <label>正文</label>
              <textarea
                v-model="localContent"
                rows="10"
                placeholder="请输入正文"
                class="content-textarea"
              ></textarea>
            </div>
            <div class="form-group">
              <label>标签</label>
              <input
                v-model="localTags"
                placeholder="用逗号分隔"
              />
            </div>
          </div>
          <div class="edit-panel-footer">
            <button class="btn btn-outline" @click="handleOptimize" :disabled="optimizing">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
              </svg>
              {{ optimizing ? '优化中...' : 'AI 优化' }}
            </button>
            <button class="btn btn-primary" @click="handleSave" :disabled="saving">
              {{ saving ? '保存中...' : '保存修改' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 大图预览层（站内弹窗） -->
    <div
      v-if="imagePreviewVisible"
      class="image-preview-overlay"
      @click="closeImagePreview"
    >
      <div class="image-preview-content" @click.stop>
        <button class="image-preview-nav prev" @click.stop="previewPrev">‹</button>
        <button class="image-preview-nav next" @click.stop="previewNext">›</button>
        <button class="image-preview-close" @click="closeImagePreview">×</button>
        <div class="image-preview-title">第 {{ imagePreviewIndex + 1 }} 张</div>
        <img :src="imagePreviewUrl" class="image-preview-img" alt="预览大图" />
      </div>
    </div>

    <!-- 内容调优弹窗 -->
    <RefineModal
      :visible="showRefineModal"
      :initialTitle="localTitle"
      :initialContent="localContent"
      :initialTags="localTagsArray"
      @close="showRefineModal = false"
      @apply="handleRefineApply"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { refineContent, refineAll } from '../../api'
import RefineModal from '../result/RefineModal.vue'
import { MAX_TITLE_LENGTH, truncateTitle } from '../../utils/title'

/**
 * 图片画廊模态框组件
 *
 * 功能：
 * - 展示历史记录的所有生成图片
 * - 支持重新生成单张图片
 * - 支持下载单张/全部图片
 * - 可展开查看完整大纲
 * - 支持内容编辑和 AI 调优
 */

// 定义记录类型
interface ViewingRecord {
  id: string
  title: string
  status: 'draft' | 'completed' | 'generating' | 'partial' | 'error'
  updated_at: string
  outline: {
    raw: string
    pages: Array<{ type: string; content: string }>
  }
  images: {
    task_id: string
    generated: string[]
  }
  // 新增：内容字段
  content?: {
    titles: string[]
    copywriting: string
    tags: string[]
  }
}

// 定义 Props
const props = defineProps<{
  visible: boolean
  record: ViewingRecord | null
  regeneratingImages: Set<number>
}>()

// 定义 Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'showOutline'): void
  (e: 'publish'): void
  (e: 'continueGenerate'): void
  (e: 'downloadAll'): void
  (e: 'download', filename: string, index: number): void
  (e: 'regenerate', index: number): void
  (e: 'saveContent', data: { title: string; content: string; tags: string[] }): void
}>()

// 标题展开状态
const titleExpanded = ref(false)

// 选中图片索引
const selectedImageIndex = ref(0)

// 本地内容编辑状态
const localTitle = ref('')
const localContent = ref('')
const localTags = ref('')

// 调优弹窗状态
const showRefineModal = ref(false)
const showEditPanel = ref(false)
const optimizing = ref(false)
const saving = ref(false)
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const imagePreviewIndex = ref(0)

// 标签数组
const localTagsArray = computed(() => {
  return localTags.value.split(',').map(t => t.trim()).filter(t => t)
})

const isCoverPage = computed(() => selectedImageIndex.value === 0)
const canContinueGenerate = computed(() => {
  return !!props.record && ['draft', 'partial', 'error'].includes(props.record.status)
})

// 监听弹窗打开，初始化内容
watch(() => props.visible, (val) => {
  if (val && props.record) {
    // 优先使用 content 字段，否则从 outline 中获取
    if (props.record.content) {
      localTitle.value = truncateTitle(props.record.content.titles?.[0] || props.record.title || '')
      localContent.value = props.record.content.copywriting || ''
      localTags.value = props.record.content.tags?.join(', ') || ''
    } else {
      localTitle.value = truncateTitle(props.record.title || '')
      // 从 outline 中获取第一页的内容作为默认内容
      const firstPage = props.record.outline.pages?.[0]
      localContent.value = firstPage?.content || ''
      localTags.value = ''
    }
    // 默认选中第一张图片
    selectedImageIndex.value = 0
    selectImage(0)
  }
})

// 监听选中图片变化，更新内容
watch(selectedImageIndex, (idx) => {
  updateLocalContentByIndex(idx)
  // 选中图片时自动显示编辑面板
  showEditPanel.value = true
})

watch(localTitle, (val) => {
  const normalized = truncateTitle(val)
  if (normalized !== val) {
    localTitle.value = normalized
  }
})

function updateLocalContentByIndex(idx: number) {
  if (props.record && props.record.outline.pages && props.record.outline.pages[idx]) {
    const page = props.record.outline.pages[idx]
    localContent.value = page.content || ''
  }
}

function selectImage(idx: number) {
  if (selectedImageIndex.value !== idx) {
    selectedImageIndex.value = idx
    return
  }
  // 即使重复点击当前图片，也要能打开面板并刷新对应内容
  updateLocalContentByIndex(idx)
  showEditPanel.value = true
}

function openImagePreview(idx: number, filename: string) {
  if (!props.record) return
  imagePreviewIndex.value = idx
  imagePreviewUrl.value = `/api/images/${props.record.images.task_id}/${filename}`
  imagePreviewVisible.value = true
}

function closeImagePreview() {
  imagePreviewVisible.value = false
  imagePreviewUrl.value = ''
}

function openRefineModal() {
  if (!props.record) return

  const fallbackTitle =
    (localTitle.value || '').trim() ||
    (props.record.content?.titles?.[0] || '').trim() ||
    (props.record.title || '').trim()

  if (fallbackTitle) {
    localTitle.value = truncateTitle(fallbackTitle)
  }

  showRefineModal.value = true
}

function previewPrev() {
  if (!props.record) return
  const total = props.record.images.generated.length
  if (total === 0) return
  const nextIndex = (imagePreviewIndex.value - 1 + total) % total
  const filename = props.record.images.generated[nextIndex]
  if (!filename) return
  imagePreviewIndex.value = nextIndex
  imagePreviewUrl.value = `/api/images/${props.record.images.task_id}/${filename}`
}

function previewNext() {
  if (!props.record) return
  const total = props.record.images.generated.length
  if (total === 0) return
  const nextIndex = (imagePreviewIndex.value + 1) % total
  const filename = props.record.images.generated[nextIndex]
  if (!filename) return
  imagePreviewIndex.value = nextIndex
  imagePreviewUrl.value = `/api/images/${props.record.images.task_id}/${filename}`
}

function handlePreviewKeydown(e: KeyboardEvent) {
  if (!imagePreviewVisible.value) return

  if (e.key === 'ArrowLeft') {
    e.preventDefault()
    previewPrev()
    return
  }
  if (e.key === 'ArrowRight') {
    e.preventDefault()
    previewNext()
    return
  }
  if (e.key === 'Escape') {
    e.preventDefault()
    closeImagePreview()
  }
}

watch(imagePreviewVisible, (visible) => {
  if (visible) {
    window.addEventListener('keydown', handlePreviewKeydown)
  } else {
    window.removeEventListener('keydown', handlePreviewKeydown)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handlePreviewKeydown)
})

// 格式化日期
const formattedDate = computed(() => {
  if (!props.record) return ''
  const d = new Date(props.record.updated_at)
  return `${d.getMonth() + 1}/${d.getDate()}`
})

// AI 优化处理
async function handleOptimize() {
  optimizing.value = true

  try {
    if (isCoverPage.value) {
      if (!localTitle.value.trim() && !localContent.value.trim()) {
        alert('请先输入标题或正文')
        return
      }

      // 封面页：一键优化标题、正文、标签
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
          localTags.value = result.tags.join(', ')
        }
      } else {
        alert(result.error || '优化失败')
      }
    } else {
      if (!localContent.value.trim()) {
        alert('请先输入正文')
        return
      }

      // 非封面页：只优化当前页正文，避免修改全局标题
      const result = await refineContent(localContent.value)
      if (result.success && result.optimized_content) {
        localContent.value = result.optimized_content
      } else {
        alert(result.error || '优化失败')
      }
    }
  } catch (e: any) {
    alert(e.message || '优化失败')
  } finally {
    optimizing.value = false
  }
}

// 保存内容
async function handleSave() {
  if (!props.record) return

  saving.value = true

  try {
    const tags = localTagsArray.value
    emit('saveContent', {
      title: truncateTitle(localTitle.value),
      content: localContent.value,
      tags
    })
    alert('保存成功')
  } catch (e: any) {
    alert(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// 调优弹窗应用回调
function handleRefineApply(data: { title: string; content: string; tags: string[] }) {
  localTitle.value = truncateTitle(data.title)
  localContent.value = data.content
  localTags.value = data.tags.join(', ')
  showRefineModal.value = false
}
</script>

<style scoped>
/* 全屏模态框遮罩 */
.modal-fullscreen {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

/* 模态框主体 */
.modal-body {
  background: white;
  width: 100%;
  max-width: 1000px;
  height: 90vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 头部区域 */
.modal-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-shrink: 0;
  gap: 20px;
}

/* 标题区域 */
.title-section {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 4px;
}

.modal-title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
  color: #1a1a1a;
  word-break: break-word;
  transition: max-height 0.3s ease;
}

.modal-title.collapsed {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.title-expand-btn {
  flex-shrink: 0;
  padding: 2px 8px;
  background: #f0f0f0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  color: #666;
  transition: all 0.2s;
  margin-top: 2px;
}

.title-expand-btn:hover {
  background: var(--primary, #ff2442);
  color: white;
}

/* 元信息 */
.modal-meta {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

/* 查看大纲按钮 */
.view-outline-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #495057;
  transition: all 0.2s;
}

.view-outline-btn:hover {
  background: var(--primary, #ff2442);
  color: white;
  border-color: var(--primary, #ff2442);
}

/* 头部操作区 */
.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.download-btn {
  padding: 8px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.publish-btn {
  padding: 8px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: #fff7f7;
  color: #ff2442;
  border: 1px solid #ffccd5;
}

.publish-btn:hover {
  background: #ffeef2;
}

.continue-btn {
  padding: 8px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f6ffed;
  color: #389e0d;
  border: 1px solid #b7eb8f;
}

.continue-btn:hover {
  background: #ecfcca;
}

.close-icon {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  line-height: 1;
}

.close-icon:hover {
  color: #333;
}

/* 主内容区 */
.modal-main {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

/* 图片网格 */
.modal-gallery-grid {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  align-content: start;
}

/* 单个图片项 */
.modal-img-item {
  display: flex;
  flex-direction: column;
}

/* 图片预览容器 */
.modal-img-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 3/4;
  overflow: hidden;
  border-radius: 8px;
  contain: layout style paint;
}

.modal-img-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 悬浮遮罩 */
.modal-img-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s ease-out;
  pointer-events: none;
  will-change: opacity;
}

.modal-img-preview:hover .modal-img-overlay {
  opacity: 1;
  pointer-events: auto;
}

/* 重绘中状态 */
.modal-img-preview.regenerating .modal-img-overlay {
  opacity: 1;
  pointer-events: auto;
}

.modal-img-preview.regenerating .regenerate-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 遮罩层按钮 */
.modal-overlay-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #333;
  transition: background-color 0.2s, color 0.2s, transform 0.1s;
  will-change: transform;
}

.modal-overlay-btn:hover {
  background: var(--primary, #ff2442);
  color: white;
  transform: scale(1.05);
}

.modal-overlay-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.image-preview-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.86);
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.image-preview-content {
  position: relative;
  max-width: min(90vw, 960px);
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.image-preview-title {
  color: #fff;
  margin-bottom: 10px;
  font-size: 14px;
}

.image-preview-img {
  max-width: 100%;
  max-height: calc(85vh - 48px);
  border-radius: 10px;
  object-fit: contain;
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.45);
}

.image-preview-close {
  position: absolute;
  top: -40px;
  right: 0;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.image-preview-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview-nav.prev {
  left: -56px;
}

.image-preview-nav.next {
  right: -56px;
}

/* 占位符 */
.placeholder {
  width: 100%;
  aspect-ratio: 3/4;
  background: #f5f5f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 14px;
}

/* 图片底部信息 */
.img-footer {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.download-link {
  cursor: pointer;
  color: var(--primary, #ff2442);
  transition: opacity 0.2s;
}

.download-link:hover {
  opacity: 0.7;
}

/* 响应式 */
@media (max-width: 768px) {
  .modal-fullscreen {
    padding: 20px;
  }

  .modal-gallery-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
    padding: 12px;
  }

  .image-preview-nav.prev {
    left: 8px;
  }

  .image-preview-nav.next {
    right: 8px;
  }
}

/* 头部优化按钮 */
.optimize-btn-header {
  padding: 8px 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: #fff5f5;
  color: #ff2442;
  border: 1px solid #ff2442;
}

.optimize-btn-header:hover {
  background: #ffeaea;
}

/* 选中状态 */
.modal-img-item.selected {
  outline: 3px solid #ff2442;
  outline-offset: 2px;
  border-radius: 8px;
}

/* 内容编辑区域 */
.content-edit-section {
  border-top: 1px solid #eee;
  padding: 16px 20px;
  background: #fafafa;
  flex-shrink: 0;
}

.content-edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.content-edit-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.selected-hint {
  font-size: 12px;
  color: #999;
}

.content-edit-body {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group:first-child {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  font-weight: 500;
}

.form-group textarea,
.form-group input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  resize: none;
}

.form-group textarea:focus,
.form-group input:focus {
  outline: none;
  border-color: #ff2442;
}

.content-edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-primary {
  background: #ff2442;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #e6203b;
}

.btn-primary:disabled {
  background: #ff99a8;
  cursor: not-allowed;
}

.btn-outline {
  background: white;
  color: #666;
  border: 1px solid #ddd;
}

.btn-outline:hover:not(:disabled) {
  background: #f5f5f5;
}

.btn-outline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 悬浮编辑面板 */
.edit-panel {
  width: 0;
  background: #fafafa;
  border-left: 1px solid #eee;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.edit-panel.show {
  width: 400px;
}

.edit-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  background: #fff;
}

.edit-panel-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.close-panel-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
  padding: 0;
  line-height: 1;
}

.close-panel-btn:hover {
  color: #333;
}

.edit-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.edit-panel-body .form-group {
  margin-bottom: 16px;
}

.title-lock-tip {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff7e6;
  border: 1px solid #ffd591;
  color: #ad6800;
  font-size: 13px;
}

.edit-panel-body .form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 6px;
}

.edit-panel-body .form-group textarea,
.edit-panel-body .form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  transition: border-color 0.2s;
}

.edit-panel-body .form-group textarea:focus,
.edit-panel-body .form-group input:focus {
  outline: none;
  border-color: #ff2442;
}

.char-count {
  margin-top: 6px;
  text-align: right;
  font-size: 12px;
  color: #999;
}

.edit-panel-body .content-textarea {
  min-height: 200px;
}

.edit-panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #eee;
  background: #fff;
}

/* 响应式 */
@media (max-width: 900px) {
  .edit-panel.show {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 100%;
    max-width: 400px;
    z-index: 10;
    box-shadow: -4px 0 20px rgba(0,0,0,0.15);
  }
}
</style>
