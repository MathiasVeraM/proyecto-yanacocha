// Lecturas de la API que pasan por la caché en memoria (ver cache.ts).
// Aquí se decide, en un solo lugar, la clave de cada consulta y cuánto se puede reutilizar:
//
// - Catálogos que casi no cambian (recintos, especies): una vez por sesión.
//   Si alguien los edita, la petición de edición invalida la caché y se vuelven a pedir.
// - Datos que cambian seguido (animales, actividades, registros veterinarios, dietas):
//   por defecto se revalidan siempre. La pantalla decide si muestra lo guardado mientras
//   tanto (pasando `alActualizar`) o si espera la respuesta nueva.
import { consultar, TODA_LA_SESION, type OpcionesConsulta } from './cache'
import { animalesApi, recintosApi, taxonomiaApi } from './animales'
import { actividadesApi, planificacionReferenciasApi } from './actividades'
import { ApiError } from './http'
import { veterinariaApi } from './veterinaria'
import type { Animal, FiltrosAnimales, Recinto, Taxonomia } from '@/types/animales'
import type {
  Actividad,
  Dieta,
  FiltrosActividades,
  LimitesActividades,
  Observacion,
  ReferenciasPlanificacion,
} from '@/types/actividades'
import type { Diagnostico, SignosVitalesHistorial, Tratamiento } from '@/types/veterinaria'

// El primer tramo es el servicio: http.ts invalida por servicio cuando algo se modifica
const clave = (servicio: 'animales' | 'actividades' | 'auth', ...partes: (string | number)[]) =>
  [servicio, ...partes].join('|')

// Los filtros se ordenan y se quitan los vacíos para que {} y {buscar: undefined} sean la misma clave
function claveFiltros(filtros: object) {
  const limpios = Object.entries(filtros)
    .filter(([, v]) => v !== undefined && v !== '' && v !== null)
    .sort(([a], [b]) => a.localeCompare(b))
  return JSON.stringify(limpios)
}

const porSesion = <T>(op?: OpcionesConsulta<T>): OpcionesConsulta<T> => ({ maxEdad: TODA_LA_SESION, ...op })

export const consultas = {
  // ---- Catálogos: una vez por sesión ----
  recintos: (op?: OpcionesConsulta<Recinto[]>) =>
    consultar(clave('animales', 'recintos'), () => recintosApi.listar(), porSesion(op)),

  especies: (op?: OpcionesConsulta<Taxonomia[]>) =>
    consultar(clave('animales', 'taxonomia'), () => taxonomiaApi.listar(), porSesion(op)),

  // Ejemplares, recintos y usuarios de Planificación en una sola petición. Va con el servicio
  // "animales" (como la lista de ejemplares que reemplaza): si se registra o edita un ejemplar o
  // un recinto, se vuelve a pedir. Planificación la revalida en cada visita mostrando lo guardado.
  referenciasPlanificacion: (op?: OpcionesConsulta<ReferenciasPlanificacion>) =>
    consultar(clave('animales', 'referencias-planificacion'), () => planificacionReferenciasApi.todas(), op),

  // Límites de fechas y duración: cambian solo con el día, se revisan cada 5 minutos
  limitesActividades: (op?: OpcionesConsulta<LimitesActividades>) =>
    consultar(clave('actividades', 'limites'), () => actividadesApi.limites(), { maxEdad: 5 * 60 * 1000, ...op }),

  // ---- Gestión animal ----
  animales: (filtros: FiltrosAnimales = {}, op?: OpcionesConsulta<Animal[]>) =>
    consultar(clave('animales', 'lista', claveFiltros(filtros)), () => animalesApi.listar(filtros), op),

  animal: (id: number, op?: OpcionesConsulta<Animal>) =>
    consultar(clave('animales', 'ficha', id), () => animalesApi.obtener(id), op),

  animalesConTratamientoEnCurso: (op?: OpcionesConsulta<number>) =>
    consultar(
      clave('animales', 'metrica-tratamientos'),
      () => veterinariaApi.contarAnimalesConTratamientoEnCurso(),
      op,
    ),

  diagnosticos: (idAnimal: number, op?: OpcionesConsulta<Diagnostico[]>) =>
    consultar(clave('animales', 'diagnosticos', idAnimal), () => veterinariaApi.listarDiagnosticos(idAnimal), op),

  // Todos los tratamientos del animal en una sola petición (antes, una por diagnóstico)
  tratamientosDelAnimal: (idAnimal: number, op?: OpcionesConsulta<Tratamiento[]>) =>
    consultar(
      clave('animales', 'tratamientos-animal', idAnimal),
      () => veterinariaApi.listarTratamientosDelAnimal(idAnimal),
      op,
    ),

  signosVitales: (idAnimal: number, op?: OpcionesConsulta<SignosVitalesHistorial[]>) =>
    consultar(clave('animales', 'signos', idAnimal), () => veterinariaApi.listarSignosVitales(idAnimal), op),

  // ---- Actividades y dietas ----
  actividades: (filtros: FiltrosActividades, op?: OpcionesConsulta<Actividad[]>) =>
    consultar(clave('actividades', 'lista', claveFiltros(filtros)), () => actividadesApi.listar(filtros), op),

  observacionesEnRango: (desde: string, hasta: string, op?: OpcionesConsulta<Observacion[]>) =>
    consultar(
      clave('actividades', 'observaciones', desde, hasta),
      () => actividadesApi.observacionesEnRango(desde, hasta),
      op,
    ),

  // Historial de dietas de todos los animales en una sola petición (Planificación)
  todasLasDietas: (op?: OpcionesConsulta<Dieta[]>) =>
    consultar(clave('actividades', 'dietas-todas'), () => actividadesApi.listarDietas(), op),

  dietasPorAnimal: (idAnimal: number, op?: OpcionesConsulta<Dieta[]>) =>
    consultar(clave('actividades', 'dietas', idAnimal), () => actividadesApi.dietasPorAnimal(idAnimal), op),

  // Sin dieta vigente el servicio responde 404: se guarda como null (no es un error)
  dietaVigente: (idAnimal: number, op?: OpcionesConsulta<Dieta | null>) =>
    consultar(
      clave('actividades', 'dieta-vigente', idAnimal),
      () =>
        actividadesApi.dietaVigente(idAnimal).catch((e) => {
          if (e instanceof ApiError && e.status === 404) return null
          throw e
        }),
      op,
    ),
}

// Claves que algunas pantallas actualizan directamente después de modificar algo
export const clavesCache = {
  actividades: (filtros: FiltrosActividades) => clave('actividades', 'lista', claveFiltros(filtros)),
  observacionesEnRango: (desde: string, hasta: string) => clave('actividades', 'observaciones', desde, hasta),
  animal: (id: number) => clave('animales', 'ficha', id),
}
