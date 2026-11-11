import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import vm from 'node:vm'
import ts from 'typescript'

const legacy = readFileSync(new URL('../../time-helper/desk/src/theme/ThemeEngine.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(legacy, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
const context = { exports: {}, console, window: { matchMedia: () => ({ matches: false }) } }
vm.runInNewContext(compiled, context)
const definitions = context.exports.getAvailableThemes()
const order = ['light', 'dark', 'system', ...definitions.map(item => item.type).filter(type => !['light', 'dark', 'system'].includes(type))]
const english = {
  light: 'Daylight', dark: 'Midnight', system: 'Follow system', solid: 'Solid', gradient: 'Gradient', glass: 'Glass', neon: 'Neon',
  ink: 'Ink', vintage: 'Vintage', cyberpunk: 'Cyberpunk', pixel: 'Pixel', aurora: 'Aurora', sakura: 'Sakura', ocean: 'Ocean', forest: 'Forest',
  tech: 'Technology', midnight_library: 'Midnight library', star_voyage: 'Star voyage', rainy_city: 'Rainy city', desert_dusk: 'Desert dusk',
  bamboo_dawn: 'Bamboo dawn', nordic_polar_night: 'Polar night', japanese_garden: 'Japanese garden', victorian_study: 'Victorian study', underwater_temple: 'Underwater temple',
}
const entries = order.map((type, index) => {
  const definition = definitions.find(item => item.type === type)
  const style = context.exports.getThemeStyle({ type })
  return {
    id: index + 1, slug: type, version: '1.0.0', author: 'EffiLife',
    name: { 'zh-CN': definition.name, 'en-US': english[type] || type },
    mode: type === 'system' ? 'system' : 'auto',
    palette: { background: style.bgColor, surface: style.cardBg, text: style.textColor, muted: style.textSecondary, accent: style.accentColor },
    decoration: {
      gradient: style.bgGradient || null, particles: style.particles || null,
      renderer: style.renderCanvas ? style.renderCanvas.toString() : null,
      helpers: style.renderCanvas?.toString().includes('drawFlower') ? vm.runInNewContext('drawFlower.toString()', context) : null,
    },
    legacyType: type,
  }
})
const target = new URL('../resources/themes/', import.meta.url)
mkdirSync(target, { recursive: true })
writeFileSync(new URL('catalog.json', target), JSON.stringify(entries, null, 2) + '\n')
console.log(`Migrated ${entries.length} theme definitions and retained their decoration sources`)
