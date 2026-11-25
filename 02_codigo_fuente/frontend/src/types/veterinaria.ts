export type EstadoTratamiento = 'en_curso' | 'finalizado' | 'suspendido'
export type UnidadFrecuenciaTratamiento = 'horas' | 'dias'
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
  descripcion: string
  medicamento_o_proceso?: string | null
  dosis?: string | null
  frecuencia?: string | null
  fecha_inicio: string
  fecha_fin: string | null
  frecuencia_valor: number | null
  frecuencia_unidad: UnidadFrecuenciaTratamiento | null
  hora_inicio: string | null
  estado: EstadoTratamiento
  medicamentos: TratamientoMedicamento[]
}

export interface TratamientoMedicamento {
  id_tratamiento_medicamento: number
  nombre_medicamento: string
  dosis_ml: number
}

export interface TratamientoMedicamentoCreate {
  nombre_medicamento: string
  dosis_ml: number
}

export interface TratamientoCreate {
  descripcion: string
  frecuencia_valor: number
  frecuencia_unidad: UnidadFrecuenciaTratamiento
  hora_inicio: string
  medicamentos: TratamientoMedicamentoCreate[]
  fecha_inicio?: string | null
  fecha_fin?: string | null
  estado?: EstadoTratamiento
}

export type TratamientoUpdate = Partial<TratamientoCreate>
