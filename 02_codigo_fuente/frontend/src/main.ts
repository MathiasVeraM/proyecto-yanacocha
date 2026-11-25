import './assets/styles/main.css'
import './movil/estilos/movil.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { esMovil } from './movil/plataforma'

// Los estilos de la app móvil cuelgan de esta clase y no afectan a la web
if (esMovil) document.documentElement.classList.add('movil')

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
