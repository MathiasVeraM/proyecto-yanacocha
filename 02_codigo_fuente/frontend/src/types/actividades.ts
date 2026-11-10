import type { Animal, Recinto } from '@/types/animales'

export type TipoActividad = 'alimentacion' | 'limpieza' | 'enriquecimiento' | 'entrenamiento'
export type TipoEnriquecimiento = 'social' | 'sensorial' | 'alimenticio' | 'cognitivo'
export type UnidadFrecuencia = 'horas' | 'dias' | 'semanas'
export type UnidadCantidad = 'g' | 'kg' | 'unidad'

export interface DietaAlimento {
  id_dieta_alimento: number
  id_dieta: number
  nombre_alimento: string
  cantidad_gramos: number
  unidad_cantidad?: UnidadCantidad
}

export interface Dieta {
  id_dieta: number
  id_animal: number
  id_usuario_creador: number
  fecha_inicio: string
  fecha_fin: string | null
  frecuencia_valor: number
  frecuencia_unidad: UnidadFrecuencia
  vigente: boolean
  observaciones: string | null
  alimentos: DietaAlimento[]
  es_restriccion?: boolean
}

export interface Actividad {
  id_actividad: number
  tipo_actividad: TipoActividad
  id_animal: number | null
  id_recinto: number | null
  fecha_programada: string
  hora_programada: string | null
  duracion_horas: number
  duracion_minutos: number
  id_usuario_programo: number
  fecha_registro: string
  completada: boolean
  observaciones: string | null
  id_usuario_completo: number | null
  fecha_completada: string | null
  id_dieta: number | null
  tipo_enriquecimiento: TipoEnriquecimiento | null
  descripcion_estimulo: string | null
  objetivo_entrenamiento: string | null
  tipo_refuerzo: string | null
  cancelada: boolean
  id_usuario_responsable?: number | null
  animal?: Animal
  recinto?: Recinto
}

export interface EventoCalendario {
  id_actividad: number
  inicio: string
  fin: string
  tipo: TipoActividad
  completada: boolean
  todo_el_dia: boolean
}

export interface AlimentoCreate {
  nombre_alimento: string
  cantidad_gramos: number
  unidad_cantidad: UnidadCantidad
}

export interface DietaCreate {
  id_animal: number
  fecha_inicio: string
  frecuencia_valor: number
  frecuencia_unidad: UnidadFrecuencia
  alimentos: AlimentoCreate[]
  es_restriccion: boolean
}

export interface FiltrosActividades {
  id_animal?: number
  id_recinto?: number
  tipo_actividad?: TipoActividad
  completada?: boolean
  fecha_desde?: string
  fecha_hasta?: string
}

export interface UsuarioResponsable {
  id_usuario: number
  nombre: string
  apellido: string
  correo: string
}
