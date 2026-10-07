import { request } from './http'
import type { TokenResponse } from '@/types'

export const authApi = {
  login: (correo: string, password: string) =>
    request<TokenResponse>('POST', '/api/auth/login', { correo, password }),
}
