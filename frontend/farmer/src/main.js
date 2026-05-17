import { createApp } from 'vue'
import 'leaflet/dist/leaflet.css'
import './styles/design-tokens.css'
import './styles/global.css'
import './styles/utilities.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')
