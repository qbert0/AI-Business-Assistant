const HTML_ESCAPE_LOOKUP: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
}

const CHART_COLORS = ['#1769e0', '#0f9d58', '#f29900', '#d93025', '#7b61ff', '#0b7285']
const SVG_WIDTH = 720
const SVG_HEIGHT = 380

type ChartKind = 'bar' | 'line' | 'pie'
type ChartFormat = 'number' | 'currency_vnd' | 'percent'

type RawChartSpec = {
  type?: unknown
  title?: unknown
  xLabel?: unknown
  yLabel?: unknown
  categories?: unknown
  series?: unknown
  format?: unknown
  note?: unknown
}

type ChartSeries = {
  name: string
  data: number[]
  color: string
}

type ChartSpec = {
  type: ChartKind
  title: string
  xLabel: string
  yLabel: string
  categories: string[]
  series: ChartSeries[]
  format: ChartFormat
  note: string
}

const escapeHtml = (value: string) => value.replace(/[&<>"']/g, (char) => HTML_ESCAPE_LOOKUP[char] || char)

const toText = (value: unknown) => {
  if (typeof value === 'string') {
    return value.trim()
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value)
  }
  return ''
}

const isFiniteNumber = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)

const ellipse = (value: string, limit = 18) => (value.length > limit ? `${value.slice(0, Math.max(0, limit - 1)).trim()}…` : value)

const toChartColor = (value: unknown, index: number) => {
  const raw = typeof value === 'string' ? value.trim() : ''
  if (/^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(raw)) {
    return raw
  }
  return CHART_COLORS[index % CHART_COLORS.length] || '#1769e0'
}

const parseMermaidCategoryList = (value: string) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

