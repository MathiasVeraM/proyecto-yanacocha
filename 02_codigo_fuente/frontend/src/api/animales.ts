import { request } from './http'
import type {
  Animal,
  AnimalCreate,
  AnimalUpdate,
  FiltrosAnimales,
  Recinto,
  RecintoCreate,
  SugerenciaTaxonomia,
  Taxonomia,
  TaxonomiaCreate,
} from '@/types/animales'

const URL = '/api/animales'

// Arma el query string solo con los filtros que tienen valor
function query(params: Record<string, string | number | undefined>) {
  const valores = Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
  return valores.length ? `?${new URLSearchParams(valores.map(([k, v]) => [k, String(v)]))}` : ''
}

export const animalesApi = {
  listar: (filtros: FiltrosAnimales = {}) => request<Animal[]>('GET', `${URL}${query({ ...filtros })}`),

  obtener: (id: number) => request<Animal>('GET', `${URL}/${id}`),

  crear: (datos: AnimalCreate) => request<Animal>('POST', URL, datos),

  actualizar: (id: number, datos: AnimalUpdate) => request<Animal>('PUT', `${URL}/${id}`, datos),
}

export const taxonomiaApi = {
  listar: (buscar?: string) => request<Taxonomia[]>('GET', `${URL}/taxonomia${query({ buscar })}`),

  // Autocompletado: catálogo propio + iNaturalist
  sugerencias: (buscar: string) =>
    request<SugerenciaTaxonomia[]>('GET', `${URL}/taxonomia/sugerencias${query({ buscar })}`),

  importar: (idInaturalist: number) =>
    request<Taxonomia>('POST', `${URL}/taxonomia/importar`, { id_inaturalist: idInaturalist }),

  crear: (datos: TaxonomiaCreate) => request<Taxonomia>('POST', `${URL}/taxonomia`, datos),
}

export const recintosApi = {
  listar: () => request<Recinto[]>('GET', `${URL}/recintos`),

  crear: (datos: RecintoCreate) => request<Recinto>('POST', `${URL}/recintos`, datos),
}
