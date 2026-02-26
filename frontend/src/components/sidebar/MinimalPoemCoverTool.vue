<template>
  <section class="poem-tool">
    <button class="tool-toggle" type="button" @click="open = !open">
      <span>三行诗封面</span>
      <span>{{ open ? '收起' : '展开' }}</span>
    </button>

    <div v-if="open" class="tool-body">
      <div class="form-group">
        <label>第一行</label>
        <input v-model="line1" type="text" />
      </div>
      <div class="form-group">
        <label>第二行</label>
        <input v-model="line2" type="text" />
      </div>
      <div class="form-group">
        <label>第三行</label>
        <input v-model="line3" type="text" />
      </div>

      <details class="tool-section">
        <summary>画布</summary>
        <div class="grid">
          <div class="form-group">
            <label>宽度</label>
            <input v-model.number="width" type="number" min="320" max="2400" />
          </div>
          <div class="form-group">
            <label>高度</label>
            <input v-model.number="height" type="number" min="400" max="3000" />
          </div>
        </div>
      </details>

      <details class="tool-section">
        <summary>颜色</summary>
        <div class="grid">
          <div class="form-group">
            <label>背景</label>
            <input v-model="bg" type="text" />
          </div>
          <div class="form-group">
            <label>文字</label>
            <input v-model="textColor" type="text" />
          </div>
          <div class="form-group">
            <label>图形</label>
            <input v-model="shapeColor" type="text" />
          </div>
        </div>
      </details>

      <details class="tool-section">
        <summary>排版</summary>
        <div class="form-group">
          <label>字号 {{ titleSize }}</label>
          <input v-model.number="titleSize" type="range" min="40" max="140" step="1" />
        </div>
        <div class="form-group">
          <label>行距 {{ lineGap }}</label>
          <input v-model.number="lineGap" type="range" min="0" max="80" step="1" />
        </div>
        <div class="form-group">
          <label>文字位置 {{ Math.round(topOffset * 100) }}%</label>
          <input v-model.number="topOffset" type="range" min="0.2" max="0.75" step="0.01" />
        </div>
      </details>

      <details class="tool-section">
        <summary>几何</summary>
        <div class="form-group form-switch">
          <label>显示横线 + 圆</label>
          <input v-model="showGeometry" type="checkbox" />
        </div>
        <div class="form-group">
          <label>圆大小 {{ circleSize }}</label>
          <input v-model.number="circleSize" type="range" min="60" max="280" step="1" />
        </div>
        <div class="form-group">
          <label>横线粗细 {{ lineThickness }}</label>
          <input v-model.number="lineThickness" type="range" min="1" max="16" step="1" />
        </div>
        <div class="form-group">
          <label>位置 {{ Math.round(lineY * 100) }}%</label>
          <input v-model.number="lineY" type="range" min="0.55" max="0.92" step="0.01" />
        </div>
      </details>

      <div class="preview-wrap">
        <canvas ref="canvasRef" class="preview-canvas" />
      </div>

      <div class="actions">
        <button type="button" @click="draw">重绘</button>
        <button type="button" @click="exportPng">导出 PNG</button>
        <button type="button" @click="resetDefault">默认</button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

const DEFAULT_LINES = ['它不会理解，', '它只在预测，', '可我们却问它意义。']

const open = ref(false)
const line1 = ref(DEFAULT_LINES[0])
const line2 = ref(DEFAULT_LINES[1])
const line3 = ref(DEFAULT_LINES[2])

const width = ref(1080)
const height = ref(1350)
const bg = ref('#F5F3EF')
const textColor = ref('#111111')
const shapeColor = ref('#111111')
const fontFamily = ref('"Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", serif')
const titleSize = ref(88)
const lineGap = ref(26)
const topOffset = ref(0.5)
const showGeometry = ref(false)
const circleSize = ref(160)
const lineThickness = ref(6)
const lineY = ref(0.78)

const canvasRef = ref<HTMLCanvasElement | null>(null)
const lines = computed(() => [line1.value, line2.value, line3.value].map((s) => (s || '').trimEnd()))

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n))
}

function normalizeNumberState() {
  width.value = clamp(Number(width.value) || 1080, 320, 2400)
  height.value = clamp(Number(height.value) || 1350, 400, 3000)
  titleSize.value = clamp(Number(titleSize.value) || 88, 40, 140)
  lineGap.value = clamp(Number(lineGap.value) || 26, 0, 80)
  topOffset.value = clamp(Number(topOffset.value) || 0.5, 0.2, 0.75)
  circleSize.value = clamp(Number(circleSize.value) || 160, 60, 280)
  lineThickness.value = clamp(Number(lineThickness.value) || 6, 1, 16)
  lineY.value = clamp(Number(lineY.value) || 0.78, 0.55, 0.92)
}

