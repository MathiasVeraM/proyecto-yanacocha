import { createRouter, createWebHashHistory } from 'vue-router'
import { MODULO_PLANIFICACION } from '@/config/modulos'
import { useAuthStore } from '@/stores/auth'

// Rutas de la app móvil: pocas pantallas y planas (todo a máximo unos toques de la principal).
// Hash en vez de historial HTML5: el WebView de Android no tiene servidor que resuelva rutas.
export function crearRouterMovil() {
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      {
        path: '/login',
        name: 'login',
        component: () => import('./views/LoginMovilView.vue'),
        meta: { public: true },
      },
      {
        path: '/',
        component: () => import('./layouts/LayoutMovil.vue'),
        children: [
          {
            path: '',
            name: 'actividades',
            component: () => import('./views/HoyMovilView.vue'),
          },
          {
            path: 'calendario',
            name: 'calendario',
            component: () => import('./views/CalendarioMovilView.vue'),
          },
          {
            path: 'envio',
            name: 'envio',
            component: () => import('./views/EnvioMovilView.vue'),
          },
        ],
      },
      { path: '/:pathMatch(.*)*', redirect: '/' },
    ],
  })

  router.beforeEach((to) => {
    const auth = useAuthStore()
    if (!to.meta.public && !auth.isAuthenticated) {
      auth.logout()
      return { name: 'login' }
    }
    if (to.name === 'login' && auth.isAuthenticated && auth.tieneAcceso(MODULO_PLANIFICACION)) {
      return { name: 'actividades' }
    }
  })

  return router
}
