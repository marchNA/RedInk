<template>
  <div class="container" style="max-width: 1100px;">
    <div class="page-header">
      <div>
        <h1 class="page-title">调试生图</h1>
        <p class="page-subtitle">使用当前图片供应商配置，调试 system 与 user（文本 + 图片）输入</p>
      </div>
      <div class="header-actions">
        <button class="btn" :disabled="isGenerating" @click="handleCopyRequestJson">
          复制请求 JSON
        </button>
        <button class="btn btn-primary" :disabled="isGenerating" @click="handleGenerate">
          {{ isGenerating ? '生成中...' : '开始调试生图' }}
        </button>
      </div>
    </div>

    <div class="workspace-grid">
      <div class="card form-card">
        <div class="field">
          <button class="toggle-system-btn" @click="showSystemPrompt = !showSystemPrompt">
            {{ showSystemPrompt ? '隐藏 System 文本' : '展开 System 文本（可选）' }}
          </button>
        </div>

        <div v-if="showSystemPrompt" class="field">
          <label class="field-label">System 角色（可选）</label>
          <textarea
            v-model="systemPrompt"
            class="field-input"
            rows="5"
            placeholder="例如：你是一名擅长小红书封面图设计的视觉总监。"
          />
        </div>

        <div class="field">
          <label class="field-label">User 角色（文本）</label>
          <textarea
            v-model="userPrompt"
            class="field-input"
            rows="10"
            placeholder="必填，例如：帮我生成一张上班族早晨通勤主题封面图，清新明亮，留出标题区。"
          />
        </div>

        <div class="field">
          <label class="field-label">User 角色（图片）</label>
          <div class="upload-row">
            <label class="btn upload-btn">
              上传参考图
              <input type="file" accept="image/*" multiple class="file-input" @change="handleFileChange" />
            </label>
            <button class="btn" :disabled="uploadedImages.length === 0" @click="clearImages">清空图片</button>
            <span class="hint">最多 6 张</span>
          </div>

          <div v-if="uploadedImages.length > 0" class="image-list">
            <div v-for="(item, idx) in uploadedImages" :key="idx" class="image-item">
              <img :src="item.preview" :alt="`user-image-${idx}`" />
              <button class="remove-btn" @click="removeImage(idx)">×</button>
            </div>
          </div>
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>
        <div v-if="copyMessage" class="success-msg">{{ copyMessage }}</div>
      </div>

      <div class="card result-card">
        <div class="result-header">
          <h3>生成结果</h3>
        </div>

        <img v-if="resultImage" :src="resultImage" alt="debug-result" class="result-image" />
        <div v-else class="result-empty">暂无结果，先在左侧输入 User 文本并点击“开始调试生图”。</div>

        <div v-if="resultProvider" class="provider-meta">
          <div><strong>激活供应商：</strong>{{ resultProvider.active_provider }}</div>
          <div><strong>类型：</strong>{{ resultProvider.type }}</div>
          <div><strong>模型：</strong>{{ resultProvider.model || '-' }}</div>
          <div><strong>端点：</strong>{{ resultProvider.endpoint_type || '-' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import {
  debugGenerateImage,
  type DebugImageProviderInfo
} from '../api'

interface UploadedImage {
  file: File
  preview: string
}

const systemPrompt = ref('')
const userPrompt = ref('')
const showSystemPrompt = ref(false)
const uploadedImages = ref<UploadedImage[]>([])
const isGenerating = ref(false)
const error = ref('')
const copyMessage = ref('')
const resultImage = ref('')
const resultProvider = ref<DebugImageProviderInfo | null>(null)

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files || [])
  if (files.length === 0) return

  const remain = 6 - uploadedImages.value.length
  files.slice(0, Math.max(0, remain)).forEach((file) => {
    const preview = URL.createObjectURL(file)
    uploadedImages.value.push({ file, preview })
  })

  target.value = ''
}

function removeImage(index: number) {
  const item = uploadedImages.value[index]
  if (!item) return
  URL.revokeObjectURL(item.preview)
  uploadedImages.value.splice(index, 1)
}

function clearImages() {
  uploadedImages.value.forEach((item) => URL.revokeObjectURL(item.preview))
  uploadedImages.value = []
}

async function handleGenerate() {
  if (!userPrompt.value.trim()) {
    error.value = '请先填写 User 角色文本'
    return
  }

  error.value = ''
  copyMessage.value = ''
  isGenerating.value = true
  resultImage.value = ''

  try {
    const response = await debugGenerateImage(
      systemPrompt.value.trim(),
      userPrompt.value.trim(),
      uploadedImages.value.map((item) => item.file)
    )

    if (!response.success || !response.image_base64) {
      error.value = response.error || '生成失败'
      return
    }

    resultImage.value = response.image_base64
    resultProvider.value = response.provider || null
  } catch (e: any) {
    error.value = e?.response?.data?.error || e?.message || '生成失败'
  } finally {
    isGenerating.value = false
  }
}

async function handleCopyRequestJson() {
  copyMessage.value = ''
  error.value = ''

  try {
    const userImagesBase64 = await Promise.all(
      uploadedImages.value.map(async (item) => fileToDataUrl(item.file))
    )

    const payload = {
      system_prompt: systemPrompt.value.trim(),
      user_prompt: userPrompt.value.trim(),
      user_images: userImagesBase64
    }

    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2))
    copyMessage.value = '请求 JSON 已复制到剪贴板'
  } catch (e: any) {
    error.value = e?.message || '复制请求 JSON 失败'
  }
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('图片转 base64 失败'))
    reader.readAsDataURL(file)
  })
}

onBeforeUnmount(() => {
  clearImages()
})
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 10px;
}

.form-card {
  margin-bottom: 0;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(360px, 1fr) minmax(320px, 1fr);
  gap: 16px;
  align-items: start;
}

.field {
  margin-bottom: 14px;
}

.field-label {
  display: block;
  font-size: 13px;
  color: var(--text-sub);
  margin-bottom: 8px;
}

.field-input {
  width: 100%;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px 12px;
  resize: vertical;
  font-family: inherit;
  line-height: 1.6;
}

.toggle-system-btn {
  border: 1px dashed var(--border-color);
  background: #fff;
  color: var(--text-sub);
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.upload-btn {
  position: relative;
  overflow: hidden;
}

.file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.hint {
  color: var(--text-sub);
  font-size: 12px;
}

.image-list {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}

.image-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  background: #fff;
  aspect-ratio: 1 / 1;
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.remove-btn {
  position: absolute;
  right: 6px;
  top: 6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 0;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  cursor: pointer;
}

.result-card {
  min-height: 420px;
}

.result-header h3 {
  margin: 0 0 12px;
}

.result-image {
  width: 100%;
  max-height: 760px;
  object-fit: contain;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: #fafafa;
}

.result-empty {
  min-height: 220px;
  border: 1px dashed var(--border-color);
  border-radius: 12px;
  color: var(--text-sub);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  text-align: center;
  background: #fff;
}

.provider-meta {
  margin-top: 12px;
  display: grid;
  gap: 6px;
  font-size: 14px;
}

@media (max-width: 900px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }
}
</style>
