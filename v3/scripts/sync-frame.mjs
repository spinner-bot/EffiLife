import { readFile, writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'

const root = new URL('../', import.meta.url)
const script = await readFile(new URL('public/extension-frame.js', root), 'utf8')
const css = await readFile(new URL('public/extension-frame.css', root), 'utf8')
const hash = 'sha256-' + createHash('sha256').update(script).digest('base64')
const policy = "default-src 'none'; script-src '" + hash + "'; style-src 'unsafe-inline'; worker-src blob:; connect-src 'none'; img-src 'none'; font-src 'none'; media-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"
const html = '<!doctype html>\n<html><head><meta charset="utf-8">\n<meta http-equiv="Content-Security-Policy" content="' + policy + '">\n<style>' + css + '</style></head>\n<body><canvas id="canvas"></canvas><div id="view"></div>\n<script>' + script + '</script></body></html>\n'
const configPath = new URL('apps/desktop/src-tauri/tauri.conf.json', root)
const config = JSON.parse(await readFile(configPath, 'utf8'))
for (const key of ['csp', 'devCsp']) {
  config.app.security[key] = config.app.security[key].replace(/script-src [^;]+;/, "script-src 'self' '" + hash + "';")
}
for (const [path, expected] of [[new URL('public/extension-frame.html', root), html], [configPath, JSON.stringify(config, null, 2) + '\n']]) {
  if (process.argv.includes('--check')) {
    if (await readFile(path, 'utf8') !== expected) throw new Error(fileURLToPath(path) + ': run npm run sync:frame before building')
  } else await writeFile(path, expected)
}
console.log('Trusted frame CSP:', hash)
