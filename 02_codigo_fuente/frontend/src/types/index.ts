// Tipos que reflejan los esquemas del servicio de accesos

export interface Usuario {
  id_usuario: number
  nombre: string
  apellido: string
  correo: string
  id_rol: number
  activo: boolean
}

export interface UsuarioCreate {
  nombre: string
  apellido: string
  correo: string
  password: string
  id_rol: number
}

export type UsuarioUpdate = Partial<UsuarioCreate & { activo: boolean }>

export interface Rol {
  id_rol: number
  nombre_rol: string
  descripcion: string | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface TokenPayload {
  sub: string
  id_rol: number
  exp: number
}
