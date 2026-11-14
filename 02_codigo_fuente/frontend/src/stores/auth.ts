import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import { limpiarCache } from '@/api/cache'
import type { TokenPayload } from '@/types'

const TOKEN_KEY = 'yanacocha_token'

// El administrador accede a todos los módulos sin que estén listados en su token (igual que en el gateway)
const ID_ROL_ADMIN = 1

function decodificarToken(token: string): TokenPayload | null {
  try {
    const base64 = token.split('.')[1]!.replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64)) as TokenPayload
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  // localStorage si el usuario marcó "Mantener sesión iniciada", si no sessionStorage
  const token = ref<string | null>(
    localStorage.getItem(TOKEN_KEY) ?? sessionStorage.getItem(TOKEN_KEY),
  )

  const payload = computed(() => (token.value ? decodificarToken(token.value) : null))

  const isAuthenticated = computed(
    () => !!payload.value && payload.value.exp * 1000 > Date.now(),
  )

  // Solo oculta o muestra pantallas: el permiso real lo aplica el gateway
  function tieneAcceso(codigoServicio: string) {
    if (!payload.value) return false
    if (payload.value.id_rol === ID_ROL_ADMIN) return true
    return payload.value.modulos?.includes(codigoServicio) ?? false
  }

  async function login(correo: string, password: string, recordar: boolean) {
    const { access_token } = await authApi.login(correo, password)
    // Nada de una sesión anterior debe verse con el usuario nuevo
    limpiarCache()
    token.value = access_token
    ;(recordar ? localStorage : sessionStorage).setItem(TOKEN_KEY, access_token)
  }

  function logout() {
    // Los datos en memoria (fichas, actividades, fotos) se borran al salir
    limpiarCache()
    token.value = null
    localStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(TOKEN_KEY)
  }

  return { token, payload, isAuthenticated, tieneAcceso, login, logout }
})
