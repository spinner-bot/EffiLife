import { requireCondition } from '../domain/errors'

const properties = new Set([
  'color', 'background-color', 'background-image', 'border-color', 'border-radius',
  'box-shadow', 'text-shadow', 'opacity', 'outline-color', 'text-decoration-color',
  'caret-color', 'accent-color', 'fill', 'stroke',
])
/** Deliberately small L1 visual grammar: no geometry, at-rules or resource URLs. */
export function scopeVisualCss(input: string, id: number): string {
  const source = input.replace(/\/\*[\s\S]*?\*\//g, '')
  requireCondition(!/[\\@<>\u0000-\u0008]/.test(source), 'extensions.unsafeCss')
  let position = 0
  const output: string[] = []
  const blocks = /([^{}]+)\{([^{}]*)\}/g
  for (const match of source.matchAll(blocks)) {
    requireCondition(!source.slice(position, match.index).trim(), 'extensions.unsafeCss')
    const selectors = match[1]!.split(',').map(selector => selector.trim())
    requireCondition(selectors.every(selector => /^[a-zA-Z0-9_.\s>+~:#\[\]="'-]+$/.test(selector) && !selector.includes(':root')), 'extensions.unsafeCss')
    const declarations: string[] = []
    for (const entry of match[2]!.split(';').filter(item => item.trim())) {
      const colon = entry.indexOf(':')
      const property = entry.slice(0, colon).trim().toLowerCase()
      const value = entry.slice(colon + 1).trim()
      requireCondition(colon > 0 && properties.has(property) && value && !/url\s*\(|image-set\s*\(|expression\s*\(|!important|[{}<>]/i.test(value), 'extensions.unsafeCss')
      requireCondition(/^[a-zA-Z0-9#(),.%\s+*/_-]+$/.test(value), 'extensions.unsafeCss')
      for (const fn of value.matchAll(/([\w-]+)\s*\(/g)) requireCondition(['rgb', 'rgba', 'hsl', 'hsla', 'var', 'linear-gradient', 'radial-gradient', 'repeating-linear-gradient'].includes(fn[1]!.toLowerCase()), 'extensions.unsafeCss')
      for (const variable of value.matchAll(/var\(\s*(--[\w-]+)/g)) requireCondition(['--page', '--surface', '--ink', '--muted', '--accent', '--line', '--subtle'].includes(variable[1]!), 'extensions.unsafeCss')
      declarations.push(property + ':' + value)
    }
    output.push(selectors.map(selector => '[data-active-theme="' + id + '"] ' + selector).join(',') + '{' + declarations.join(';') + '}')
    position = match.index + match[0].length
  }
  requireCondition(!source.slice(position).trim(), 'extensions.unsafeCss')
  return output.join('\n')
}

