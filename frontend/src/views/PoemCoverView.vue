<template>
  <div class="container poem-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">三行诗封面</h1>
        <p class="page-subtitle">左侧配置参数，右侧实时预览并导出 PNG。</p>
      </div>
    </div>

    <div class="poem-layout">
      <section class="card config-panel">
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

        <details class="section" open>
          <summary>画布尺寸</summary>
          <div class="grid2">
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

        <details class="section">
          <summary>颜色</summary>
          <div class="grid2">
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

        <details class="section">
          <summary>字体</summary>
          <div class="form-group">
            <label>font-family</label>
            <input v-model="fontFamily" type="text" />
          </div>
        </details>

        <details class="section">
          <summary>排版</summary>
          <div class="form-group">
            <label>字体对齐</label>
            <select v-model="textAlignMode">
              <option value="left">左对齐</option>
              <option value="center">居中对齐</option>
              <option value="right">右对齐</option>
            </select>
          </div>
          <div class="form-group">
            <label>标题字号 {{ titleSize }}</label>
            <input v-model.number="titleSize" type="range" min="40" max="140" step="1" />
          </div>
          <div class="form-group">
            <label>行距 {{ lineGap }}</label>
            <input v-model.number="lineGap" type="range" min="0" max="80" step="1" />
          </div>
          <div class="form-group">
            <label>文字垂直位置 {{ Math.round(topOffset * 100) }}%</label>
            <input v-model.number="topOffset" type="range" min="0.2" max="0.75" step="0.01" />
          </div>
        </details>

        <details class="section">
          <summary>几何元素</summary>
          <div class="form-group switch-row">
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
            <label>横线/圆位置 {{ Math.round(lineY * 100) }}%</label>
            <input v-model.number="lineY" type="range" min="0.55" max="0.92" step="0.01" />
          </div>
        </details>

        <div class="action-row">
          <button class="btn btn-secondary" type="button" @click="draw">重绘</button>
          <button class="btn btn-primary" type="button" @click="exportPng">导出 PNG</button>
          <button class="btn btn-secondary" type="button" @click="resetDefault">恢复默认</button>
        </div>
      </section>

      <section class="card preview-panel">
        <h3 class="section-title">预览</h3>
        <div class="preview-wrap">
          <canvas ref="canvasRef" class="preview-canvas" />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

const DEFAULT_LINES = ['它不会理解，', '它只在预测，', '可我们却问它意义。']

const line1 = ref(DEFAULT_LINES[0])
const line2 = ref(DEFAULT_LINES[1])
const line3 = ref(DEFAULT_LINES[2])

const width = ref(1080)
const height = ref(1350)
const bg = ref('#F5F3EF')
const textColor = ref('#111111')
const shapeColor = ref('#111111')
const fontFamily = ref('"Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", serif')
const textAlignMode = ref<'left' | 'center' | 'right'>('left')
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

function normalizeState() {
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
  normalizeState()
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = width.value
  canvas.height = height.value

  ctx.fillStyle = bg.value
  ctx.fillRect(0, 0, width.value, height.value)

  ctx.fillStyle = textColor.value
  ctx.textAlign = textAlignMode.value
  ctx.textBaseline = 'middle'

  const scale = width.value / 1080
  const fontSize = Math.round(titleSize.value * scale)
  const gap = Math.round(lineGap.value * scale)
  ctx.font = `600 ${fontSize}px ${fontFamily.value}`

  const blockHeight = 3 * fontSize + 2 * gap
  const centerY = Math.round(height.value * topOffset.value)
  const startY = centerY - blockHeight / 2 + fontSize / 2
  const horizontalPadding = Math.round(width.value * 0.12)
  const textX =
    textAlignMode.value === 'left'
      ? horizontalPadding
      : textAlignMode.value === 'right'
        ? width.value - horizontalPadding
        : width.value / 2

  for (let i = 0; i < 3; i++) {
    ctx.fillText(lines.value[i] || '', textX, startY + i * (fontSize + gap))
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
  fontFamily.value = '"Noto Serif SC", "Source Han Serif SC", "Songti SC", "STSong", serif'
  textAlignMode.value = 'left'
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
    textAlignMode,
    titleSize,
    lineGap,
    topOffset,
    showGeometry,
    circleSize,
    lineThickness,
    lineY
  ],
  draw
)

onMounted(draw)
</script>

<style scoped>
.poem-page {
  max-width: 1400px;
}

.poem-layout {
  display: grid;
  grid-template-columns: minmax(380px, 480px) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.config-panel {
  position: sticky;
  top: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.section summary {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
  cursor: pointer;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  color: var(--text-sub);
}

.form-group input[type='text'],
.form-group input[type='number'],
.form-group select {
  height: 38px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 0 10px;
  font-size: 14px;
  background: #fff;
}

.form-group input[type='range'] {
  width: 100%;
}

.grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 10px;
}

.switch-row {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.action-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.preview-panel {
  min-height: 560px;
}

.preview-wrap {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.preview-canvas {
  width: 100%;
  height: auto;
  display: block;
}

@media (max-width: 1100px) {
  .poem-layout {
    grid-template-columns: 1fr;
  }

  .config-panel {
    position: static;
  }

  .grid2,
  .action-row {
    grid-template-columns: 1fr;
  }
}
</style>
