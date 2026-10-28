export type EstadoTratamiento = 'en_curso' | 'finalizado' | 'suspendido'

export interface Diagnostico {
  id_diagnostico: number
  id_animal: number
  id_usuario: number
  diagnostico: string
  observaciones: string | null
  es_critico: boolean
  fecha_registro: string
}

export interface DiagnosticoCreate {
  diagnostico: string
  observaciones?: string | null
  es_critico?: boolean
}

export type DiagnosticoUpdate = Partial<DiagnosticoCreate>

export interface Tratamiento {
  id_tratamiento: number
  id_diagnostico: number
  medicamento_o_proceso: string
  dosis: string | null
  frecuencia: string | null
  fecha_inicio: string
  fecha_fin: string | null
  estado: EstadoTratamiento
}

export interface TratamientoCreate {
  medicamento_o_proceso: string
  dosis?: string | null
  frecuencia?: string | null
  fecha_inicio?: string | null
  fecha_fin?: string | null
  estado?: EstadoTratamiento
}

export type TratamientoUpdate = Partial<TratamientoCreate>
