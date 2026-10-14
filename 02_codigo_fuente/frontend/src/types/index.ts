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

export interface RolCreate {
  nombre_rol: string
  descripcion?: string | null
}

export type RolUpdate = Partial<RolCreate>

export interface Modulo {
  id_modulo: number
  nombre_modulo: string
  codigo_servicio: string
}

export type ModuloCreate = Omit<Modulo, 'id_modulo'>

export type ModuloUpdate = Partial<ModuloCreate>

export interface RolConUsuarios extends Rol {
  total_usuarios: number
}

export interface Permiso {
  id_rol: number
  id_modulo: number
}

export interface MatrizPermisos {
  roles: RolConUsuarios[]
  modulos: Modulo[]
  permisos: Permiso[]
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface TokenPayload {
  sub: string
  id_usuario: number
  id_rol: number
  exp: number
}
