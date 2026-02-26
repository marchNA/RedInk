<template>
  <section class="brainstorm-section" :class="{ embedded }">
    <div class="brainstorm-header">
      <div>
        <h2 class="section-title">创意风暴</h2>
        <p class="section-subtitle">先对话打磨思路，再一键进入大纲与配图流程</p>
      </div>
      <div class="action-group">
        <button class="btn" :disabled="messages.length < 2 || composing || sending" @click="handleComposeText">
          {{ composing ? '生成中...' : '1. 生成文字内容' }}
        </button>
        <button class="btn" :disabled="!draftReady || composing || sending" @click="goOutlineEdit">
          去编辑大纲
        </button>
        <button class="btn btn-primary" :disabled="!draftReady || composing || sending" @click="handleGenerateImages">
          2. 生成图片
        </button>
      </div>
    </div>

    <div class="card chat-card">
      <div class="chat-list">
        <div v-if="messages.length === 0" class="empty-tip">
          先说你的想法，比如：我想做一篇关于「上班族低成本减脂」的笔记，但不想太说教。
        </div>
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="chat-item"
          :class="msg.role"
        >
          <div class="bubble">{{ msg.content }}</div>
        </div>
      </div>

      <div v-if="quickOptions.length > 0" class="quick-options">
        <button
          v-for="(opt, idx) in quickOptions"
          :key="idx"
          class="quick-btn"
          :disabled="sending || composing"
          @click="applyQuickOption(opt)"
        >
          {{ opt }}
        </button>
      </div>

      <div class="composer">
        <textarea
          v-model="inputText"
          class="chat-input"
          rows="3"
          placeholder="继续聊你的目标人群、场景、语气、结构偏好..."
          :disabled="sending || composing"
          @keydown.enter.exact.prevent="handleSend"
        />
        <button class="btn" :disabled="!inputText.trim() || sending || composing" @click="handleSend">
          {{ sending ? '思考中...' : '发送' }}
        </button>
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>
      <div v-if="success" class="success-msg">{{ success }}</div>
    </div>

    <div v-if="draftReady" class="card preview-card">
      <div class="preview-head">
        <h3>文字内容预览（确认无误后再生成图片）</h3>
      </div>

      <div class="preview-block">
        <div class="preview-label">主题</div>
        <div class="preview-value">{{ store.topic }}</div>
      </div>

      <div class="preview-block">
        <div class="preview-label">主标题</div>
        <div class="preview-value">{{ store.content.titles?.[0] || '-' }}</div>
      </div>

      <div class="preview-block">
        <div class="preview-label">标签</div>
        <div class="preview-tags">
          <span v-for="(tag, idx) in store.content.tags" :key="idx" class="tag-chip">{{ tag }}</span>
          <span v-if="store.content.tags.length === 0">-</span>
        </div>
      </div>

      <div class="preview-block">
        <div class="preview-label">正文</div>
        <div class="preview-body">{{ store.content.copywriting || '-' }}</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGeneratorStore } from '../../stores/generator'
import {
  brainstormChat,
  brainstormCompose,
  createHistory,
  type BrainstormMessage
} from '../../api'

withDefaults(defineProps<{ embedded?: boolean }>(), {
  embedded: false
})

const router = useRouter()
const store = useGeneratorStore()

const messages = ref<BrainstormMessage[]>([])
const quickOptions = ref<string[]>([])
const inputText = ref('')
const sending = ref(false)
const composing = ref(false)
const draftReady = ref(false)
const error = ref('')
const success = ref('')

async function handleSend() {
  const text = inputText.value.trim()
  if (!text) return

  error.value = ''
  success.value = ''
  sending.value = true
  messages.value.push({ role: 'user', content: text })
  inputText.value = ''

  try {
    const res = await brainstormChat(messages.value, text)
    if (!res.success || !res.assistant_reply) {
      error.value = res.error || '对话失败'
      return
    }
    messages.value.push({ role: 'assistant', content: res.assistant_reply })
    quickOptions.value = res.next_options || []
  } catch (e: any) {
    error.value = e.message || '对话失败'
  } finally {
    sending.value = false
  }
}

function applyQuickOption(option: string) {
  inputText.value = option
}

async function handleComposeText() {
  if (messages.value.length < 2) return

  error.value = ''
  success.value = ''
  composing.value = true

  try {
    const res = await brainstormCompose(messages.value)
    if (!res.success || !res.pages || !res.outline) {
      error.value = res.error || '成稿失败'
      return
    }

    store.reset()
    store.setTopic((res.topic || '创意风暴笔记').trim())
    store.setOutline(res.outline, res.pages)

    if (res.content) {
      store.setContent(
        res.content.titles || [],
        res.content.copywriting || '',
        res.content.tags || []
      )
    }

    const historyResult = await createHistory(store.topic, {
      raw: res.outline,
      pages: res.pages
    }, undefined, {
      titles: store.content.titles,
      copywriting: store.content.copywriting,
      tags: store.content.tags
    })
    if (historyResult.success && historyResult.record_id) {
      store.setRecordId(historyResult.record_id)
    } else {
      store.setRecordId(null)
    }

    draftReady.value = true
    success.value = '文字内容已生成。请先检查预览，确认后再点“生成图片”。'
  } catch (e: any) {
    error.value = e.message || '成稿失败'
  } finally {
    composing.value = false
  }
}

function goOutlineEdit() {
  if (!draftReady.value) return
  router.push('/outline')
}

function handleGenerateImages() {
  if (!draftReady.value) return
  router.push('/generate')
}
</script>

<style scoped>
.brainstorm-section {
  margin-bottom: 30px;
  padding: 26px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
}

.brainstorm-section.embedded {
  margin-bottom: 0;
  padding: 0;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  backdrop-filter: none;
}

.brainstorm-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.section-title {
  margin: 0 0 6px;
  font-size: 24px;
}

.section-subtitle {
  margin: 0;
  color: var(--text-sub);
}

.action-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.chat-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chat-list {
  min-height: 300px;
  max-height: 58vh;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 14px;
  background: #fcfcfc;
}

.chat-item {
  display: flex;
  margin-bottom: 10px;
}

.chat-item.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 75%;
  padding: 10px 12px;
  border-radius: 10px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.chat-item.user .bubble {
  background: #ffeef2;
}

.chat-item.assistant .bubble {
  background: #f3f5f7;
}

.empty-tip {
  color: var(--text-sub);
  font-size: 14px;
}

.quick-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-btn {
  border: 1px solid var(--border-color);
  background: #fff;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
}

.composer {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px 12px;
  resize: vertical;
  font-family: inherit;
}

.preview-card {
  margin-top: 16px;
}

.preview-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.preview-head h3 {
  margin: 0;
}

.preview-block {
  margin-bottom: 14px;
}

.preview-label {
  color: var(--text-sub);
  font-size: 12px;
  margin-bottom: 6px;
}

.preview-value {
  font-weight: 600;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: #f5f5f5;
}

.preview-body {
  white-space: pre-wrap;
  line-height: 1.7;
  background: #fcfcfc;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 12px;
}

.success-msg {
  color: #237804;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  padding: 10px 12px;
  border-radius: 8px;
}

@media (max-width: 900px) {
  .brainstorm-header {
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .brainstorm-section {
    padding: 18px;
  }

  .composer {
    flex-direction: column;
    align-items: stretch;
  }

  .bubble {
    max-width: 92%;
  }
}
</style>
