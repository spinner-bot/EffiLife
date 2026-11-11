import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'

const root = fileURLToPath(new URL('../', import.meta.url))
export const version = readFileSync(resolve(root, 'VERSION'), 'utf8').trim()
if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error('VERSION must contain a semantic product version')
const packageVersion = JSON.parse(readFileSync(resolve(root, 'package.json'), 'utf8')).version
if (version !== packageVersion) throw new Error('package.json version differs from VERSION')
const nativePath = resolve(root, 'src-tauri/tauri.conf.json')
if (existsSync(nativePath) && JSON.parse(readFileSync(nativePath, 'utf8')).version !== version) {
  throw new Error('Tauri version differs from VERSION')
}
const changes = readFileSync(resolve(root, 'CHANGELOG.md'), 'utf8')
if (!changes.includes('[' + version + ']')) throw new Error('Current product version has no changelog entry')
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log('EffiLife v' + version + ': version and changelog are consistent')
}

