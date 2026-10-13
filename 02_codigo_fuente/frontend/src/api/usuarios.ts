import { request } from './http'
import type { Rol, Usuario, UsuarioCreate, UsuarioUpdate } from '@/types'

export const usuariosApi = {
  listar: () => request<Usuario[]>('GET', '/api/auth/usuarios'),

  crear: (datos: UsuarioCreate) => request<Usuario>('POST', '/api/auth/usuarios', datos),

  actualizar: (id: number, datos: UsuarioUpdate) =>
    request<Usuario>('PUT', `/api/auth/usuarios/${id}`, datos),

  desactivar: (id: number) => request<Usuario>('PATCH', `/api/auth/usuarios/${id}/desactivar`),
}

export const rolesApi = {
  listar: () => request<Rol[]>('GET', '/api/auth/roles'),
}
