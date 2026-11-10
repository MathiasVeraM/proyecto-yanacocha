import { request } from './http'
import type {
  Actividad,
  Dieta,
  DietaCreate,
  EventoCalendario,
  FiltrosActividades,
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

export const actividadesApi = {
  listar: (filtros: FiltrosActividades = {}) =>
    request<Actividad[]>('GET', `${URL}${query({ ...filtros })}`),

  calendario: (fechaDesde: string, fechaHasta: string) =>
    request<EventoCalendario[]>(
      'GET',
      `${URL}/calendario${query({ fecha_desde: fechaDesde, fecha_hasta: fechaHasta })}`,
    ),

  completar: (id: number, observaciones?: string) =>
    request<Actividad>('POST', `${URL}/${id}/completar`, { observaciones }),

  generarTomas: (idDieta: number, fechaHasta?: string) =>
    request<{ tomas: Actividad[] }>('POST', `${URL}/tomas/generar`, {
      id_dieta: idDieta,
      fecha_hasta: fechaHasta,
    }),

  renovarTomas: () => request<Actividad[]>('POST', `${URL}/tomas/renovar`),

  programarEnriquecimiento: (datos: {
    id_animal: number
    tipo_enriquecimiento: TipoEnriquecimiento
    fecha_programada: string
    hora_programada: string
    descripcion_estimulo: string
    observaciones?: string
  }) => request<Actividad>('POST', `${URL}/enriquecimientos`, datos),

  programarEntrenamiento: (datos: {
    id_animal: number
    fecha_programada: string
    hora_programada: string
    duracion_horas: number
    duracion_minutos: number
    objetivo_entrenamiento: string
    tipo_refuerzo: string
    observaciones?: string
  }) => request<Actividad>('POST', `${URL}/entrenamientos`, datos),

  programarLimpieza: (datos: {
    id_recinto: number
    fecha_programada: string
    hora_programada?: string
    duracion_horas: number
    duracion_minutos: number
    observaciones?: string
  }) => request<Actividad>('POST', `${URL}/limpiezas`, datos),

  crearDieta: (datos: DietaCreate) =>
    request<Dieta>('POST', `${URL}/dietas`, datos),

  dietasPorAnimal: (idAnimal: number) =>
    request<Dieta[]>('GET', `${URL}/animales/${idAnimal}/dietas`),

  dietaVigente: (idAnimal: number) =>
    request<Dieta>('GET', `${URL}/animales/${idAnimal}/dietas/vigente`),
}

export const planificacionReferenciasApi = {
  animales: (): Promise<Animal[]> => animalesApi.listar(),
  recintos: (): Promise<Recinto[]> => recintosApi.listar(),
  usuariosAuditoria: (): Promise<UsuarioActividad[]> => usuariosApi.listar(),
}
