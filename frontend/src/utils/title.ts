export const MAX_TITLE_LENGTH = 20

export function truncateTitle(title: string, maxLength: number = MAX_TITLE_LENGTH): string {
  const normalized = (title || '').trim()
  if (!normalized) return ''
  const chars = Array.from(normalized)
  if (chars.length <= maxLength) return normalized
  return chars.slice(0, maxLength).join('')
}

export function truncateTitles(titles: string[], maxLength: number = MAX_TITLE_LENGTH): string[] {
  if (!Array.isArray(titles)) return []
  return titles
    .map(t => truncateTitle(String(t || ''), maxLength))
    .filter(t => !!t)
}
