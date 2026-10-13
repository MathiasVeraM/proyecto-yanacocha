import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import type { TokenPayload } from '@/types'

const TOKEN_KEY = 'yanacocha_token'

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

  async function login(correo: string, password: string, recordar: boolean) {
    const { access_token } = await authApi.login(correo, password)
    token.value = access_token
    ;(recordar ? localStorage : sessionStorage).setItem(TOKEN_KEY, access_token)
  }

  function logout() {
    token.value = null
    localStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(TOKEN_KEY)
  }

  return { token, payload, isAuthenticated, login, logout }
})
