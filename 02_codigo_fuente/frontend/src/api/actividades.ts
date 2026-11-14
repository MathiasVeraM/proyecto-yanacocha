import { ApiError, request } from './http'
import { alLimpiar } from './cache'
import type {
  Actividad,
  ActividadCambios,
  CruceHorario,
  LimitesActividades,
  Repeticion,
  Dieta,
  DietaCreate,
  EventoCalendario,
  FiltrosActividades,
  Observacion,
  ObservacionCreate,
  TipoEnriquecimiento,
  UsuarioActividad,
} from '@/types/actividades'
import type { Recinto } from '@/types/animales'
import { animalesApi, recintosApi } from '@/api/animales'
import { usuariosApi } from '@/api/usuarios'
import type { Animal } from '@/types/animales'

const URL = '/api/actividades'

function query(params: Record<string, string | number | boolean | undefined>) {
  const valores = Object.entries(params).filter(([, valor]) => valor !== undefined && valor !== '')
  return valores.length
    ? `?${new URLSearchParams(valores.map(([clave, valor]) => [clave, String(valor)]))}`
    : ''
}

// ?permitir_cruce=true cuando la persona ya vio el aviso de cruce de horario y eligió "crear igual"
const cruce = (permitir?: boolean) => (permitir ? '?permitir_cruce=true' : '')

// Si la API respondió que la actividad se cruza con otras, devuelve esas actividades
export function crucesDeError(error: unknown): CruceHorario[] | null {
  if (!(error instanceof ApiError) || error.status !== 409) return null
  const detalle = error.detalle as { codigo?: string; cruces?: CruceHorario[] } | undefined
  return detalle?.codigo === 'cruce_horario' ? (detalle.cruces ?? []) : null
}

export const actividadesApi = {
  // Límites de fechas y duración definidos en el backend
  limites: () => request<LimitesActividades>('GET', `${URL}/limites`),

  // La misma actividad en varias fechas (todos los días o ciertos días)
  crearRepetida: (datos: Record<string, unknown> & { tipo_actividad: string; repeticion: Repeticion }, permitirCruce?: boolean) =>
    request<Actividad[]>('POST', `${URL}/repetidas${cruce(permitirCruce)}`, datos),

  // Solo actividades pendientes; las dosis de tratamiento se cambian desde el tratamiento
  editar: (id: number, cambios: ActividadCambios, permitirCruce?: boolean) =>
    request<Actividad>('PUT', `${URL}/${id}${cruce(permitirCruce)}`, cambios),

  eliminar: (id: number) => request<null>('DELETE', `${URL}/${id}`),

  finalizarDieta: (idDieta: number) => request<Dieta>('POST', `${URL}/dietas/${idDieta}/finalizar`),

  cambiarFinDieta: (idDieta: number, fechaFin: string | null) =>
    request<Dieta>('PATCH', `${URL}/dietas/${idDieta}`, { fecha_fin: fechaFin }),

  listar: (filtros: FiltrosActividades = {}) =>
    request<Actividad[]>('GET', `${URL}${query({ ...filtros })}`),

  calendario: (fechaDesde: string, fechaHasta: string) =>
    request<EventoCalendario[]>(
      'GET',
      `${URL}/calendario${query({ fecha_desde: fechaDesde, fecha_hasta: fechaHasta })}`,
    ),

  completar: (id: number, observaciones?: string) =>
    request<Actividad>('POST', `${URL}/${id}/completar`, { observaciones }),

  // Vuelve a dejar pendiente una actividad completada
  reabrir: (id: number) => request<Actividad>('POST', `${URL}/${id}/reabrir`),

  observaciones: (idActividad: number) =>
    request<Observacion[]>('GET', `${URL}/${idActividad}/observaciones`),

  observacionesEnRango: (fechaDesde: string, fechaHasta: string) =>
    request<Observacion[]>(
      'GET',
      `${URL}/observaciones${query({ fecha_desde: fechaDesde, fecha_hasta: fechaHasta })}`,
    ),

  agregarObservacion: (idActividad: number, datos: ObservacionCreate) =>
    request<Observacion>('POST', `${URL}/${idActividad}/observaciones`, datos),

  generarTomas: (idDieta: number, fechaHasta?: string) =>
    request<{ tomas: Actividad[] }>('POST', `${URL}/tomas/generar`, {
      id_dieta: idDieta,
      fecha_hasta: fechaHasta,
    }),

  // La renovación solo agrega días al horizonte: no invalida la caché (Planificación refresca
  // lo que se está viendo al terminar, y el resto se revalida al mostrarse)
  renovarTomas: () =>
    request<Actividad[]>('POST', `${URL}/tomas/renovar`, undefined, { invalidaCache: false }),

  renovarTratamientos: () =>
    request<Actividad[]>('POST', `${URL}/tratamientos/renovar`, undefined, { invalidaCache: false }),

  programarEnriquecimiento: (datos: {
    id_animal: number
    tipo_enriquecimiento: TipoEnriquecimiento
    fecha_programada: string
    hora_programada: string
    descripcion_estimulo: string
    duracion_horas?: number
    duracion_minutos?: number
    observaciones?: string
  }, permitirCruce?: boolean) => request<Actividad>('POST', `${URL}/enriquecimientos${cruce(permitirCruce)}`, datos),

  programarEntrenamiento: (datos: {
    id_animal: number
    fecha_programada: string
    hora_programada: string
    duracion_horas: number
    duracion_minutos: number
    objetivo_entrenamiento: string
    tipo_refuerzo: string
    observaciones?: string
  }, permitirCruce?: boolean) => request<Actividad>('POST', `${URL}/entrenamientos${cruce(permitirCruce)}`, datos),

  programarLimpieza: (datos: {
    id_recinto: number
    fecha_programada: string
    hora_programada?: string
    duracion_horas: number
    duracion_minutos: number
    observaciones?: string
  }, permitirCruce?: boolean) => request<Actividad>('POST', `${URL}/limpiezas${cruce(permitirCruce)}`, datos),

  crearDieta: (datos: DietaCreate) =>
    request<Dieta>('POST', `${URL}/dietas`, datos),

  // Historial de dietas de todos los animales en una sola petición
  listarDietas: () => request<Dieta[]>('GET', `${URL}/dietas`),

  dietasPorAnimal: (idAnimal: number) =>
    request<Dieta[]>('GET', `${URL}/animales/${idAnimal}/dietas`),

  dietaVigente: (idAnimal: number) =>
    request<Dieta>('GET', `${URL}/animales/${idAnimal}/dietas/vigente`),
}

// Renovación del horizonte de tomas y dosis (agrega los días que faltan a los próximos 30/7).
// Basta con hacerla una vez por sesión: los horizontes son de varios días. Si falla, se vuelve
// a intentar la próxima vez que se abra Planificación. Se reinicia al cerrar sesión.
let renovacion: Promise<PromiseSettledResult<Actividad[]>[]> | null = null
alLimpiar(() => (renovacion = null))

export function renovarHorizonteDeSesion() {
  renovacion ??= Promise.allSettled([
    actividadesApi.renovarTomas(),
    actividadesApi.renovarTratamientos(),
  ]).then((resultados) => {
    if (resultados.some((r) => r.status === 'rejected')) renovacion = null
    return resultados
  })
  return renovacion
}

export const planificacionReferenciasApi = {
  animales: (): Promise<Animal[]> => animalesApi.listar(),
  recintos: (): Promise<Recinto[]> => recintosApi.listar(),
  usuariosAuditoria: (): Promise<UsuarioActividad[]> => usuariosApi.listar(),
}
