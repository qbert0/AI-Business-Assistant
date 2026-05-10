import { renderChartSpecToHtml } from '@/utils/chat/render-chart'

const HTML_ESCAPE_LOOKUP: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
}

const TABLE_DIVIDER_PATTERN = /^\s*\|?(?:\s*:?-{3,}:?\s*\|)+(?:\s*:?-{3,}:\s*)?\|?\s*$/
const UNORDERED_LIST_PATTERN = /^\s*[-*+]\s+/
const ORDERED_LIST_PATTERN = /^\s*\d+\.\s+/
const BLOCKQUOTE_PATTERN = /^\s*>\s?/
const HEADING_PATTERN = /^\s*(#{1,6})\s+(.*)$/
const CODE_FENCE_PATTERN = /^\s*```/
const HORIZONTAL_RULE_PATTERN = /^\s{0,3}([-*_])(?:\s*\1){2,}\s*$/

const escapeHtml = (value: string) => value.replace(/[&<>"']/g, (char) => HTML_ESCAPE_LOOKUP[char] || char)

const normalizeMarkdown = (value: string) => value.replace(/\r\n?/g, '\n').trim()

const createPlaceholderStore = () => {
  const store = new Map<string, string>()

  return {
    add(html: string) {
      const token = `@@CHATMD${store.size}@@`
      store.set(token, html)
      return token
    },
    restore(value: string) {
      let restored = value
      for (const [token, html] of store.entries()) {
        restored = restored.replaceAll(token, html)
      }
      return restored
    }
  }
}

const toSafeUrl = (rawUrl: string) => {
  const trimmed = rawUrl.trim()
  if (!trimmed) {
    return null
  }

  if (/^(https?:\/\/|mailto:|\/)/i.test(trimmed)) {
    return escapeHtml(trimmed)
  }

  return null
}

const parseInlineMarkdown = (rawText: string) => {
  if (!rawText) {
    return ''
  }

  const placeholders = createPlaceholderStore()
  let value = rawText

  value = value.replace(/`([^`\n]+)`/g, (_match, code: string) => placeholders.add(`<code>${escapeHtml(code)}</code>`))
  value = escapeHtml(value)

  value = value.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_match, altText: string, url: string) => {
    const safeUrl = toSafeUrl(url)
    if (!safeUrl) {
      return _match
    }

    return placeholders.add(
      `<img src="${safeUrl}" alt="${altText}" loading="lazy" />`
    )
  })

  value = value.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match, label: string, url: string) => {
    const safeUrl = toSafeUrl(url)
    if (!safeUrl) {
      return _match
    }

    return placeholders.add(
      `<a href="${safeUrl}" target="_blank" rel="noreferrer">${label}</a>`
    )
  })

  value = value.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  value = value.replace(/__([^_]+)__/g, '<strong>$1</strong>')
  value = value.replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
  value = value.replace(/_([^_\n]+)_/g, '<em>$1</em>')
  value = value.replace(/~~([^~]+)~~/g, '<del>$1</del>')

  return placeholders.restore(value)
}

const parseTableRow = (line: string) =>
  line
    .trim()
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cell.trim())

const parseTableAlignments = (dividerLine: string) =>
  parseTableRow(dividerLine).map((cell) => {
    const trimmed = cell.trim()
    if (trimmed.startsWith(':') && trimmed.endsWith(':')) {
      return 'center'
    }
    if (trimmed.endsWith(':')) {
      return 'right'
    }
    return 'left'
  })

const renderParagraph = (lines: string[]) => {
  const content = lines.join('\n').trim()
  if (!content) {
    return ''
  }

  return `<p>${parseInlineMarkdown(content).replace(/\n/g, '<br />')}</p>`
}

const isTableStart = (lines: string[], index: number) =>
  Boolean(lines[index]?.includes('|') && TABLE_DIVIDER_PATTERN.test(lines[index + 1] || ''))

const isBlockStart = (lines: string[], index: number) => {
  const line = lines[index] || ''

  if (!line.trim()) {
    return true
  }

  return (
    HEADING_PATTERN.test(line)
    || CODE_FENCE_PATTERN.test(line)
    || HORIZONTAL_RULE_PATTERN.test(line)
    || UNORDERED_LIST_PATTERN.test(line)
    || ORDERED_LIST_PATTERN.test(line)
    || BLOCKQUOTE_PATTERN.test(line)
    || isTableStart(lines, index)
  )
}

