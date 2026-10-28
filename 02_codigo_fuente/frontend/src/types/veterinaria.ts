export type EstadoTratamiento = 'en_curso' | 'finalizado' | 'suspendido'
export type Hidratacion =
  | 'normal'
  | 'deshidratacion_leve'
  | 'deshidratacion_moderada'
  | 'deshidratacion_severa'
export type Mucosas = 'rosadas' | 'palidas' | 'cianoticas' | 'ictericas' | 'congestionadas'
export type Actitud = 'alerta' | 'deprimido' | 'estuporoso' | 'agitado'

export interface SignosVitales {
  id_signos_vitales: number
  id_diagnostico: number
  peso_kg: number | null
  temperatura_c: number | null
  frecuencia_cardiaca_lpm: number | null
  frecuencia_respiratoria_rpm: number | null
  tiempo_llenado_capilar_s: number | null
  hidratacion: Hidratacion | null
  condicion_corporal: number | null
  mucosas: Mucosas | null
  actitud: Actitud | null
}

export type SignosVitalesCreate = Partial<
  Omit<SignosVitales, 'id_signos_vitales' | 'id_diagnostico'>
>

export interface SignosVitalesHistorial extends SignosVitales {
  fecha_diagnostico: string
}

export interface Diagnostico {
  id_diagnostico: number
  id_animal: number
  id_usuario: number
  diagnostico: string
  observaciones: string | null
  es_critico: boolean
  fecha_registro: string
  signos_vitales: SignosVitales | null
}

export interface DiagnosticoCreate {
  diagnostico: string
  observaciones?: string | null
  es_critico?: boolean
  signos_vitales?: SignosVitalesCreate | null
}

export type DiagnosticoUpdate = Partial<Omit<DiagnosticoCreate, 'signos_vitales'>> & {
  signos_vitales?: SignosVitalesCreate | null
}

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
