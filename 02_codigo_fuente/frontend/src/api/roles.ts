import { request } from './http'
import type { Rol, RolCreate, RolUpdate } from '@/types'

export const rolesApi = {
  listar: () => request<Rol[]>('GET', '/api/auth/roles'),

  crear: (datos: RolCreate) => request<Rol>('POST', '/api/auth/roles', datos),

  actualizar: (id: number, datos: RolUpdate) => request<Rol>('PUT', `/api/auth/roles/${id}`, datos),

  eliminar: (id: number) => request<null>('DELETE', `/api/auth/roles/${id}`),
}
