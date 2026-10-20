import { createRouter, createWebHistory } from 'vue-router'
import {
  ITEMS_NAVEGACION,
  MODULO_ACCESOS,
  MODULO_ESTADISTICAS,
  MODULO_FICHAS_EJEMPLARES,
  MODULO_PLANIFICACION,
} from '@/config/modulos'
import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    // Código de servicio que el usuario debe tener para entrar a la pantalla
    modulo?: string
  }
}

// Primera pantalla a la que el usuario tiene acceso; si no tiene ninguna, la de "sin acceso"
function rutaInicial() {
  const auth = useAuthStore()
  const item = ITEMS_NAVEGACION.find((i) => auth.tieneAcceso(i.codigoServicio))
  return { name: item?.ruta ?? 'sin-acceso' }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/AppLayout.vue'),
      redirect: rutaInicial,
      children: [
        {
          path: 'fichas',
          name: 'fichas',
          component: () => import('@/views/FichasView.vue'),
          meta: { modulo: MODULO_FICHAS_EJEMPLARES },
        },
        {
          path: 'planificacion',
          name: 'planificacion',
          component: () => import('@/views/PlanificacionView.vue'),
          meta: { modulo: MODULO_PLANIFICACION },
        },
        {
          path: 'bienestar',
          name: 'bienestar',
          component: () => import('@/views/BienestarView.vue'),
          meta: { modulo: MODULO_ESTADISTICAS },
        },
        {
          path: 'usuarios',
          name: 'usuarios',
          component: () => import('@/views/UsuariosView.vue'),
          meta: { modulo: MODULO_ACCESOS },
        },
        {
          path: 'sin-acceso',
          name: 'sin-acceso',
          component: () => import('@/views/SinAccesoView.vue'),
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
  if (to.name === 'login' && auth.isAuthenticated) {
    return rutaInicial()
  }
  // Pantalla de un módulo sin permiso: se redirige a una a la que sí tenga acceso
  if (to.meta.modulo && !auth.tieneAcceso(to.meta.modulo)) {
    return rutaInicial()
  }
})

export default router
