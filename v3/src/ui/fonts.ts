import '@fontsource-variable/inter'
import '@fontsource/noto-sans-sc/chinese-simplified-400.css'
import '@fontsource/noto-sans-sc/chinese-simplified-600.css'
import { Registry } from '../extensions/registry'

export interface FontDefinition { id: string; name: string; family: string; license: string; load?: () => Promise<void> }
export const fonts = new Registry<FontDefinition>()
fonts.register({ id: 'default', name: 'Inter · Noto Sans SC', family: '"Inter Variable", "Noto Sans SC", system-ui, sans-serif', license: 'OFL-1.1' })
fonts.register({ id: 'system', name: 'System', family: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', license: 'platform' })

let request = 0
export async function applyFont(id: string): Promise<void> {
  const sequence = ++request
  const font = fonts.get(id) || fonts.get('default')!
  await font.load?.()
  if (sequence === request) document.documentElement.style.setProperty('--font-body', font.family)
}

