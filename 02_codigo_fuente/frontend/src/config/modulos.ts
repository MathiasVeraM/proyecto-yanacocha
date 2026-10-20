// Módulos del sistema. Los códigos deben coincidir con la columna codigo_servicio de la tabla modulo
// y con los que el gateway lee del token.

export const MODULO_FICHAS_EJEMPLARES = 'servicio-gestion-animal'
export const MODULO_PLANIFICACION = 'servicio-actividades'
export const MODULO_ESTADISTICAS = 'servicio-estadisticas'
export const MODULO_ACCESOS = 'servicio-accesos'

export interface ItemNavegacion {
  label: string
  codigoServicio: string
  // Nombre de la ruta a la que lleva el ítem
  ruta: string
  badge?: number
  alert?: boolean
}

// Orden en que aparecen en el menú lateral. Cada ítem solo se muestra si el usuario tiene permiso.
export const ITEMS_NAVEGACION: ItemNavegacion[] = [
  { label: 'Fichas de ejemplares', codigoServicio: MODULO_FICHAS_EJEMPLARES, ruta: 'fichas', badge: 4 },
  { label: 'Planificación', codigoServicio: MODULO_PLANIFICACION, ruta: 'planificacion' },
  {
    label: 'Bienestar animal',
    codigoServicio: MODULO_ESTADISTICAS,
    ruta: 'bienestar',
    badge: 3,
    alert: true,
  },
  { label: 'Seguridad & usuarios', codigoServicio: MODULO_ACCESOS, ruta: 'usuarios' },
]
