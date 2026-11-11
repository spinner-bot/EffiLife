import { execFileSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const project = fileURLToPath(new URL('../../', import.meta.url))
const files = [
  'scripts/sync-frame.mjs',
  'public/extension-frame.js',
  'public/extension-frame.css',
  'public/extension-frame.html',
  'apps/desktop/src-tauri/tauri.conf.json',
]
export function frameFixture(eol: '\n' | '\r\n' | '\r') {
  const cache = resolve(project, '.cache/frame-fixtures')
  mkdirSync(cache, { recursive: true })
  const root = mkdtempSync(resolve(cache, 'checkout-'))
  const read = (name: string) => readFileSync(resolve(root, name), 'utf8')
  const write = (name: string, text: string) => {
    const path = resolve(root, name)
    mkdirSync(dirname(path), { recursive: true })
    writeFileSync(path, text)
  }
  for (const name of files) write(name, readFileSync(resolve(project, name), 'utf8').replace(/\r\n?/g, '\n').replaceAll('\n', eol))
  return {
    read, write,
    run: (...args: string[]) => execFileSync(process.execPath, [resolve(root, 'scripts/sync-frame.mjs'), ...args], { encoding: 'utf8', stdio: 'pipe' }),
    dispose: () => rmSync(root, { recursive: true, force: true }),
  }
}
