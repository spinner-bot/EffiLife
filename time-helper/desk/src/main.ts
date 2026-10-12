import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'

const app = createApp(App)

function reportRuntimeError(error: unknown, source: string): void {
  const message = error instanceof Error ? error.message : String(error)
  window.dispatchEvent(new CustomEvent('effilife:runtime-error', { detail: { message, source } }))
}

app.config.errorHandler = (error, _instance, info) => {
  console.error('EffiLife runtime error:', error, info)
  reportRuntimeError(error, info)
}

window.addEventListener('unhandledrejection', (event) => {
  console.error('EffiLife unhandled promise rejection:', event.reason)
  reportRuntimeError(event.reason, 'unhandled promise rejection')
})

app.use(createPinia())
app.use(router)

app.mount('#app')