export const renderMarkdownToHtml = (markdown: string) => {
  const normalized = normalizeMarkdown(markdown || '')
  if (!normalized) {
    return ''
  }

  const lines = normalized.split('\n')
  const htmlParts: string[] = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index] || ''

    if (!line.trim()) {
      index += 1
      continue
    }

    const headingMatch = line.match(HEADING_PATTERN)
    if (headingMatch) {
      const level = Math.min(6, headingMatch[1]?.length || 1)
      const text = parseInlineMarkdown(headingMatch[2]?.trim() || '')
      htmlParts.push(`<h${level}>${text}</h${level}>`)
      index += 1
      continue
    }

    if (HORIZONTAL_RULE_PATTERN.test(line)) {
      htmlParts.push('<hr />')
      index += 1
      continue
    }

    if (CODE_FENCE_PATTERN.test(line)) {
      const language = (line.trim().slice(3).trim() || '').replace(/[^a-zA-Z0-9_-]/g, '')
      index += 1
      const codeLines: string[] = []

      while (index < lines.length && !CODE_FENCE_PATTERN.test(lines[index] || '')) {
        codeLines.push(lines[index] || '')
        index += 1
      }

      if (index < lines.length && CODE_FENCE_PATTERN.test(lines[index] || '')) {
        index += 1
      }

      if (language === 'chart') {
        const chartHtml = renderChartSpecToHtml(codeLines.join('\n'))
        if (chartHtml) {
          htmlParts.push(chartHtml)
          continue
        }
      }

      const className = language ? ` class="language-${language}"` : ''
      htmlParts.push(`<pre><code${className}>${escapeHtml(codeLines.join('\n'))}</code></pre>`)
      continue
    }

    if (isTableStart(lines, index)) {
      const headerCells = parseTableRow(lines[index] || '')
      const alignments = parseTableAlignments(lines[index + 1] || '')
      index += 2

      const bodyRows: string[][] = []
      while (index < lines.length && (lines[index] || '').includes('|') && lines[index]?.trim()) {
        bodyRows.push(parseTableRow(lines[index] || ''))
        index += 1
      }

      const headerHtml = headerCells
        .map((cell, cellIndex) => `<th style="text-align:${alignments[cellIndex] || 'left'}">${parseInlineMarkdown(cell)}</th>`)
        .join('')
      const bodyHtml = bodyRows
        .map((row) => (
          `<tr>${row.map((cell, cellIndex) => `<td style="text-align:${alignments[cellIndex] || 'left'}">${parseInlineMarkdown(cell)}</td>`).join('')}</tr>`
        ))
        .join('')

      htmlParts.push(
        `<div class="chat-markdown-table"><table><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`
      )
      continue
    }

    if (UNORDERED_LIST_PATTERN.test(line)) {
      const items: string[] = []

      while (index < lines.length && UNORDERED_LIST_PATTERN.test(lines[index] || '')) {
        items.push((lines[index] || '').replace(UNORDERED_LIST_PATTERN, ''))
        index += 1
      }

      htmlParts.push(`<ul>${items.map((item) => `<li>${parseInlineMarkdown(item)}</li>`).join('')}</ul>`)
      continue
    }

    if (ORDERED_LIST_PATTERN.test(line)) {
      const items: string[] = []

      while (index < lines.length && ORDERED_LIST_PATTERN.test(lines[index] || '')) {
        items.push((lines[index] || '').replace(ORDERED_LIST_PATTERN, ''))
        index += 1
      }

      htmlParts.push(`<ol>${items.map((item) => `<li>${parseInlineMarkdown(item)}</li>`).join('')}</ol>`)
      continue
    }

    if (BLOCKQUOTE_PATTERN.test(line)) {
      const quoteLines: string[] = []

      while (index < lines.length && BLOCKQUOTE_PATTERN.test(lines[index] || '')) {
        quoteLines.push((lines[index] || '').replace(BLOCKQUOTE_PATTERN, ''))
        index += 1
      }

      htmlParts.push(`<blockquote>${renderMarkdownToHtml(quoteLines.join('\n'))}</blockquote>`)
      continue
    }

    const paragraphLines: string[] = []
    while (index < lines.length && lines[index]?.trim() && !isBlockStart(lines, index)) {
      paragraphLines.push(lines[index] || '')
      index += 1
    }

    const paragraphHtml = renderParagraph(paragraphLines)
    if (paragraphHtml) {
      htmlParts.push(paragraphHtml)
    }
  }

  return htmlParts.join('')
}
