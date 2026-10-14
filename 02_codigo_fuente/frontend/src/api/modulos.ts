import { request } from './http'
import type { Modulo, ModuloCreate, ModuloUpdate } from '@/types'

export const modulosApi = {
  crear: (datos: ModuloCreate) => request<Modulo>('POST', '/api/auth/modulos', datos),

  actualizar: (id: number, datos: ModuloUpdate) =>
    request<Modulo>('PUT', `/api/auth/modulos/${id}`, datos),

  eliminar: (id: number) => request<null>('DELETE', `/api/auth/modulos/${id}`),
}
