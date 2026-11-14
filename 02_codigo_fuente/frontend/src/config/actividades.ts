import type {
  Actividad,
  CategoriaObservacion,
  Dieta,
  SeveridadObservacion,
  TipoActividad,
  UsuarioActividad,
} from '@/types/actividades'
import type { Animal, Recinto } from '@/types/animales'

// Orden en que aparecen los tipos en indicadores, leyenda y vista mes.
// Las dosis de tratamiento las genera el sistema a partir de los tratamientos en curso
export const TIPOS_ACTIVIDAD: TipoActividad[] = [
  'alimentacion',
  'enriquecimiento',
  'entrenamiento',
  'limpieza',
  'tratamiento',
]

export const TIPO_LABEL: Record<TipoActividad, string> = {
  alimentacion: 'Alimentación',
  enriquecimiento: 'Enriquecimiento',
  entrenamiento: 'Entrenamiento',
  limpieza: 'Limpieza',
  tratamiento: 'Tratamiento',
}

export const TIPOS_ENRIQUECIMIENTO = {
  social: 'Social',
  sensorial: 'Sensorial',
  alimenticio: 'Alimenticio',
  cognitivo: 'Cognitivo',
} as const

export const CATEGORIAS_OBSERVACION: Record<CategoriaObservacion, { label: string; ayuda: string; ejemplo: string }> = {
  recinto: {
    label: 'Recinto',
    ayuda: 'Limpieza, daños, temperatura',
    ejemplo: 'Ej.: la malla del lado norte está rota y el bebedero tiene fuga.',
  },
  comportamiento: {
    label: 'Comportamiento',
    ayuda: 'Actividad, apetito, conducta',
    ejemplo: 'Ej.: no se acercó a comer y pasó la mañana escondido.',
  },
  estado_fisico: {
    label: 'Estado físico',
    ayuda: 'Heridas, peso, pelaje o plumaje',
    ejemplo: 'Ej.: cojea de la pata trasera izquierda, sin herida visible.',
  },
}

export const SEVERIDADES: SeveridadObservacion[] = ['bajo', 'medio', 'alto']

// Mismo criterio que usa el servicio para marcar la alerta (HU RF-10)
export function generaAlerta(categoria: CategoriaObservacion, severidad: SeveridadObservacion) {
  return categoria !== 'recinto' && severidad !== 'bajo'
}

// ---- Horas ----

export function aMinutos(hora: string) {
  const [h, m] = hora.split(':').map(Number)
  return h! * 60 + m!
}

export function aHora(minutos: number) {
  return `${String(Math.floor(minutos / 60) % 24).padStart(2, '0')}:${String(minutos % 60).padStart(2, '0')}`
}

export function horaCorta(actividad: Actividad) {
  return actividad.hora_programada?.slice(0, 5) ?? ''
}

export function duracionMinutos(actividad: Actividad) {
  return actividad.duracion_horas * 60 + actividad.duracion_minutos
}

export function horaFin(actividad: Actividad) {
  if (!actividad.hora_programada) return ''
  return aHora(aMinutos(actividad.hora_programada) + duracionMinutos(actividad))
}

export function textoDuracion(minutos: number) {
  if (!minutos) return '—'
  const h = Math.floor(minutos / 60)
  const m = minutos % 60
  return [h ? `${h} h` : '', m ? `${m} min` : ''].filter(Boolean).join(' ')
}

// ---- Fechas (sin pasar por UTC para no correr el día) ----

export function fechaIso(fecha: Date) {
  return `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, '0')}-${String(fecha.getDate()).padStart(2, '0')}`
}

export function deIso(fecha: string) {
  const [a, m, d] = fecha.split('-').map(Number)
  return new Date(a!, m! - 1, d!, 12)
}

export function sumarDias(fecha: string, dias: number) {
  const d = deIso(fecha)
  d.setDate(d.getDate() + dias)
  return fechaIso(d)
}

export function lunesDe(fecha: string) {
  const dia = deIso(fecha).getDay()
  return sumarDias(fecha, dia === 0 ? -6 : 1 - dia)
}

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
const DIAS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']