function draw() {
  normalizeNumberState()
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = width.value
  canvas.height = height.value

  ctx.fillStyle = bg.value
  ctx.fillRect(0, 0, width.value, height.value)

  ctx.fillStyle = textColor.value
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  const scale = width.value / 1080
  const fontSize = Math.round(titleSize.value * scale)
  const gap = Math.round(lineGap.value * scale)
  ctx.font = `600 ${fontSize}px ${fontFamily.value}`

  const blockHeight = 3 * fontSize + 2 * gap
  const centerY = Math.round(height.value * topOffset.value)
  const startY = centerY - blockHeight / 2 + fontSize / 2

  for (let i = 0; i < 3; i++) {
    ctx.fillText(lines.value[i] || '', width.value / 2, startY + i * (fontSize + gap))
  }

  if (showGeometry.value) {
    ctx.fillStyle = shapeColor.value
    const yLineAbs = clamp(Math.round(height.value * lineY.value), 0, height.value)
    const thick = Math.max(1, Math.round(lineThickness.value * scale))
    const circle = Math.max(10, Math.round(circleSize.value * scale))
    const radius = circle / 2
    const cx = width.value / 2
    const leftEnd = cx - radius
    const rightStart = cx + radius

    ctx.fillRect(0, yLineAbs - Math.floor(thick / 2), Math.max(0, leftEnd), thick)
    ctx.fillRect(rightStart, yLineAbs - Math.floor(thick / 2), Math.max(0, width.value - rightStart), thick)

    ctx.beginPath()
    ctx.arc(cx, yLineAbs, radius, 0, Math.PI * 2)
    ctx.closePath()
    ctx.fill()
  }
}

function exportPng() {
  const canvas = canvasRef.value
  if (!canvas) return
  draw()

  try {
    const dataUrl = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = `three-line-poem_${width.value}x${height.value}.png`
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }))
    a.remove()
    return
  } catch (err) {
    console.warn('toDataURL download failed, fallback to blob', err)
  }

  if (canvas.toBlob) {
    canvas.toBlob((blob) => {
      if (!blob) return
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `three-line-poem_${width.value}x${height.value}.png`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    }, 'image/png')
  }
}

function resetDefault() {
  line1.value = DEFAULT_LINES[0]
  line2.value = DEFAULT_LINES[1]
  line3.value = DEFAULT_LINES[2]
  width.value = 1080
  height.value = 1350
  bg.value = '#F5F3EF'
  textColor.value = '#111111'
  shapeColor.value = '#111111'
  titleSize.value = 88
  lineGap.value = 26
  topOffset.value = 0.5
  showGeometry.value = false
  circleSize.value = 160
  lineThickness.value = 6
  lineY.value = 0.78
}

watch(
  [
    line1,
    line2,
    line3,
    width,
    height,
    bg,
    textColor,
    shapeColor,
    fontFamily,
    titleSize,
    lineGap,
    topOffset,
    showGeometry,
    circleSize,
    lineThickness,
    lineY
  ],
  () => draw()
)

onMounted(() => {
  draw()
})
</script>

<style scoped>
.poem-tool {
  margin-top: 14px;
  border-top: 1px solid var(--border-color);
  padding-top: 14px;
}

.tool-toggle {
  width: 100%;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: #fff;
  color: var(--text-main);
  cursor: pointer;
  padding: 8px 10px;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.tool-body {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-section {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: #fff;
  padding: 8px 10px;
}

.tool-section summary {
  font-size: 12px;
  color: var(--text-sub);
  cursor: pointer;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}

.form-group label {
  font-size: 12px;
  color: var(--text-sub);
}

.form-switch {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}

.form-group input[type='text'],
.form-group input[type='number'] {
  height: 32px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 0 8px;
  font-size: 12px;
}

.form-group input[type='range'] {
  width: 100%;
}

.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
}

.preview-wrap {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  background: #fff;
  padding: 8px;
}

.preview-canvas {
  width: 100%;
  height: auto;
  display: block;
}

.actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.actions button {
  height: 30px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: #fff;
  font-size: 12px;
  cursor: pointer;
}

.actions button:hover {
  border-color: var(--primary);
  color: var(--primary);
}
</style>
