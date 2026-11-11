import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises'
import { resolve, relative } from 'node:path'
import { createHash } from 'node:crypto'
import JSZip from 'jszip'
import formats from '../shared/package-formats.json' with { type: 'json' }

const output = resolve('dist/examples')
await mkdir(output, { recursive: true })
async function files(root) {
  return (await readdir(root, { withFileTypes: true })).flatMap(entry => entry.isDirectory() ? [] : [resolve(root, entry.name)])
    .concat(...await Promise.all((await readdir(root, { withFileTypes: true })).filter(entry => entry.isDirectory()).map(entry => files(resolve(root, entry.name)))))
}
for (const name of await readdir('resources/examples')) {
  const root = resolve('resources/examples', name)
  const manifest = JSON.parse(await readFile(resolve(root, 'manifest.json'), 'utf8'))
  const zip = new JSZip(), checksums = {}
  for (const path of (await files(root)).sort()) {
    const key = relative(root, path).replaceAll('\\', '/')
    if (key === 'manifest.json') continue
    const bytes = await readFile(path)
    checksums[key] = createHash('sha256').update(bytes).digest('hex')
    zip.file(key, bytes, { date: new Date('2026-11-11T00:00:00Z') })
  }
  zip.file('manifest.json', JSON.stringify({ ...manifest, checksums }, null, 2), { date: new Date('2026-11-11T00:00:00Z') })
  const filename = name + '.' + formats.formats[manifest.type].current
  await writeFile(resolve(output, filename), await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }))
  process.stdout.write('Example: dist/examples/' + filename + '\n')
}

