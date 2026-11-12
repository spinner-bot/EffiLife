import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const root = fileURLToPath(new URL('../', import.meta.url))
export const version = readFileSync(resolve(root, 'VERSION'), 'utf8').trim()
if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error('VERSION must contain a semantic product version')
const packageVersion = JSON.parse(readFileSync(resolve(root, 'package.json'), 'utf8')).version
if (version !== packageVersion) throw new Error('package.json version differs from VERSION')
const nativePath = resolve(root, 'apps/desktop/src-tauri/tauri.conf.json')
if (existsSync(nativePath)) {
  const nativeConfig = JSON.parse(readFileSync(nativePath, 'utf8'))
  const nativeVersion = nativeConfig.version.endsWith('.json') ? JSON.parse(readFileSync(resolve(dirname(nativePath), nativeConfig.version), 'utf8')).version : nativeConfig.version
  if (nativeVersion !== version) throw new Error('Tauri version differs from VERSION')
  const cargo = readFileSync(resolve(dirname(nativePath), 'Cargo.toml'), 'utf8')
  if (cargo.match(/^version\s*=\s*"([^"]+)"/m)?.[1] !== version) throw new Error('Cargo package version differs from VERSION')
}
const changes = readFileSync(resolve(root, 'CHANGELOG.md'), 'utf8')
if (!changes.includes('[' + version + ']')) throw new Error('Current product version has no changelog entry')
const structured = JSON.parse(readFileSync(resolve(root, 'src/data/changelog.json'), 'utf8'))
if (!structured.generations || !Object.keys(structured.generations).length) throw new Error('CHANGELOG.json needs generations')
for (const [id, generation] of Object.entries(structured.generations)) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(generation.date)) throw new Error('CHANGELOG.json generation ' + id + ' needs an ISO date')
  for (const audience of ['user', 'developer']) {
    if (typeof generation[audience] !== 'string' || !generation[audience].trim()) throw new Error('CHANGELOG.json generation ' + id + ' needs ' + audience + ' content')
  }
}
if (!structured.products || !Object.keys(structured.products).length) throw new Error('CHANGELOG.json needs products')
for (const [productId, product] of Object.entries(structured.products)) {
  if (!product.versions || !Object.keys(product.versions).length) throw new Error('CHANGELOG.json ' + productId + ' needs versions')
  for (const [id, entry] of Object.entries(product.versions)) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(entry.date)) throw new Error('CHANGELOG.json ' + productId + '@' + id + ' needs an ISO date')
    for (const audience of ['user', 'developer']) {
      if (typeof entry[audience] !== 'string' || !entry[audience].trim()) throw new Error('CHANGELOG.json ' + productId + '@' + id + ' needs ' + audience + ' content')
    }
  }
}
if (!structured.products['effilife-v3']?.versions?.[version]) throw new Error('CHANGELOG.json effilife-v3 is missing the current version')
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  console.log('EffiLife v' + version + ': version and changelog are consistent')
}

