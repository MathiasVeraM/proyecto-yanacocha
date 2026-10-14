import { request } from './http'
import type { MatrizPermisos, Permiso } from '@/types'

export const permisosApi = {
  matriz: () => request<MatrizPermisos>('GET', '/api/auth/permisos/matriz'),

  asignar: (idRol: number, idModulo: number) =>
    request<Permiso>('PUT', `/api/auth/permisos/${idRol}/${idModulo}`),

  quitar: (idRol: number, idModulo: number) =>
    request<null>('DELETE', `/api/auth/permisos/${idRol}/${idModulo}`),
}
