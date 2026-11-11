import { packageFormats, extensionFor } from '../extensions/formats'

export function isNative(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}
export async function saveDataFile(bytes: Uint8Array, filename: string): Promise<boolean> {
  if (isNative()) {
    const [{ save }, { writeFile }] = await Promise.all([import('@tauri-apps/plugin-dialog'), import('@tauri-apps/plugin-fs')])
    const path = await save({ defaultPath: filename, filters: [{ name: 'EffiLife', extensions: [extensionFor('data')] }] })
    if (!path) return false
    await writeFile(path, bytes)
    return true
  }
  const url = URL.createObjectURL(new Blob([Uint8Array.from(bytes).buffer], { type: packageFormats.data.mime }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.append(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  return true
}

