import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import './ui/tokens.css'
import './ui/layout.css'
import './ui/controls.css'
import './ui/information.css'

createApp(App).use(router).mount('#app')