const parseMermaidNumericValue = (value: string) => {
  const normalized = value.replace(/_/g, '').replace(/,/g, '').trim()
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

const normalizeMermaidLines = (rawSpec: string) => {
  const lines = rawSpec
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  return lines.filter((line) => !line.startsWith('%%{') && line !== '%%')
}

const parseMermaidBarSpec = (rawSpec: string): RawChartSpec | null => {
  const meaningfulLines = normalizeMermaidLines(rawSpec)
  if (!meaningfulLines.length || meaningfulLines[0]?.toLowerCase() !== 'bar') {
    return null
  }

  let title = 'Bieu do du lieu'
  let xLabel = ''
  let yLabel = ''
  let categories: string[] = []
  const fallbackCategories: string[] = []
  const values: number[] = []

  for (const line of meaningfulLines.slice(1)) {
    const lowerLine = line.toLowerCase()
    if (lowerLine.startsWith('title ')) {
      title = line.slice(6).trim() || title
      continue
    }
    if (lowerLine.startsWith('x-axis ')) {
      categories = parseMermaidCategoryList(line.slice(7))
      continue
    }
    if (lowerLine.startsWith('y-axis ')) {
      yLabel = line.slice(7).trim()
      continue
    }

    const seriesMatch = line.match(/^(.+?)\s+(-?\d+(?:[.,]\d+)?)$/)
    if (!seriesMatch) {
      continue
    }

    const category = seriesMatch[1]?.trim()
    const value = parseMermaidNumericValue(seriesMatch[2] || '')
    if (!category || value === null) {
      continue
    }

    fallbackCategories.push(category)
    values.push(value)
  }

  const finalCategories = categories.length === values.length ? categories : fallbackCategories
  if (!finalCategories.length || finalCategories.length !== values.length) {
    return null
  }

  return {
    type: 'bar',
    title,
    xLabel,
    yLabel,
    categories: finalCategories,
    series: [
      {
        name: yLabel || 'Gia tri',
        data: values,
        color: CHART_COLORS[0]
      }
    ],
    format: /vnđ|vnd|dong|đ/i.test(yLabel) ? 'currency_vnd' : 'number'
  }
}

const parseMermaidPieLabel = (rawLabel: string) => {
  const trimmed = rawLabel.trim()
  if ((trimmed.startsWith('"') && trimmed.endsWith('"')) || (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
    return trimmed.slice(1, -1).trim()
  }
  return trimmed
}

const parseMermaidPieSpec = (rawSpec: string): RawChartSpec | null => {
  const meaningfulLines = normalizeMermaidLines(rawSpec)
  if (!meaningfulLines.length || meaningfulLines[0]?.toLowerCase() !== 'pie') {
    return null
  }

  let title = 'Bieu do tron'
  const categories: string[] = []
  const values: number[] = []

  for (const line of meaningfulLines.slice(1)) {
    const lowerLine = line.toLowerCase()
    if (lowerLine === 'showdata') {
      continue
    }
    if (lowerLine.startsWith('title ')) {
      title = line.slice(6).trim() || title
      continue
    }

    const sliceMatch = line.match(/^(.+?)\s*:\s*(-?\d+(?:[.,]\d+)?)$/)
    if (!sliceMatch) {
      continue
    }

    const label = parseMermaidPieLabel(sliceMatch[1] || '')
    const value = parseMermaidNumericValue(sliceMatch[2] || '')
    if (!label || value === null) {
      continue
    }

    categories.push(label)
    values.push(value)
  }

  if (!categories.length || categories.length !== values.length) {
    return null
  }

  return {
    type: 'pie',
    title,
    categories,
    series: [
      {
        name: title,
        data: values,
        color: CHART_COLORS[0]
      }
    ],
    format: 'number'
  }
}

const parseMermaidAxisCategories = (rawValue: string) => {
  const bracketMatch = rawValue.match(/^\[(.*)\]$/)
  if (bracketMatch) {
    return parseMermaidCategoryList(bracketMatch[1] ?? '')
  }

  return parseMermaidCategoryList(rawValue)
}

const parseMermaidSeriesData = (rawValue: string) => {
  const bracketMatch = rawValue.match(/^\[(.*)\]$/)
  if (!bracketMatch) {
    return []
  }

  return (bracketMatch[1] ?? '')
    .split(',')
    .map((item) => parseMermaidNumericValue(item))
    .filter((item): item is number => item !== null)
}

const parseMermaidXyChartSpec = (rawSpec: string): RawChartSpec | null => {
  const meaningfulLines = normalizeMermaidLines(rawSpec)
  if (!meaningfulLines.length) {
    return null
  }

  const firstLine = meaningfulLines[0]?.toLowerCase()
  if (firstLine !== 'xychart' && firstLine !== 'xychart-beta') {
    return null
  }

  let title = 'Bieu do du lieu'
  let xLabel = ''
  let yLabel = ''
  let categories: string[] = []
  let minY: number | null = null
  let maxY: number | null = null
  const series: Array<{ name: string, data: number[], color?: string }> = []

  for (const line of meaningfulLines.slice(1)) {
    const lowerLine = line.toLowerCase()
    if (lowerLine.startsWith('title ')) {
      title = line.slice(6).trim() || title
      continue
    }
    if (lowerLine.startsWith('x-axis ')) {
      categories = parseMermaidAxisCategories(line.slice(7).trim())
      continue
    }
    if (lowerLine.startsWith('y-axis ')) {
      const axisBody = line.slice(7).trim()
      const rangeMatch = axisBody.match(/^(.*?)\s+(-?\d+(?:[.,]\d+)?)\s*-->\s*(-?\d+(?:[.,]\d+)?)$/)
      if (rangeMatch) {
        yLabel = rangeMatch[1]?.trim() ?? ''
        minY = parseMermaidNumericValue(rangeMatch[2] || '')
        maxY = parseMermaidNumericValue(rangeMatch[3] || '')
      } else {
        yLabel = axisBody
      }
      continue
    }

    const seriesMatch = line.match(/^(bar|line)\s+(?:\"([^\"]+)\"|'([^']+)'|([^\[]+?))?\s*\[(.*)\]$/i)
    if (!seriesMatch) {
      continue
    }

    const seriesType = (seriesMatch[1] || '').toLowerCase()
    const seriesName = (seriesMatch[2] || seriesMatch[3] || seriesMatch[4] || seriesType).trim()
    const data = parseMermaidSeriesData(`[${seriesMatch[5] || ''}]`)
    if (!data.length) {
      continue
    }

    series.push({
      name: seriesName,
      data,
      color: seriesType === 'line' ? (CHART_COLORS[1] ?? '#0f9d58') : (CHART_COLORS[0] ?? '#1769e0')
    })
  }

  if (!series.length) {
    return null
  }

  const longestSeriesLength = Math.max(...series.map((item) => item.data.length))
  const finalCategories = categories.length === longestSeriesLength
    ? categories
    : Array.from({ length: longestSeriesLength }, (_item, index) => `Muc ${index + 1}`)

  const chartType: ChartKind = series.some((item) => item.color === CHART_COLORS[1]) ? 'line' : 'bar'
  const note = (minY !== null && maxY !== null) ? `Khoang truc Y de xuat: ${minY} -> ${maxY}` : ''

  if (!finalCategories.length) {
    return null
  }

  return {
    type: chartType,
    title,
    xLabel,
    yLabel,
    categories: finalCategories,
    series: series.map((item) => ({
      name: item.name,
      data: item.data.slice(0, finalCategories.length),
      color: item.color || CHART_COLORS[0]
    })),
    format: /vnđ|vnd|dong|đ/i.test(yLabel) ? 'currency_vnd' : 'number',
    note
  }
}

const formatFullValue = (value: number, format: ChartFormat) => {
  if (format === 'percent') {
    return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(value)}%`
  }

  const formatted = new Intl.NumberFormat('vi-VN', {
    maximumFractionDigits: Math.abs(value) < 100 ? 2 : 0
  }).format(value)

  if (format === 'currency_vnd') {
    return `${formatted} VNĐ`
  }

  return formatted
}

const formatShortValue = (value: number, format: ChartFormat) => {
  if (format === 'percent') {
    return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(value)}%`
  }

  const absValue = Math.abs(value)
  let scaled = value
  let suffix = ''

  if (absValue >= 1_000_000_000) {
    scaled = value / 1_000_000_000
    suffix = 'B'
  } else if (absValue >= 1_000_000) {
    scaled = value / 1_000_000
    suffix = 'M'
  } else if (absValue >= 1_000) {
    scaled = value / 1_000
    suffix = 'K'
  }

  const formatted = new Intl.NumberFormat('vi-VN', {
    maximumFractionDigits: suffix ? 1 : 0
  }).format(scaled)

  return format === 'currency_vnd' && suffix ? `${formatted}${suffix}` : `${formatted}${suffix}`
}

const buildTickValues = (minValue: number, maxValue: number, steps = 4) => {
  const range = maxValue - minValue || 1
  return Array.from({ length: steps + 1 }, (_item, index) => maxValue - ((range / steps) * index))
}

const valueToY = (value: number, minValue: number, maxValue: number, chartTop: number, chartHeight: number) => {
  const range = maxValue - minValue || 1
  const normalized = (value - minValue) / range
  return chartTop + ((1 - normalized) * chartHeight)
}

const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0
  return {
    x: centerX + (radius * Math.cos(angleInRadians)),
    y: centerY + (radius * Math.sin(angleInRadians))
  }
}

const describeArc = (centerX: number, centerY: number, radius: number, startAngle: number, endAngle: number) => {
  const start = polarToCartesian(centerX, centerY, radius, endAngle)
  const end = polarToCartesian(centerX, centerY, radius, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1'

  return [
    'M', centerX, centerY,
    'L', start.x, start.y,
    'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y,
    'Z'
  ].join(' ')
}

const renderLegend = (items: Array<{ color: string, label: string, value?: string }>) => {
  if (!items.length) {
    return ''
  }

  return `
    <div class="chat-chart__legend">
      ${items.map((item) => (
        `<div class="chat-chart__legend-item">
          <span class="chat-chart__legend-swatch" style="background:${escapeHtml(item.color)}"></span>
          <span class="chat-chart__legend-label">${escapeHtml(item.label)}</span>
          ${item.value ? `<span class="chat-chart__legend-value">${escapeHtml(item.value)}</span>` : ''}
        </div>`
      )).join('')}
    </div>
  `
}

const renderMeta = (spec: ChartSpec) => {
  const meta: string[] = []
  if (spec.xLabel) {
    meta.push(`<span><strong>Truc X:</strong> ${escapeHtml(spec.xLabel)}</span>`)
  }
  if (spec.yLabel) {
    meta.push(`<span><strong>Truc Y:</strong> ${escapeHtml(spec.yLabel)}</span>`)
  }
  if (!meta.length && !spec.note) {
    return ''
  }

  return `
    <div class="chat-chart__footer">
      ${meta.length ? `<div class="chat-chart__meta">${meta.join('')}</div>` : ''}
      ${spec.note ? `<p class="chat-chart__note">${escapeHtml(spec.note)}</p>` : ''}
    </div>
  `
}

const normalizeChartSpec = (rawSpec: RawChartSpec): ChartSpec | null => {
  const rawType = toText(rawSpec.type).toLowerCase()
  if (!['bar', 'line', 'pie'].includes(rawType)) {
    return null
  }

  const rawCategories = Array.isArray(rawSpec.categories) ? rawSpec.categories.map((item) => toText(item)).filter(Boolean) : []
  const rawSeries = Array.isArray(rawSpec.series) ? rawSpec.series : []
  if (!rawSeries.length) {
    return null
  }

  const categories = rawCategories.slice(0, 8)
  const normalizedSeries = rawSeries
    .map((item, index) => {
      const payload = item && typeof item === 'object' ? item as { name?: unknown, data?: unknown, color?: unknown } : null
      const rawData = Array.isArray(payload?.data) ? payload?.data : []
      const data = rawData.filter(isFiniteNumber).slice(0, 8)
      if (!data.length) {
        return null
      }

      return {
        name: toText(payload?.name) || `Series ${index + 1}`,
        data,
        color: toChartColor(payload?.color, index)
      } satisfies ChartSeries
    })
    .filter((item): item is ChartSeries => Boolean(item))
    .slice(0, rawType === 'pie' ? 1 : 2)

  if (!normalizedSeries.length) {
    return null
  }

  const longestSeriesLength = Math.max(...normalizedSeries.map((item) => item.data.length))
  const fallbackCategories = Array.from({ length: longestSeriesLength }, (_item, index) => `Muc ${index + 1}`)
  const finalCategories = (categories.length ? categories : fallbackCategories).slice(0, longestSeriesLength)

  if (rawType !== 'pie' && finalCategories.length < 2) {
    return null
  }

  if (rawType === 'pie' && finalCategories.length !== normalizedSeries[0]?.data.length) {
    return null
  }

  const rawFormat = toText(rawSpec.format)
  const format: ChartFormat = ['currency_vnd', 'percent', 'number'].includes(rawFormat) ? rawFormat as ChartFormat : 'number'

  return {
    type: rawType as ChartKind,
    title: toText(rawSpec.title) || 'Bieu do du lieu',
    xLabel: toText(rawSpec.xLabel),
    yLabel: toText(rawSpec.yLabel),
    categories: finalCategories,
    series: normalizedSeries.map((series) => ({
      ...series,
      data: series.data.slice(0, finalCategories.length)
    })),
    format,
    note: toText(rawSpec.note)
  }
}

const renderBarChart = (spec: ChartSpec) => {
  const margin = { top: 28, right: 24, bottom: 76, left: 72 }
  const chartWidth = SVG_WIDTH - margin.left - margin.right
  const chartHeight = SVG_HEIGHT - margin.top - margin.bottom
  const chartLeft = margin.left
  const chartTop = margin.top
  const chartBottom = chartTop + chartHeight
  const flatValues = spec.series.flatMap((item) => item.data)
  const minValue = Math.min(0, ...flatValues)
  const maxValue = Math.max(0, ...flatValues, 1)
  const zeroLineY = valueToY(0, minValue, maxValue, chartTop, chartHeight)
  const tickValues = buildTickValues(minValue, maxValue)
  const groupWidth = chartWidth / spec.categories.length
  const seriesGap = spec.series.length > 1 ? 6 : 0
  const innerWidth = Math.max(22, groupWidth - 20)
  const barWidth = Math.max(12, Math.min(42, (innerWidth - (seriesGap * (spec.series.length - 1))) / spec.series.length))

  const gridHtml = tickValues.map((tick) => {
    const y = valueToY(tick, minValue, maxValue, chartTop, chartHeight)
    return `
      <line x1="${chartLeft}" y1="${y}" x2="${chartLeft + chartWidth}" y2="${y}" class="chat-chart__grid" />
      <text x="${chartLeft - 12}" y="${y + 4}" class="chat-chart__tick" text-anchor="end">${escapeHtml(formatShortValue(tick, spec.format))}</text>
    `
  }).join('')

  const barsHtml = spec.categories.map((label, categoryIndex) => {
    const groupX = chartLeft + (categoryIndex * groupWidth)
    const totalBarsWidth = (spec.series.length * barWidth) + ((spec.series.length - 1) * seriesGap)
    const startX = groupX + ((groupWidth - totalBarsWidth) / 2)

    const seriesBars = spec.series.map((series, seriesIndex) => {
      const value = series.data[categoryIndex] || 0
      const x = startX + (seriesIndex * (barWidth + seriesGap))
      const y = value >= 0 ? valueToY(value, minValue, maxValue, chartTop, chartHeight) : zeroLineY
      const height = Math.max(2, Math.abs(valueToY(value, minValue, maxValue, chartTop, chartHeight) - zeroLineY))

      return `
        <rect x="${x}" y="${y}" width="${barWidth}" height="${height}" rx="6" fill="${escapeHtml(series.color)}">
          <title>${escapeHtml(`${series.name} - ${label}: ${formatFullValue(value, spec.format)}`)}</title>
        </rect>
      `
    }).join('')

    return `
      ${seriesBars}
      <text x="${groupX + (groupWidth / 2)}" y="${chartBottom + 22}" class="chat-chart__label" text-anchor="middle">${escapeHtml(ellipse(label))}</text>
    `
  }).join('')

  return `
    <div class="chat-chart">
      <div class="chat-chart__header">
        <h4 class="chat-chart__title">${escapeHtml(spec.title)}</h4>
      </div>
      <div class="chat-chart__body">
        <svg class="chat-chart__svg" viewBox="0 0 ${SVG_WIDTH} ${SVG_HEIGHT}" role="img" aria-label="${escapeHtml(spec.title)}">
          ${gridHtml}
          <line x1="${chartLeft}" y1="${zeroLineY}" x2="${chartLeft + chartWidth}" y2="${zeroLineY}" class="chat-chart__axis" />
          <line x1="${chartLeft}" y1="${chartTop}" x2="${chartLeft}" y2="${chartBottom}" class="chat-chart__axis" />
          ${barsHtml}
        </svg>
      </div>
      ${spec.series.length > 1 ? renderLegend(spec.series.map((item) => ({ color: item.color, label: item.name }))) : ''}
      ${renderMeta(spec)}
    </div>
  `
}

const renderLineChart = (spec: ChartSpec) => {
  const margin = { top: 28, right: 24, bottom: 76, left: 72 }
  const chartWidth = SVG_WIDTH - margin.left - margin.right
  const chartHeight = SVG_HEIGHT - margin.top - margin.bottom
  const chartLeft = margin.left
  const chartTop = margin.top
  const chartBottom = chartTop + chartHeight
  const flatValues = spec.series.flatMap((item) => item.data)
  const minValue = Math.min(0, ...flatValues)
  const maxValue = Math.max(...flatValues, 1)
  const tickValues = buildTickValues(minValue, maxValue)
  const stepX = spec.categories.length > 1 ? chartWidth / (spec.categories.length - 1) : chartWidth

  const gridHtml = tickValues.map((tick) => {
    const y = valueToY(tick, minValue, maxValue, chartTop, chartHeight)
    return `
      <line x1="${chartLeft}" y1="${y}" x2="${chartLeft + chartWidth}" y2="${y}" class="chat-chart__grid" />
      <text x="${chartLeft - 12}" y="${y + 4}" class="chat-chart__tick" text-anchor="end">${escapeHtml(formatShortValue(tick, spec.format))}</text>
    `
  }).join('')

  const seriesHtml = spec.series.map((series) => {
    const points = series.data.map((value, index) => {
      const x = chartLeft + (index * stepX)
      const y = valueToY(value, minValue, maxValue, chartTop, chartHeight)
      return { x, y, value, label: spec.categories[index] || '' }
    })

    const polyline = points.map((point) => `${point.x},${point.y}`).join(' ')
    const circles = points.map((point) => `
      <circle cx="${point.x}" cy="${point.y}" r="4.5" fill="${escapeHtml(series.color)}">
        <title>${escapeHtml(`${series.name} - ${point.label}: ${formatFullValue(point.value, spec.format)}`)}</title>
      </circle>
    `).join('')

    return `
      <polyline points="${polyline}" fill="none" stroke="${escapeHtml(series.color)}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
      ${circles}
    `
  }).join('')

  const xLabels = spec.categories.map((label, index) => `
    <text x="${chartLeft + (index * stepX)}" y="${chartBottom + 22}" class="chat-chart__label" text-anchor="middle">${escapeHtml(ellipse(label))}</text>
  `).join('')

  return `
    <div class="chat-chart">
      <div class="chat-chart__header">
        <h4 class="chat-chart__title">${escapeHtml(spec.title)}</h4>
      </div>
      <div class="chat-chart__body">
        <svg class="chat-chart__svg" viewBox="0 0 ${SVG_WIDTH} ${SVG_HEIGHT}" role="img" aria-label="${escapeHtml(spec.title)}">
          ${gridHtml}
          <line x1="${chartLeft}" y1="${chartBottom}" x2="${chartLeft + chartWidth}" y2="${chartBottom}" class="chat-chart__axis" />
          <line x1="${chartLeft}" y1="${chartTop}" x2="${chartLeft}" y2="${chartBottom}" class="chat-chart__axis" />
          ${seriesHtml}
          ${xLabels}
        </svg>
      </div>
      ${renderLegend(spec.series.map((item) => ({ color: item.color, label: item.name })))}
      ${renderMeta(spec)}
    </div>
  `
}

const renderPieChart = (spec: ChartSpec) => {
  const values = spec.series[0]?.data || []
  const categories = spec.categories.slice(0, values.length)
  const total = values.reduce((sum, value) => sum + Math.max(0, value), 0)
  if (!total) {
    return null
  }

  const centerX = 360
  const centerY = 168
  const radius = 112
  let currentAngle = 0

  const slicesHtml = values.map((value, index) => {
    const sliceValue = Math.max(0, value)
    const sliceAngle = (sliceValue / total) * 360
    const startAngle = currentAngle
    const endAngle = currentAngle + sliceAngle
    currentAngle = endAngle

    const shape = sliceAngle >= 359.99
      ? `<circle cx="${centerX}" cy="${centerY}" r="${radius}" fill="${escapeHtml(CHART_COLORS[index % CHART_COLORS.length] || '#1769e0')}"></circle>`
      : `<path d="${describeArc(centerX, centerY, radius, startAngle, endAngle)}" fill="${escapeHtml(CHART_COLORS[index % CHART_COLORS.length] || '#1769e0')}"></path>`

    return `
      <g>
        <title>${escapeHtml(`${categories[index] || `Muc ${index + 1}`}: ${formatFullValue(value, spec.format)}`)}</title>
        ${shape}
      </g>
    `
  }).join('')

  const legend = renderLegend(
    values.map((value, index) => ({
      color: CHART_COLORS[index % CHART_COLORS.length] || '#1769e0',
      label: categories[index] || `Muc ${index + 1}`,
      value: formatFullValue(value, spec.format)
    }))
  )

  return `
    <div class="chat-chart">
      <div class="chat-chart__header">
        <h4 class="chat-chart__title">${escapeHtml(spec.title)}</h4>
      </div>
      <div class="chat-chart__body">
        <svg class="chat-chart__svg" viewBox="0 0 ${SVG_WIDTH} ${SVG_HEIGHT}" role="img" aria-label="${escapeHtml(spec.title)}">
          ${slicesHtml}
          <circle cx="${centerX}" cy="${centerY}" r="${radius * 0.48}" fill="#ffffff"></circle>
          <text x="${centerX}" y="${centerY - 4}" class="chat-chart__center-label" text-anchor="middle">Tong</text>
          <text x="${centerX}" y="${centerY + 20}" class="chat-chart__center-value" text-anchor="middle">${escapeHtml(formatShortValue(total, spec.format))}</text>
        </svg>
      </div>
      ${legend}
      ${renderMeta(spec)}
    </div>
  `
}

export const renderChartSpecToHtml = (rawSpec: string) => {
  try {
    const parsed = (
      parseMermaidBarSpec(rawSpec)
      || parseMermaidPieSpec(rawSpec)
      || parseMermaidXyChartSpec(rawSpec)
      || JSON.parse(rawSpec)
    ) as RawChartSpec
    const spec = normalizeChartSpec(parsed)
    if (!spec) {
      return null
    }

    if (spec.type === 'bar') {
      return renderBarChart(spec)
    }
    if (spec.type === 'line') {
      return renderLineChart(spec)
    }
    return renderPieChart(spec)
  } catch {
    return null
  }
}
