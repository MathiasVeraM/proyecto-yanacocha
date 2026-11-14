import type { Animal, EstadoAnimal, Recinto, Taxonomia } from '@/types/animales'

export type TipoActividad =
  | 'alimentacion'
  | 'limpieza'
  | 'enriquecimiento'
  | 'entrenamiento'
  | 'tratamiento'
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

export interface MedicamentoDosis {
  nombre_medicamento: string
  dosis_ml: number
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
  id_tratamiento: number | null
  // Qué se aplica en una dosis (solo en actividades de tipo tratamiento)
  descripcion_tratamiento?: string | null
  // Medicamentos y dosis a administrar (solo en actividades de tipo tratamiento)
  medicamentos_tratamiento?: MedicamentoDosis[]
  cancelada: boolean
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

// ---- Listas de referencia de Planificación (GET /api/actividades/referencias) ----
// Solo lo necesario para mostrar nombres y llenar selectores: cualquier rol con el módulo de
// Planificación las puede pedir, sin permisos sobre Fichas ni Accesos.

export interface AnimalReferencia {
  id_animal: number
  codigo_animal: string
  nombre: string | null
  id_taxonomia: number
  id_recinto: number
  estado_actual: EstadoAnimal
  taxonomia: Pick<Taxonomia, 'id_taxonomia' | 'nombre_comun' | 'especie' | 'clase'>
  recinto: Recinto
}

// Nombre de quien programó o completó una actividad (y, más adelante, de los responsables)
export interface UsuarioReferencia {
  id_usuario: number
  nombre: string
  apellido: string
  // Los inactivos se incluyen para mostrar actividades antiguas; los selectores solo ofrecen activos
  activo: boolean
}

export interface ReferenciasPlanificacion {
  animales: AnimalReferencia[]
  recintos: Recinto[]
  usuarios: UsuarioReferencia[]
}

// Observaciones de bienestar sobre una actividad (HU RF-10)
export type CategoriaObservacion = 'recinto' | 'comportamiento' | 'estado_fisico'
export type SeveridadObservacion = 'bajo' | 'medio' | 'alto'

export interface Observacion {
  id_observacion: number
  id_actividad: number
  categoria: CategoriaObservacion
  severidad: SeveridadObservacion
  detalle: string
  // Lo calcula el servicio: estado físico o comportamiento con severidad media o alta
  genera_alerta: boolean
  id_usuario: number
  fecha_registro: string
}

export interface ObservacionCreate {
  categoria: CategoriaObservacion
  severidad: SeveridadObservacion
  detalle: string
}

// Límites que define el backend (config.py); se usan como min y max de los campos
export interface LimitesActividades {
  hoy: string
  hora_actual: string
  fecha_min: string
  fecha_max: string
  duracion_max_minutos: number
  duracion_enriquecimiento_minutos: number
  repeticion_meses_max: number
  dieta_inicio_fecha_max: string
}

// Cómo se repite una actividad. dias_semana: 0 = lunes … 6 = domingo; null = todos los días
export interface Repeticion {
  dias_semana: number[] | null
  fecha_fin?: string
  meses?: number
}

// Actividad con la que se cruza en horario la que se quiere crear o mover (409 "cruce_horario")
export interface CruceHorario {
  id_actividad: number
  tipo_actividad: TipoActividad
  fecha_programada: string
  hora_programada: string | null
  duracion_minutos: number
}

// Lo que se puede cambiar de una actividad pendiente
export interface ActividadCambios {
  fecha_programada?: string
  hora_programada?: string
  duracion_horas?: number
  duracion_minutos?: number
  observaciones?: string | null
  tipo_enriquecimiento?: TipoEnriquecimiento
  descripcion_estimulo?: string
  objetivo_entrenamiento?: string
  tipo_refuerzo?: string
}
