import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const version = readFileSync(new URL('./VERSION', import.meta.url), 'utf8').trim()
const manifest = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf8'))
if (!/^\d+\.\d+\.\d+$/.test(version) || manifest.version !== version) {
  throw new Error('Product version metadata is invalid')
}

export default defineConfig({
  plugins: [vue()],
  define: { __APP_VERSION__: JSON.stringify(version) },
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  server: { strictPort: true, watch: { ignored: ['**/src-tauri/**', '**/.tools/**', '**/.cache/**'] } },
  build: {
    target: 'es2022',
    rollupOptions: { output: { manualChunks(id) {
      if (id.includes('/node_modules/')) {
        if (id.includes('/jszip/')) return 'archive'
        if (id.includes('/reka-ui/')) return 'accessible-controls'
        if (id.includes('/lucide-vue-next/')) return 'icons'
        return 'vendor'
      }
    } } },
  },
})

