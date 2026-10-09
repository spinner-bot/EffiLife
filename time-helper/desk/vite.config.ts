import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { versionPlugin } from './vite-plugins/version-plugin'

export default defineConfig({
  plugins: [vue(), versionPlugin()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: '0.0.0.0',
  },
  envPrefix: ['VITE_', 'TAURI_'],
  build: {
    target: ['es2021', 'chrome100', 'safari13'],
    minify: !process.env.TAURI_DEBUG ? 'esbuild' : false,
    sourcemap: !!process.env.TAURI_DEBUG,
    rollupOptions: {
      output: {
        // Keep stable third-party code out of the workspace entry chunk. This
        // improves browser/Tauri cache reuse after a small application update
        // and keeps the initial chunk below the warning threshold as the
        // bilingual catalog and unified shell grow.
        manualChunks(id) {
          const moduleId = id.replaceAll('\\', '/')
          if (!moduleId.includes('/node_modules/')) return undefined
          if (moduleId.includes('/vue/') || moduleId.includes('/@vue/') || moduleId.includes('/pinia/') || moduleId.includes('/vue-router/')) return 'vendor-vue'
          if (moduleId.includes('/lucide-vue-next/')) return 'vendor-icons'
          if (moduleId.includes('/chart.js/') || moduleId.includes('/vue-chartjs/')) return 'vendor-charts'
          if (moduleId.includes('/jszip/') || moduleId.includes('/file-saver/')) return 'vendor-archive'
          if (moduleId.includes('/@tauri-apps/')) return 'vendor-tauri'
          return undefined
        },
      },
    },
  },
})