export function nombreMes(fecha: string) {
  return MESES[deIso(fecha).getMonth()]!
}

// "Martes 10 de noviembre"
export function diaLargo(fecha: string) {
  const d = deIso(fecha)
  const texto = `${DIAS[d.getDay()]} ${d.getDate()} de ${MESES[d.getMonth()]}`
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

export function diaCorto(fecha: string) {
  return DIAS[deIso(fecha).getDay()]!.slice(0, 3)
}

// ---- Estado ----

export function estaAtrasada(actividad: Actividad, hoy: string, ahora: string) {
  if (actividad.completada || actividad.cancelada) return false
  if (actividad.fecha_programada < hoy) return true
  if (actividad.fecha_programada > hoy || !actividad.hora_programada) return false
  return aMinutos(horaCorta(actividad)) + duracionMinutos(actividad) < aMinutos(ahora)
}

// ---- Textos que dependen de ejemplares, recintos, dietas y usuarios ----

export interface ContextoActividades {
  animales: Animal[]
  recintos: Recinto[]
  dietasPorId: Record<number, Dieta>
  usuarios: UsuarioActividad[]
}

export function describirActividades(ctx: ContextoActividades) {
  const animal = (id: number | null) => ctx.animales.find((a) => a.id_animal === id)
  const recinto = (id: number | null) => ctx.recintos.find((r) => r.id_recinto === id)

  const nombreAnimal = (id: number | null) => {
    const a = animal(id)
    return a?.nombre ?? a?.taxonomia.nombre_comun ?? `Ejemplar #${id}`
  }
  const nombreRecinto = (id: number | null) => recinto(id)?.nombre_recinto ?? `Recinto #${id}`

  // Recinto donde ocurre: el de la limpieza o el del ejemplar
  const lugar = (a: Actividad) => {
    const r = a.tipo_actividad === 'limpieza' ? recinto(a.id_recinto) : animal(a.id_animal)?.recinto
    if (!r) return '—'
    return r.tipo ? `${r.nombre_recinto} · ${r.tipo}` : r.nombre_recinto
  }

  const alimentos = (a: Actividad) => {
    const dieta = a.id_dieta ? ctx.dietasPorId[a.id_dieta] : undefined
    return dieta?.alimentos.map((x) => x.nombre_alimento).join(' + ') || 'Plan de alimentación'
  }

  // "Limpieza · AV-02" / "Alimentación · Yaku"
  const titulo = (a: Actividad) =>
    a.tipo_actividad === 'limpieza'
      ? `Limpieza · ${nombreRecinto(a.id_recinto)}`
      : `${TIPO_LABEL[a.tipo_actividad]} · ${nombreAnimal(a.id_animal)}`

  // Texto corto para la tarjeta del calendario
  const tituloTarjeta = (a: Actividad) =>
    a.tipo_actividad === 'limpieza'
      ? `Limpieza ${nombreRecinto(a.id_recinto)}`
      : `${nombreAnimal(a.id_animal)} · ${TIPO_LABEL[a.tipo_actividad]}`

  const detalle = (a: Actividad) => {
    if (a.tipo_actividad === 'alimentacion') return alimentos(a)
    if (a.tipo_actividad === 'enriquecimiento') return a.descripcion_estimulo ?? 'Enriquecimiento'
    if (a.tipo_actividad === 'entrenamiento') return a.objetivo_entrenamiento ?? 'Entrenamiento'
    if (a.tipo_actividad === 'tratamiento') return a.descripcion_tratamiento || 'Dosis de tratamiento'
    return a.observaciones || recinto(a.id_recinto)?.tipo || 'Limpieza del recinto'
  }

  const usuario = (id: number | null) => {
    if (id === null) return '—'
    const u = ctx.usuarios.find((x) => x.id_usuario === id)
    return u ? `${u.nombre} ${u.apellido}` : `Usuario #${id}`
  }

  return { animal, recinto, nombreAnimal, nombreRecinto, lugar, alimentos, titulo, tituloTarjeta, detalle, usuario }
}
